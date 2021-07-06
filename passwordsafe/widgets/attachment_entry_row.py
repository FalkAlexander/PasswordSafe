# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.safe_element import SafeEntry
    from pykeepass.attachment import Attachment


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/attachment_entry_row.ui")
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
        save_dialog = Gtk.FileChooserNative.new(
            # NOTE: Filechooser title for downloading an attachment
            _("Save attachment"),
            window,
            Gtk.FileChooserAction.SAVE,
            _("_Save"),
            None,
        )
        save_dialog.set_current_name(self.attachment.filename)
        save_dialog.set_modal(True)

        save_dialog.connect("response", self._on_save_filechooser_response, save_dialog)
        save_dialog.show()

    @Gtk.Template.Callback()
    def _on_delete_button_clicked(self, _button):
        self.entry.delete_attachment(self.attachment)
        listbox = self.get_parent()
        listbox.remove(self)

    def _on_save_filechooser_response(
        self,
        dialog: Gtk.Dialog,
        response: Gtk.ResponseType,
        _dialog: Gtk.Dialog,
    ) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            bytes_buffer = self.entry.get_attachment_content(self.attachment)
            stream = Gio.File.replace(
                dialog.get_file(),
                None,
                False,
                Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION,
                None,
            )
            Gio.OutputStream.write_bytes(stream, GLib.Bytes.new(bytes_buffer), None)
            stream.close()
