# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Gtk


class SaveDialog:
    def __init__(self, window):
        self.window = window

        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/save_dialog.ui"
        )
        self._dialog = builder.get_object("dialog")
        self._dialog.set_transient_for(window)
        self._dialog.connect("response", self._on_dialog_response)

    def show(self):
        self._dialog.show()

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
