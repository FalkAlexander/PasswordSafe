# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _
from typing import Optional

from gi.repository import GObject, Gtk
from passwordsafe.safe_element import SafeGroup

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


class GroupRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    group_uuid = NotImplemented
    label = NotImplemented
    selection_checkbox = NotImplemented
    edit_button = NotImplemented
    type = "GroupRow"

    def __init__(self, unlocked_database, safe_group):
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class("row")

        assert isinstance(safe_group, SafeGroup)
        self.unlocked_database = unlocked_database

        self.group_uuid = safe_group.uuid
        self.label = safe_group.name
        self.safe_group = safe_group

        self._entry_box_gesture: Optional[Gtk.GestureMultiPress] = None
        self.assemble_group_row()

    def assemble_group_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/group_row.ui")
        group_event_box = builder.get_object("group_event_box")

        self._entry_box_gesture = builder.get_object("entry_box_gesture")
        self._entry_box_gesture.connect(
            "pressed", self._on_group_row_button_pressed)

        group_name_label = builder.get_object("group_name_label")

        if self.label:
            group_name_label.set_text(self.label)
        else:
            group_name_label.set_markup("<span font-style=\"italic\">" + _("No group title specified") + "</span>")

        self.add(group_event_box)
        self.show()

        # Selection Mode Checkboxes
        self.selection_checkbox = builder.get_object("selection_checkbox_group")
        self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
        self.unlocked_database.bind_property(
            "selection_mode",
            self.selection_checkbox,
            "visible",
            GObject.BindingFlags.SYNC_CREATE,
        )
        self.unlocked_database.connect(
            "notify::selection-mode",
            self._on_selection_mode_change,
            self.selection_checkbox,
        )

        # Edit Button
        self.edit_button = builder.get_object("group_edit_button")
        self.edit_button.connect("clicked", self.on_group_edit_button_clicked)
        self.unlocked_database.bind_property(
            "selection_mode",
            self.edit_button,
            "visible",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN,
        )

    def _on_selection_mode_change(
        self,
        unlocked_db: UnlockedDatabase,
        _value: GObject.ParamSpecBoolean,
        checkbox: Gtk.CheckBox,
    ) -> None:
        if not unlocked_db.props.selection_mode:
            checkbox.set_active(False)

    def _on_group_row_button_pressed(
            self, _gesture: Gtk.GestureMultiPress, _n_press: int, _event_x: float,
            _event_y: float) -> None:
        # pylint: disable=too-many-arguments
        db_view: UnlockedDatabase = self.unlocked_database
        db_view.start_database_lock_timer()

        if not db_view.props.search_active:
            if db_view.props.selection_mode:
                active = self.selection_checkbox.props.active
                self.selection_checkbox.props.active = not active
            else:
                db_view.props.selection_mode = True
                self.selection_checkbox.props.active = True

    def get_uuid(self):
        return self.group_uuid

    def set_label(self, label):
        self.label = label

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.get_active():
            self.unlocked_database.selection_ui.add_group(self)
        else:
            self.unlocked_database.selection_ui.remove_group(self)

    def on_group_edit_button_clicked(self, button: Gtk.Button) -> None:
        """Edit button in a GroupRow was clicked

        button: The edit button in the GroupRow"""
        self.unlocked_database.start_database_lock_timer()  # Reset the lock timer

        self.unlocked_database.props.current_element = self.safe_group
        self.unlocked_database.show_page_of_new_directory(True, False)
