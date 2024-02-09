# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/add_attribute_dialog.ui")
class AddAttributeDialog(Adw.Dialog):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "AddAttributeDialog"

    _key_entry = Gtk.Template.Child()
    _protected_switch = Gtk.Template.Child()
    _value_entry = Gtk.Template.Child()
    _toast_overlay = Gtk.Template.Child()

    def __init__(self, db_manager, entry):
        super().__init__()

        self.entry = entry

        db_manager.connect("notify::locked", self._on_locked)

    @Gtk.Template.Callback()
    def _on_add_button_clicked(self, _button):
        key = self._key_entry.props.text

        # TODO Remove once https://github.com/libkeepass/pykeepass/issues/254 is
        # fixed
        if '"' in key or "'" in key:
            self._key_entry.add_css_class("error")
            toast = Adw.Toast.new(
                _("Attribute key contains an illegal character")
            )
            self._toast_overlay.add_toast(toast)
            return

        if key == "" or key is None:
            self._key_entry.add_css_class("error")
            return

        if self.entry.has_attribute(key):
            self._key_entry.add_css_class("error")
            toast = Adw.Toast.new(_("Attribute key already exists"))
            self._toast_overlay.add_toast(toast)
            return

        value = self._value_entry.props.text
        protected = self._protected_switch.props.active

        self.entry.set_attribute(key, value, protected)
        self.close()

    def _on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
