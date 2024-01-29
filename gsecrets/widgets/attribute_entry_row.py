# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from gi.repository import Adw, Gtk

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attribute_entry_row.ui")
class AttributeEntryRow(Adw.EntryRow):
    __gtype_name__ = "AttributeEntryRow"

    def __init__(self, entry: SafeEntry, key: str, value: str) -> None:
        super().__init__()

        self.entry = entry
        self.key = key

        self.props.title = key
        if value:
            self.props.text = value

    @Gtk.Template.Callback()
    def _on_remove_button_clicked(self, _button):
        window = self.get_root()
        self.entry.delete_attribute(self.key)
        window.unlocked_db.attribute_deleted(
            self.entry, self.key, self.props.text, False
        )

    @Gtk.Template.Callback()
    def _on_copy_button_clicked(self, _row):
        clipboard = self.get_clipboard()
        clipboard.set(self.props.text)
        window = self.get_root()
        window.send_notification(_("Attribute copied"))

    @Gtk.Template.Callback()
    def _on_changed(self, row):
        self.entry.set_attribute(self.key, row.get_text())
