# Single Screen

Windows' `Win+P` for Linux Mint (Cinnamon): switch in one keystroke between your
multi-monitor layout and a single display, then back.

| Shortcut / action | Effect |
|---|---|
| `Super+P` or click on the panel icon | Opens the menu |
| **Extend (all displays)** | Restores the saved multi-monitor layout |
| **&lt;Monitor&gt; only** | Turns every other monitor off |

The menu lists the monitors connected at the time it opens, and a dot marks the current mode.
It is keyboard-navigable (arrows + `Enter`, `Esc` to close).

## Installation

```bash
./install.sh      # symlinks the applet into ~/.local/share/cinnamon/applets
./uninstall.sh    # --purge also deletes the saved layout and the applet settings
```

Then add the applet to a panel: *System Settings → Applets → Single Screen*.
The shortcut can be changed in the applet settings.

Requirements: Cinnamon (Muffin) with Python 3 and PyGObject, both shipped with Linux Mint.

## Behavior

- Switching to a single display first saves the current multi-monitor layout
  (positions, modes, scaling, primary monitor) to `~/.config/single-screen/saved.json`.
  Switching from one single display to another keeps that saved layout.
- **Extend** reapplies the saved layout as long as it matches the connected monitors and
  their available modes; otherwise it falls back to all monitors side by side
  (external monitors first, preferred mode, current scaling).
- Changes are applied in *temporary* mode: `cinnamon-monitors.xml` is not modified
  and Cinnamon shows no "Keep this configuration?" dialog.

## Architecture

```
single-screen@romu/applet.js              panel applet: icon, menu, global shortcut
single-screen@romu/screens.py             CLI talking to Muffin's D-Bus API (org.cinnamon.Muffin.DisplayConfig)
single-screen@romu/settings-schema.json   applet settings (shortcut)
```

`screens.py` can also be used on its own:

```bash
python3 single-screen@romu/screens.py status          # JSON: monitors, active ones, saved layout available
python3 single-screen@romu/screens.py single HDMI-0   # keep only HDMI-0
python3 single-screen@romu/screens.py restore         # back to the saved layout
```
