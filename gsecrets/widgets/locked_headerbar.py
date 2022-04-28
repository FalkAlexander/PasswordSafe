# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gio, Gtk

from gsecrets import const
from gsecrets.recent_files_menu import RecentFilesMenu


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/locked_headerbar.ui")
class LockedHeaderBar(Adw.Bin):

    __gtype_name__ = "LockedHeaderBar"

    title = Gtk.Template.Child()
    split_button = Gtk.Template.Child()

    settings = Gio.Settings.new(const.APP_ID)

    def __init__(self):
        super().__init__()

        self.set_menu()
        self.settings.connect(
            "changed::last-opened-list", self.on_settings_changed
        )

    def set_menu(self):
        menu = RecentFilesMenu()
        if menu.is_empty:
            self.split_button.set_menu_model(None)
        else:
            self.split_button.set_menu_model(menu.menu)

    def on_settings_changed(self, _settings, _key):
        self.set_menu()
