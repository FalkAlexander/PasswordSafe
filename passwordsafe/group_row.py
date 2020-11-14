# SPDX-License-Identifier: GPL-3.0-only
import typing
from gettext import gettext as _
from typing import Optional

from gi.repository import Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.unlocked_database import UnlockedDatabase


class GroupRow(Gtk.ListBoxRow):
    unlocked_database = NotImplemented
    group_uuid = NotImplemented
    label = NotImplemented
    selection_checkbox = NotImplemented
    edit_button = NotImplemented
    type = "GroupRow"

    def __init__(self, unlocked_database, dbm, group):
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class("row")

        self.unlocked_database = unlocked_database

        self.group_uuid = group.uuid
        self.label = dbm.get_group_name(group)

        self._entry_box_gesture: Optional[Gtk.GestureMultiPress] = None
        self.props.activatable = False
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
        if self.unlocked_database.props.selection_mode:
            self.selection_checkbox.show()

        # Edit Button
        self.edit_button = builder.get_object("group_edit_button")
        self.edit_button.connect("clicked", self.unlocked_database.on_group_edit_button_clicked)

    def _on_group_row_button_pressed(
            self, gesture: Gtk.GestureMultiPress, n_press: int, event_x: float,
            event_y: float) -> bool:
        # pylint: disable=unused-argument
        # pylint: disable=too-many-arguments
        db_view: UnlockedDatabase = self.unlocked_database
        db_view.start_database_lock_timer()

        button: int = gesture.get_current_button()
        if button == 1:
            group = db_view.database_manager.get_group(self.get_uuid())
            db_view.show_element(group)
            return True

        if (button == 3
                and not db_view.props.search_active):
            if db_view.props.selection_mode:
                active = self.selection_checkbox.props.active
                self.selection_checkbox.props.active = not active
            else:
                db_view.props.selection_mode = True
                self.selection_checkbox.props.active = True

        return True

    def get_uuid(self):
        return self.group_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def get_type(self):
        return self.type

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.get_active():
            self.unlocked_database.selection_ui.add_group(self)
        else:
            self.unlocked_database.selection_ui.remove_group(self)
