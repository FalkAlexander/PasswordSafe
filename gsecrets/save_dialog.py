# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import GLib, Gtk


class SaveDialog:
    def __init__(self, window):
        self.window = window

        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/World/Secrets/gtk/save_dialog.ui"
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
                database.database_manager.save_async(self._on_save)

        elif response == Gtk.ResponseType.NO:  # Discard
            self.window.save_window_size()
            self.window.destroy()

    def _on_save(self, database_manager, result):
        try:
            is_saved = database_manager.save_finish(result)
        except GLib.Error as err:
            self.window.send_notification(_("Could not save Safe"))
            logging.error("Could not save Safe %s", err)
        else:
            if is_saved:
                self.window.save_window_size()
                self.window.destroy()
