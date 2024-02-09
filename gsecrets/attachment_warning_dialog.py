# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

from gsecrets import const

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment

    from gsecrets.entry_page import EntryPage  # pylint: disable=ungrouped-imports


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attachment_warning_dialog.ui")
class AttachmentWarningDialog(Adw.AlertDialog):
    __gtype_name__ = "AttachmentWarningDialog"

    def __init__(self, entry_page: EntryPage, attachment: Attachment) -> None:
        """Dialog to confirm opening an attachment

        :param entry_page: entry page
        """
        super().__init__()

        self.__unlocked_database = entry_page.unlocked_database
        self.__attachment = attachment

    @Gtk.Template.Callback()
    def _on_proceed(self, _dialog, _response):
        attachment = self.__attachment
        u_db = self.__unlocked_database
        self.__open_tmp_file(
            u_db.database_manager.db.binaries[attachment.id],
            attachment.filename,
        )

    def __open_tmp_file(self, bytes_buffer, filename):
        cache_dir = os.path.join(GLib.get_user_cache_dir(), const.SHORT_NAME, "tmp")
        file_path = os.path.join(cache_dir, filename)
        window = self.__unlocked_database.window
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        gfile = Gio.File.new_for_path(file_path)

        contents = GLib.Bytes.new(bytes_buffer)
        gfile.replace_contents_bytes_async(
            contents,
            None,
            False,
            Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
            None,
            _callback,
            window,
        )


def _callback(gfile, result, window):
    try:
        gfile.replace_contents_finish(result)
    except GLib.Error as err:
        logging.debug("Could not load attachment: %s", err.message)
        window.send_notification(_("Could not load attachment"))
    else:
        launcher = Gtk.FileLauncher.new(gfile)
        launcher.launch(window, None, _on_launch, window)


def _on_launch(launcher, result, window):
    try:
        launcher.launch_finish(result)
    except GLib.Error as err:
        logging.debug("Could not launch attachment file: %s", err.message)
        window.send_notification(_("Could not load attachment"))
