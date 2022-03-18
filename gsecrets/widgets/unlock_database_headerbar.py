# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, GObject, Gtk

import gsecrets.config_manager


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlock_database_headerbar.ui")
class UnlockDatabaseHeaderbar(Adw.Bin):

    __gtype_name__ = "UnlockDatabaseHeaderbar"

    title = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    window = GObject.Property(type=Adw.ApplicationWindow)

    @Gtk.Template.Callback()
    def _on_back_button_clicked(self, _widget: Gtk.Button) -> None:
        # TODO Use the go_back action instead.
        database = self.props.window.unlocked_db
        if database:
            if gsecrets.config_manager.get_save_automatically():
                database.auto_save_database()

            database.cleanup()

        self.props.window.view = self.props.window.View.RECENT_FILES
