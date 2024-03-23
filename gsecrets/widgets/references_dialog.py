# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import Adw, Gio, GLib, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/references_dialog.ui")
class ReferencesDialog(Adw.Dialog):
    __gtype_name__ = "ReferencesDialog"

    __property = "P"

    _codes_popover = Gtk.Template.Child()
    _property_label = Gtk.Template.Child()
    _property_popover_button = Gtk.Template.Child()
    _reference_entry = Gtk.Template.Child()
    _uuid_label = Gtk.Template.Child()
    _uuid_popover = Gtk.Template.Child()

    def __init__(self, unlocked_database):
        super().__init__()

        self.__unlocked_database = unlocked_database
        self.__database_manager = unlocked_database.database_manager

        self.__setup_actions()
        self.__setup_signals()
        self.__setup_widgets()

    def __setup_widgets(self) -> None:
        self.__update_reference_entry()

    def __setup_signals(self) -> None:
        self.__connect_model_buttons_signals()
        self.__database_manager.connect("notify::locked", self.__on_locked)

    def __setup_actions(self) -> None:
        action_group = Gio.SimpleActionGroup.new()
        for label in ["U", "N", "A", "P", "T"]:
            simple_action = Gio.SimpleAction.new(label, None)
            simple_action.connect("activate", self.__on_property_model_button_clicked)
            action_group.insert(simple_action)
        self.insert_action_group("reference", action_group)

    def __connect_model_buttons_signals(self):
        self._uuid_popover.set_parent(self._uuid_label)
        self._codes_popover.set_parent(self._property_label)

    def __update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.__unlocked_database.current_element.uuid
        encoded_uuid = uuid.hex.upper()

        self._property_popover_button.set_label(self.__property)

        self._reference_entry.set_text(
            "{REF:" + self.__property + "@I:" + encoded_uuid + "}",
        )

    @Gtk.Template.Callback()
    def _open_codes_popover(self, _gesture, _n_points, _x, _y):
        self._codes_popover.popup()

    @Gtk.Template.Callback()
    def _open_uuid_popover(self, _gesture, _n_points, _x, _y):
        self._uuid_popover.popup()

    @Gtk.Template.Callback()
    def _on_copy_secondary_button_clicked(self, entry, _position):
        self.__unlocked_database.start_database_lock_timer()
        self.__unlocked_database.clipboard.set(entry.get_text())

    def __on_property_model_button_clicked(
        self,
        action: Gio.Action,
        _parameter: GLib.Variant,
    ) -> None:
        self.__unlocked_database.start_database_lock_timer()
        self.__property = action.props.name
        self.__update_reference_entry()

    def __on_locked(self, database_manager, _value):
        locked = database_manager.props.locked
        if locked:
            self.close()
