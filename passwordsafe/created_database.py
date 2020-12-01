# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk
from passwordsafe.unlock_database import UnlockDatabase


@Gtk.Template(
    resource_path="/org/gnome/PasswordSafe/created_database.ui")
class CreatedDatabase(Gtk.Box):
    """Page to show when a safe has been successfully created."""

    __gtype_name__ = "CreatedDatabase"

    def __init__(self, window, widget, dbm):
        super().__init__()
        self.window = window
        self.parent_widget = widget
        self.database_manager = dbm
        self.parent_widget.add(self)

    @Gtk.Template.Callback()
    def on_finish_button_clicked(self, _widget):
        self.destroy()
        UnlockDatabase(
            self.window, self.parent_widget,
            self.database_manager.database_path)
