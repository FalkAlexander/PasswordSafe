import gi
import sys
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
from keepassgtk.main_window import MainWindow


class Application(Gtk.Application):
    window = NotImplemented

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, application_id="run.terminal.KeepassGtk", **kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        GLib.set_prgname("KeepassGtk")

        self.assemble_application_menu()

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(
                application=self, title="KeepassGtk",
                icon_name="dialog-password")
            self.add_menubutton_popover_actions()
            self.window.application = self

        self.window.present()

    def assemble_application_menu(self):
        app_menu = Gio.Menu()

        app_menu.append("Settings", "app.settings")
        # TODO: Seperator
        app_menu.append("About", "app.about")
        app_menu.append("Quit", "app.quit")

        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_menu_clicked)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_menu_clicked)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_menu_clicked)

        self.add_action(settings_action)
        self.add_action(about_action)
        self.add_action(quit_action)
        self.set_app_menu(app_menu)

    def on_settings_menu_clicked(self, action, param):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/settings_dialog.ui")
        settings_dialog = builder.get_object("settings_dialog")
        settings_dialog.set_modal(True)
        settings_dialog.set_transient_for(self.window)
        settings_dialog.present()

    def on_about_menu_clicked(self, action, param):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/about_dialog.ui")
        about_dialog = builder.get_object("about_dialog")
        about_dialog.set_modal(True)
        about_dialog.set_transient_for(self.window)
        about_dialog.present()

    def on_quit_menu_clicked(self, action, param):
        self.quit()

    def add_menubutton_popover_actions(self):
        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.window.create_filechooser)
        self.add_action(new_action)

        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self.window.open_filechooser)
        self.add_action(open_action)


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
