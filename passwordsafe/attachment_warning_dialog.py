# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing

from gi.repository import Gdk, Gio, GLib, Gtk

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
        try:
            cache_dir = os.path.join(
                GLib.get_user_cache_dir(), "passwordsafe", "tmp"
            )
            file_path = os.path.join(cache_dir, filename)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            gfile = Gio.File.new_for_path(file_path)
            output_stream = gfile.replace(
                None, False,
                Gio.FileCreateFlags.PRIVATE
                | Gio.FileCreateFlags.REPLACE_DESTINATION, None
            )
            output_stream.write_bytes(GLib.Bytes.new(bytes_buffer))
            output_stream.close()
            Gtk.show_uri_on_window(None, gfile.get_uri(), Gdk.CURRENT_TIME)
        except GLib.Error as err:
            logging.debug("Could not load attachment %s: %s", filename, err)
