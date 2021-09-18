# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Gtk

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/attribute_entry_row.ui")
class AttributeEntryRow(Gtk.Box):

    __gtype_name__ = "AttributeEntryRow"

    key_edit_button = Gtk.Template.Child()
    value_entry = Gtk.Template.Child()
    entry_box = Gtk.Template.Child()
    key_entry = Gtk.Template.Child()
    edit_stack = Gtk.Template.Child()

    def __init__(self, entry: SafeEntry, key: str, value: str) -> None:
        super().__init__()

        self.entry = entry
        self.key = key

        self.key_edit_button.set_label(key)
        self.key_entry.set_text(key)
        if value:
            self.value_entry.set_text(value)

        # We connect it latter so it does not trigger update() on the entry
        self.value_entry.connect("changed", self._on_value_entry_changed)

    @Gtk.Template.Callback()
    def _on_remove_button_clicked(self, _button):
        self.entry.delete_attribute(self.key)
        self.unparent()

    def _on_value_entry_changed(self, widget):
        self.entry.set_attribute(self.key, widget.get_text())

    @Gtk.Template.Callback()
    def _on_key_edit_button_clicked(self, _button):
        self.edit_stack.set_visible_child(self.key_entry)
        self.key_entry.grab_focus()

    @Gtk.Template.Callback()
    def _on_key_entry_activate(
        self,
        entry: Gtk.Entry,
    ) -> None:
        # pylint: disable=too-many-arguments
        new_key: str = entry.props.text
        if not new_key:
            entry.add_css_class("error")
            return

        if new_key == self.key:
            self.edit_stack.set_visible_child(self.key_edit_button)
            return

        if self.entry.has_attribute(new_key):
            entry.add_css_class("error")
            window = self.get_root()
            window.send_notification(_("Attribute key Already Exists"))
            return

        self.entry.set_attribute(new_key, self.entry.props.attributes[self.key])
        self.entry.delete_attribute(self.key)

        self.edit_stack.set_visible_child(self.key_edit_button)
        entry.remove_css_class("error")

        self.key_edit_button.set_label(new_key)
        self.key = new_key
