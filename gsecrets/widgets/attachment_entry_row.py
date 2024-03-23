# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment

    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attachment_entry_row.ui")
class AttachmentEntryRow(Adw.ActionRow):
    __gtype_name__ = "AttachmentEntryRow"

    download_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, entry: SafeEntry, attachment: Attachment) -> None:
        super().__init__()

        self.entry = entry
        self.attachment = attachment

        self.set_title(attachment.filename)
        # TODO Display mime type in subtitle

    @Gtk.Template.Callback()
    def _on_download_button_clicked(self, _button):
        window = self.get_root()
        dialog = Gtk.FileDialog.new()
        # NOTE: Filechooser title for downloading an attachment
        dialog.props.title = _("Save Attachment")
        dialog.props.initial_name = self.attachment.filename

        dialog.save(window, None, self._on_save_filechooser_response)

    @Gtk.Template.Callback()
    def _on_delete_button_clicked(self, _button):
        self.entry.delete_attachment(self.attachment)
        listbox = self.get_parent()
        listbox.remove(self)

    def _replace_contents_callback(self, gfile, result):
        try:
            gfile.replace_contents_finish(result)
        except GLib.Error:
            logging.exception("Could not store attachment")
            window = self.get_root()
            window.send_notification(_("Could not store attachment"))

    def _on_save_filechooser_response(self, dialog, result):
        try:
            gfile = dialog.save_finish(result)
        except GLib.Error as err:
            if not err.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                logging.exception("Could not save file")
        else:
            bytes_buffer = self.entry.get_attachment_content(self.attachment)
            gbytes = GLib.Bytes.new(bytes_buffer)

            gfile.replace_contents_bytes_async(
                gbytes,
                None,
                False,
                Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
                self._replace_contents_callback,
            )
