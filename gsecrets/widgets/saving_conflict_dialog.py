# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk


class SavingConflictDialog(Adw.MessageDialog):

    __gtype_name__ = "SavingConflictDialog"

    def __init__(self, window, db_manager, save_callback):
        super().__init__(transient_for=window)

        self.save_callback = save_callback
        self.db_manager = db_manager
        self.window = window

        # TRANSLATORS Warning dialog to resolve file saving conflicts.
        self.props.heading = _("Conflicts While Saving")
        self.props.body = _(
            # TRANSLATORS Warning Dialog to resolve saving conflicts. \n is a new line.
            "The safe was modified from somewhere else. Saving will overwrite the safe with our current version.\n\n You can also make a backup of their version of the safe."  # pylint: disable=line-too-long # noqa: E501
        )

        gfile = Gio.File.new_for_path(db_manager.path)
        file_name = os.path.splitext(gfile.get_basename())[0]

        self.add_response("cancel", _("_Cancel"))
        # TRANSLATORS backup and save current safe.
        self.add_response("backup", _("_Back up and Save"))
        self.add_response("save", _("_Save"))
        self.set_response_appearance(
            "save", Adw.ResponseAppearance.DESTRUCTIVE
        )

        self.connect("response::save", self._on_response_save)
        self.connect("response::backup", self._on_response_backup, file_name)

    def _on_response_save(self, _dialog, _response):
        self.db_manager.save_async(self.save_callback)

    def _on_response_backup(self, _message_dialog, _response, file_name):
        dialog = Gtk.FileChooserNative.new(
            _("Save Backup"),
            self.window,
            Gtk.FileChooserAction.SAVE,
            _("_Save"),
            None,
        )
        dialog.set_modal(True)
        dialog.set_current_name(f"{file_name}-backup.kdbx")
        dialog.connect("response", self._on_filechooser_response, dialog)
        dialog.show()

    def _on_copy_backup(self, gfile, result):
        try:
            gfile.copy_finish(result)
        except GLib.Error as err:
            logging.debug("Could not backup safe: %s", err.message)
            self.window.send_notification(_("Could not backup safe"))
        else:
            self.db_manager.save_async(self.save_callback)

    def _on_filechooser_response(self, _dialog, response, dialog):
        dest = dialog.get_file()
        dialog.destroy()
        if dest is None:
            return

        if response == Gtk.ResponseType.ACCEPT:
            gfile = Gio.File.new_for_path(self.db_manager.path)
            gfile.copy_async(
                dest,
                Gio.FileCopyFlags.OVERWRITE,
                GLib.PRIORITY_DEFAULT,
                None,
                None,
                None,
                self._on_copy_backup,
            )
