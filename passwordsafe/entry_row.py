# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import typing
from gettext import gettext as _
from uuid import UUID
from typing import Optional
from gi.repository import Gtk

import passwordsafe.config_manager
import passwordsafe.icon
from passwordsafe.color_widget import Color

if typing.TYPE_CHECKING:
    from pykeepass.entry import Entry
    from passwordsafe.unlocked_database import UnlockedDatabase  # pylint: disable=C0412


class EntryRow(Gtk.ListBoxRow):
    # pylint: disable=too-many-instance-attributes

    builder = Gtk.Builder()
    selection_checkbox = NotImplemented
    type = "EntryRow"

    def __init__(self, database: UnlockedDatabase, entry: Entry) -> None:
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class("row")

        self.unlocked_database = database
        self.db_manager = database.database_manager

        self.entry_uuid = entry.uuid
        self.icon: Optional[int] = self.db_manager.get_icon(entry)
        self.label: str = entry.title or ""
        self.color = self.db_manager.get_entry_color(entry)
        self.username: str = entry.username or ""
        if self.username.startswith("{REF:U"):
            # Lookup reference and put in the "real" username
            uuid = UUID(self.unlocked_database.reference_to_hex_uuid(self.username))
            self.username = self.db_manager.get_entry_username(uuid)

        self._entry_box_gesture: Optional[Gtk.GestureMultiPress] = None
        self.assemble_entry_row()

    def assemble_entry_row(self):
        self.builder.add_from_resource("/org/gnome/PasswordSafe/entry_row.ui")
        entry_event_box = self.builder.get_object("entry_event_box")

        self._entry_box_gesture = self.builder.get_object("entry_box_gesture")
        self._entry_box_gesture.connect(
            "pressed", self._on_entry_row_button_pressed)

        entry_icon = self.builder.get_object("entry_icon")
        entry_name_label = self.builder.get_object("entry_name_label")
        entry_subtitle_label = self.builder.get_object("entry_subtitle_label")
        entry_copy_pass_button = self.builder.get_object("entry_copy_pass_button")
        entry_copy_user_button = self.builder.get_object("entry_copy_user_button")

        # Icon
        icon_name: str = passwordsafe.icon.get_icon_name(self.icon)
        entry_icon.set_from_icon_name(icon_name, 20)
        # Title/Name
        if self.label:
            entry_name_label.set_text(self.label)
        else:
            entry_name_label.set_markup("<span font-style=\"italic\">" + _("Title not specified") + "</span>")

        # Subtitle
        if self.username:
            entry_subtitle_label.set_text(self.username)
        else:
            entry_subtitle_label.set_markup("<span font-style=\"italic\">" + _("No username specified") + "</span>")

        entry_copy_pass_button.connect("clicked", self.on_entry_copy_pass_button_clicked)
        entry_copy_user_button.connect("clicked", self.on_entry_copy_user_button_clicked)

        # Color Button
        image_style = entry_icon.get_style_context()
        image_style.add_class(self.color + "List")
        if self.color != Color.NONE.value:
            image_style.remove_class("DarkIcon")
            image_style.add_class("BrightIcon")

        self.add(entry_event_box)
        self.show()

        # Selection Mode Checkboxes
        self.selection_checkbox = self.builder.get_object("selection_checkbox_entry")
        self.selection_checkbox.connect("toggled", self.on_selection_checkbox_toggled)
        if self.unlocked_database.props.selection_mode:
            self.selection_checkbox.show()

    def _on_entry_row_button_pressed(
            self, _gesture: Gtk.GestureMultiPress, _n_press: int, _event_x: float,
            _event_y: float) -> bool:
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

        return True

    def get_uuid(self):
        return self.entry_uuid

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.props.active:
            self.unlocked_database.selection_ui.add_entry(self)
        else:
            self.unlocked_database.selection_ui.remove_entry(self)

    def on_entry_copy_pass_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self.db_manager.get_entry_password(self.entry_uuid),
            _("Password copied to clipboard"),
        )

    def on_entry_copy_user_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self.db_manager.get_entry_username(self.entry_uuid),
            _("Username copied to clipboard"),
        )
