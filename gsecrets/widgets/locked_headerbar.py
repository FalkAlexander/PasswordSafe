# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, Gio, Gtk

import gsecrets.config_manager as config
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
        if config.get_last_opened_list():
            menu = RecentFilesMenu().menu
            self.split_button.set_menu_model(menu)
        else:
            self.split_button.set_menu_model(None)

    def on_settings_changed(self, _settings, _key):
        self.set_menu()
