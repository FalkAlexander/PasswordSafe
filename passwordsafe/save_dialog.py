# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/save_dialog.ui")
class SaveDialog(Gtk.MessageDialog):

    __gtype_name__ = "SaveDialog"

    def __init__(self, window):
        super().__init__()

        self.window = window
        self.set_transient_for(window)

    @Gtk.Template.Callback()
    def _on_dialog_response(
        self, dialog: Gtk.Dialog, response: Gtk.ResponseType
    ) -> None:
        database = self.window.unlocked_db
        dialog.close()

        if response == Gtk.ResponseType.YES:  # Save
            if database:
                database.database_manager.save_database()

            self.window.save_window_size()
            self.window.destroy()

        elif response == Gtk.ResponseType.NO:  # Discard
            self.window.save_window_size()
            self.window.destroy()
