# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, Gtk

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


class ProtectedAttributeEntryRow:
    def __init__(
        self, entry: SafeEntry, key: str, value: str, listbox: Gtk.ListBox
    ) -> None:
        super().__init__()

        self._entry = entry
        self._key = key
        self._list_box = listbox

        self.row = Adw.PasswordEntryRow.new()

        self.row.props.title = key
        if value:
            self.row.props.text = value

        copy_btn = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
        copy_btn.props.valign = Gtk.Align.CENTER
        copy_btn.props.tooltip_text = _("Copy Attribute")
        copy_btn.add_css_class("flat")
        copy_btn.connect("clicked", self._on_copy_button_clicked)

        button = Gtk.Button.new_from_icon_name("user-trash-symbolic")
        button.props.valign = Gtk.Align.CENTER
        button.props.tooltip_text = _("Remove Attribute")
        button.add_css_class("flat")
        button.connect("clicked", self._on_remove_button_clicked)

        self.row.connect("changed", self._on_changed)
        self.row.add_suffix(copy_btn)
        self.row.add_suffix(button)

    def _on_remove_button_clicked(self, _button):
        self._entry.delete_attribute(self._key)
        self._list_box.remove(self.row)

    def _on_changed(self, row):
        self._entry.set_attribute(self._key, row.props.text, True)

    def _on_copy_button_clicked(self, _row):
        clipboard = self.row.get_clipboard()
        clipboard.set(self.row.props.text)

        window = self.row.get_root()
        window.send_notification(_("Attribute copied"))
