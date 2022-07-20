# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/save_dialog.ui")
class SaveDialog(Adw.MessageDialog):

    __gtype_name__ = "SaveDialog"

    def __init__(self, window):
        super().__init__(transient_for=window)

        self.window = window

    @Gtk.Template.Callback()
    def _on_discard(self, _dialog, _response):
        self.window.force_close()

    @Gtk.Template.Callback()
    def _on_save(self, _dialog, _response):
        if (database := self.window.unlocked_db):
            database.database_manager.save_async(self._save_finished)

    def _save_finished(self, database_manager, result):
        try:
            is_saved = database_manager.save_finish(result)
        except GLib.Error as err:
            self.window.send_notification(_("Could not save Safe"))
            logging.error("Could not save Safe %s", err.message)
        else:
            if is_saved:
                self.window.close()
            else:
                # This shouldn't happen
                self.window.send_notification(_("Could not save Safe"))
