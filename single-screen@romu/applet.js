const Gtk = imports.gi.Gtk;
const GLib = imports.gi.GLib;
const Gettext = imports.gettext;
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Settings = imports.ui.settings;
const Main = imports.ui.main;
const Util = imports.misc.util;

const UUID = "single-screen@romu";
const HOTKEY_ID = "single-screen-menu";

Gettext.bindtextdomain(UUID, GLib.get_home_dir() + "/.local/share/locale");

function _(str) {
    return Gettext.dgettext(UUID, str);
}

class SingleScreenApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.script = metadata.path + "/screens.py";

        this.set_applet_icon_symbolic_name("video-display");
        this.set_applet_tooltip(_("Display configuration"));

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);

        this.settings = new Settings.AppletSettings(this, metadata.uuid, instanceId);
        this.settings.bind("keybinding", "keybinding", () => this._bindHotkey());
        this._bindHotkey();
    }

    _bindHotkey() {
        Main.keybindingManager.addHotKey(HOTKEY_ID, this.keybinding, () => this._openMenu());
    }

    _run(args, callback) {
        Util.spawnCommandLineAsyncIO(null, (stdout, stderr, exitCode) => {
            if (exitCode !== 0)
                Main.notify(_("Single Screen"), stderr || _("Command failed: ") + args.join(" "));
            else if (callback)
                callback(stdout);
        }, { argv: ["python3", this.script].concat(args) });
    }

    // The menu is rebuilt on every opening to reflect the currently connected monitors.
    _openMenu() {
        this._run(["status"], (stdout) => {
            this._buildMenu(JSON.parse(stdout));
            this.menu.open(true);
            this.menu.actor.navigate_focus(null, Gtk.DirectionType.TAB_FORWARD, false);
        });
    }

    _buildMenu(status) {
        this.menu.removeAll();
        const active = status.monitors.filter(m => m.active);

        const extend = new PopupMenu.PopupMenuItem(_("Extend (all displays)"));
        extend.setSensitive(status.monitors.length > 1);
        if (active.length > 1)
            extend.setOrnament(PopupMenu.OrnamentType.DOT, true);
        extend.connect("activate", () => this._run(["restore"]));
        this.menu.addMenuItem(extend);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        for (const monitor of status.monitors) {
            const item = new PopupMenu.PopupMenuItem(_("%s only").format(monitor.name));
            if (active.length === 1 && monitor.active)
                item.setOrnament(PopupMenu.OrnamentType.DOT, true);
            item.connect("activate", () => this._run(["single", monitor.connector]));
            this.menu.addMenuItem(item);
        }
    }

    on_applet_clicked() {
        if (this.menu.isOpen)
            this.menu.close();
        else
            this._openMenu();
    }

    on_applet_removed_from_panel() {
        Main.keybindingManager.removeHotKey(HOTKEY_ID);
        this.settings.finalize();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new SingleScreenApplet(metadata, orientation, panelHeight, instanceId);
}
