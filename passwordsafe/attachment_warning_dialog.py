# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import subprocess
import typing

from gi.repository import Gio, GLib, Gtk

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment
    from passwordsafe.entry_page import EntryPage


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/attachment_warning_dialog.ui")
class AttachmentWarningDialog(Gtk.MessageDialog):

    __gtype_name__ = "AttachmentWarningDialog"

    def __init__(self, entry_page: EntryPage, attachment: Attachment) -> None:
        """Dialog to confirm opening an attachment

        :param entry_page: entry page
        """
        super().__init__()
        self.__unlocked_database = entry_page.unlocked_database
        self.__attachment = attachment

        # Setup Widgets
        self.set_modal(True)
        self.set_transient_for(self.__unlocked_database.window)

    @Gtk.Template.Callback()
    def _on_warning_dialog_back_button_clicked(self, _button):
        self.close()

    @Gtk.Template.Callback()
    def _on_warning_dialog_proceed_button_clicked(self, _button):
        attachment = self.__attachment
        u_db = self.__unlocked_database
        self.close()
        self.__open_tmp_file(
            u_db.database_manager.db.binaries[attachment.id], attachment.filename
        )

    def __open_tmp_file(self, bytes_buffer, filename):
        (file, stream) = Gio.File.new_tmp(filename + ".XXXXXX")
        stream.get_output_stream().write_bytes(GLib.Bytes.new(bytes_buffer))
        stream.close()
        self.__unlocked_database.scheduled_tmpfiles_deletion.append(file)
        subprocess.run(["xdg-open", file.get_path()], check=True)
