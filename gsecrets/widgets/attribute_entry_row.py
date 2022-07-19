# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gi.repository import Adw, Gtk

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attribute_entry_row.ui")
class AttributeEntryRow(Adw.EntryRow):

    __gtype_name__ = "AttributeEntryRow"

    def __init__(
            self, entry: SafeEntry, key: str, value: str, list_box: Gtk.ListBox
    ) -> None:
        super().__init__()

        self.entry = entry
        self.key = key
        self.list_box = list_box

        self.props.title = key
        if value:
            self.props.text = value

    @Gtk.Template.Callback()
    def _on_remove_button_clicked(self, _button):
        self.entry.delete_attribute(self.key)
        self.list_box.remove(self)

    @Gtk.Template.Callback()
    def _on_changed(self, row):
        self.entry.set_attribute(self.key, row.get_text())
