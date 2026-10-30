#!/usr/bin/env python3
"""Switches between the current multi-monitor layout and a single display,
through Muffin's D-Bus API (the one used by Cinnamon's "Display" settings panel).

  screens.py status            -> JSON: connected monitors, active monitors, saved layout available
  screens.py single CONNECTOR  -> saves the current layout, then enables CONNECTOR only
  screens.py restore           -> reapplies the saved layout (or extends side by side)
"""
import json
import os
import sys

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

BUS_NAME = "org.cinnamon.Muffin.DisplayConfig"
OBJ_PATH = "/org/cinnamon/Muffin/DisplayConfig"
METHOD_TEMPORARY = 1  # not written to cinnamon-monitors.xml, no confirmation dialog
SAVE_FILE = os.path.join(GLib.get_user_config_dir(), "single-screen", "saved.json")


def proxy():
    return Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
        BUS_NAME, OBJ_PATH, BUS_NAME, None)


def get_state(p):
    serial, monitors, logical, props = p.call_sync(
        "GetCurrentState", None, Gio.DBusCallFlags.NONE, -1, None).unpack()
    return serial, monitors, logical, props


def current_mode_id(monitor):
    _, modes, _ = monitor
    for mode in modes:
        if mode[6].get("is-current"):
            return mode[0]
    return None


def preferred_mode(monitor):
    _, modes, _ = monitor
    for mode in modes:
        if mode[6].get("is-preferred"):
            return mode
    return modes[0]


def describe(monitors, logical):
    active = {spec[0] for lm in logical for spec in lm[5]}
    return [{
        "connector": m[0][0],
        "name": m[2].get("display-name", m[0][0]),
        "builtin": bool(m[2].get("is-builtin", False)),
        "active": m[0][0] in active,
    } for m in monitors]


def snapshot(monitors, logical):
    """Converts the current state to the format expected by ApplyMonitorsConfig."""
    modes = {m[0][0]: current_mode_id(m) for m in monitors}
    return [{
        "x": lm[0], "y": lm[1], "scale": lm[2], "transform": lm[3], "primary": lm[4],
        "monitors": [{"connector": spec[0], "mode": modes[spec[0]]} for spec in lm[5]],
    } for lm in logical]


def apply(p, serial, props, logical_monitors):
    lms = [(lm["x"], lm["y"], lm["scale"], lm["transform"], lm["primary"],
            [(m["connector"], m["mode"], {}) for m in lm["monitors"]])
           for lm in logical_monitors]
    out_props = {}
    if "layout-mode" in props:
        out_props["layout-mode"] = GLib.Variant("u", props["layout-mode"])
    p.call_sync("ApplyMonitorsConfig",
                GLib.Variant("(uua(iiduba(ssa{sv}))a{sv})",
                             (serial, METHOD_TEMPORARY, lms, out_props)),
                Gio.DBusCallFlags.NONE, -1, None)


def load_saved(monitors):
    """Returns the saved layout if it matches the currently connected monitors."""
    try:
        with open(SAVE_FILE) as f:
            saved = json.load(f)
    except (OSError, ValueError):
        return None
    connected = {m[0][0]: {mode[0] for mode in m[1]} for m in monitors}
    for lm in saved:
        for m in lm["monitors"]:
            if m["mode"] not in connected.get(m["connector"], ()):
                return None
    return saved


def logical_width(mode_width, scale, props):
    """Width in Muffin's coordinate space, which depends on the layout-mode."""
    layout = props.get("layout-mode", 1)
    if layout == 2:  # physical
        return mode_width
    if layout == 3:  # logical with a global UI factor (X11 fractional scaling)
        return round(mode_width * props.get("legacy-ui-scaling-factor", 1) / scale)
    return round(mode_width / scale)


def side_by_side(monitors, logical, props):
    """Fallback without a saved layout: all monitors side by side, preferred mode."""
    scales = {spec[0]: lm[2] for lm in logical for spec in lm[5]}
    result, x = [], 0
    for i, m in enumerate(sorted(monitors, key=lambda m: m[2].get("is-builtin", False))):
        mode = preferred_mode(m)
        scale = scales.get(m[0][0], 1.0)
        result.append({"x": x, "y": 0, "scale": scale, "transform": 0, "primary": i == 0,
                       "monitors": [{"connector": m[0][0], "mode": mode[0]}]})
        x += logical_width(mode[1], scale, props)
    return result


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    p = proxy()
    serial, monitors, logical, props = get_state(p)
    cmd = argv[1]

    if cmd == "status":
        print(json.dumps({
            "monitors": describe(monitors, logical),
            "saved": load_saved(monitors) is not None,
        }))
        return 0

    if cmd == "single":
        if len(argv) < 3:
            print("usage: screens.py single CONNECTOR", file=sys.stderr)
            return 2
        target = next((m for m in monitors if m[0][0] == argv[2]), None)
        if target is None:
            print(f"unknown monitor: {argv[2]}", file=sys.stderr)
            return 1
        # Only multi-monitor layouts are saved: switching from one single display
        # to another must not overwrite the layout to restore.
        if len(logical) > 1:
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
            with open(SAVE_FILE, "w") as f:
                json.dump(snapshot(monitors, logical), f, indent=2)
        scale = next((lm[2] for lm in logical for spec in lm[5] if spec[0] == argv[2]), 1.0)
        mode = current_mode_id(target) or preferred_mode(target)[0]
        apply(p, serial, props, [{"x": 0, "y": 0, "scale": scale, "transform": 0, "primary": True,
                                  "monitors": [{"connector": argv[2], "mode": mode}]}])
        return 0

    if cmd == "restore":
        apply(p, serial, props, load_saved(monitors) or side_by_side(monitors, logical, props))
        return 0

    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
