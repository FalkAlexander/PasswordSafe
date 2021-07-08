# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing

from gi.repository import Gdk, Gio, GLib, Gtk

from passwordsafe import const

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment

    from passwordsafe.entry_page import EntryPage


class AttachmentWarningDialog:
    def __init__(self, entry_page: EntryPage, attachment: Attachment) -> None:
        """Dialog to confirm opening an attachment

        :param entry_page: entry page
        """
        self.__unlocked_database = entry_page.unlocked_database
        self.__attachment = attachment

        # Setup Widgets
        builder = Gtk.Builder.new_from_resource(
            "/org/gnome/PasswordSafe/attachment_warning_dialog.ui"
        )
        self._dialog = builder.get_object("dialog")
        self._dialog.connect("response", self._on_warning_dialog_response)
        self._dialog.set_modal(True)
        self._dialog.set_transient_for(self.__unlocked_database.window)

    def show(self):
        self._dialog.show()

    def _on_warning_dialog_response(self, dialog, response):
        dialog.close()

        if response == Gtk.ResponseType.OK:
            attachment = self.__attachment
            u_db = self.__unlocked_database
            self.__open_tmp_file(
                u_db.database_manager.db.binaries[attachment.id], attachment.filename
            )

    def __open_tmp_file(self, bytes_buffer, filename):
        try:
            cache_dir = os.path.join(GLib.get_user_cache_dir(), const.SHORT_NAME, "tmp")
            file_path = os.path.join(cache_dir, filename)
            window = self.__unlocked_database.window
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            gfile = Gio.File.new_for_path(file_path)
            output_stream = gfile.replace(
                None,
                False,
                Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
            )
            output_stream.write_bytes(GLib.Bytes.new(bytes_buffer))
            output_stream.close()
            Gtk.show_uri(window, gfile.get_uri(), Gdk.CURRENT_TIME)
        except GLib.Error as err:
            logging.debug("Could not load attachment %s: %s", filename, err)
