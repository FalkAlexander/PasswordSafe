import gi
import sys

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('Handy', '0.0')

from gi.repository import GLib, Gio, Gtk
from gi.repository import Notify
from gettext import gettext as _
from passwordsafe.main_window import MainWindow
from passwordsafe.settings_dialog import SettingsDialog


class Application(Gtk.Application):
    window = NotImplemented
    file_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, application_id="org.gnome.PasswordSafe", flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        GLib.set_application_name('Password Safe')
        GLib.set_prgname("Password Safe")
        Notify.init("Password Safe")

        self.connect("open", self.file_open_handler)
        self.assemble_application_menu()

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(
                application=self, title="Password Safe",
                icon_name="dialog-password")

            self.window.application = self

            self.add_menubutton_popover_actions()
            self.window.add_row_popover_actions()
            self.window.add_database_menubutton_popover_actions()
            self.window.add_selection_actions()
            self.add_global_accelerators()

        self.window.present()

    def assemble_application_menu(self):
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_menu_clicked)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_menu_clicked)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_menu_clicked)

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self.on_shortcuts_menu_clicked)

        self.add_action(settings_action)
        self.add_action(about_action)
        self.add_action(quit_action)
        self.add_action(shortcuts_action)

    def on_settings_menu_clicked(self, action, param):
        SettingsDialog(self.window).on_settings_menu_clicked(action, param)

    def on_about_menu_clicked(self, action, param):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/about_dialog.ui")
        about_dialog = builder.get_object("about_dialog")
        about_dialog.set_modal(True)
        if self.window is not NotImplemented:
            about_dialog.set_transient_for(self.window)
        about_dialog.present()

    def on_quit_menu_clicked(self, action, param):
        self.quit()

    def on_shortcuts_menu_clicked(self, action, param):
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/shortcuts_overview.ui")
        shortcuts_overview = builder.get_object("shortcuts_overview")
        if self.window is not NotImplemented:
            shortcuts_overview.set_transient_for(self.window)
        shortcuts_overview.show()

    def add_menubutton_popover_actions(self):
        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.window.create_filechooser)
        self.add_action(new_action)

        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self.window.open_filechooser)
        self.add_action(open_action)

    def file_open_handler(self, app, g_file_list, amount, ukwn):
        for g_file in g_file_list:
            self.file_list.append(g_file)
            if self.window is not None:
                self.window.start_database_opening_routine(g_file.get_basename(), g_file.get_path())

        self.do_activate()

    def add_global_accelerators(self):
        self.window.add_global_accelerator_actions()
        self.set_accels_for_action("app.settings", ["<Control>p"])
        self.set_accels_for_action("app.open", ["<Control>o"])
        self.set_accels_for_action("app.new", ["<Control>n"])
        self.set_accels_for_action("app.db.save", ["<Control>s"])
        self.set_accels_for_action("app.db.lock", ["<Control>l"])
        self.set_accels_for_action("app.db.add_entry", ["<Control>e"])
        self.set_accels_for_action("app.db.add_group", ["<Control>g"])


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)

