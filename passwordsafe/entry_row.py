# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import typing
from gettext import gettext as _
from typing import Optional
from gi.repository import GObject, Gtk

from passwordsafe.color_widget import Color

if typing.TYPE_CHECKING:
    from passwordsafe.safe_entry import SafeEntry
    from passwordsafe.unlocked_database import UnlockedDatabase  # pylint: disable=C0412


class EntryRow(Gtk.ListBoxRow):
    # pylint: disable=too-many-instance-attributes

    builder = Gtk.Builder()
    selection_checkbox = NotImplemented
    type = "EntryRow"

    def __init__(self, database: UnlockedDatabase, safe_entry: SafeEntry) -> None:
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class("row")

        self._safe_entry: SafeEntry = safe_entry

        self.unlocked_database = database
        self.db_manager = database.database_manager

        self.builder.add_from_resource("/org/gnome/PasswordSafe/entry_row.ui")

        self._entry_icon: Gtk.Image = self.builder.get_object("entry_icon")
        self._entry_name_label: Gtk.Label = self.builder.get_object("entry_name_label")
        self._entry_username_label: Gtk.Label = self.builder.get_object(
            "entry_subtitle_label")
        self._entry_box_gesture: Optional[Gtk.GestureMultiPress] = None
        self.assemble_entry_row()

    def assemble_entry_row(self):
        entry_event_box = self.builder.get_object("entry_event_box")

        self._entry_box_gesture = self.builder.get_object("entry_box_gesture")
        self._entry_box_gesture.connect(
            "pressed", self._on_entry_row_button_pressed)

        entry_copy_pass_button = self.builder.get_object("entry_copy_pass_button")
        entry_copy_user_button = self.builder.get_object("entry_copy_user_button")

        # Icon
        self._entry_icon.set_from_icon_name(self._safe_entry.icon_name, 20)
        self._safe_entry.connect("notify::name", self._on_entry_name_changed)
        self._on_entry_name_changed(self._safe_entry, None)

        self._safe_entry.connect("notify::username", self._on_entry_username_changed)
        self._on_entry_username_changed(self._safe_entry, None)

        entry_copy_pass_button.connect("clicked", self.on_entry_copy_pass_button_clicked)
        entry_copy_user_button.connect("clicked", self.on_entry_copy_user_button_clicked)
        self._safe_entry.connect("notify::color", self._on_entry_color_changed)
        self._on_entry_color_changed(self._safe_entry, None)

        self.add(entry_event_box)
        self.show()

        # Selection Mode Checkboxes
        self.selection_checkbox = self.builder.get_object("selection_checkbox_entry")
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

    def _on_selection_mode_change(
        self,
        unlocked_db: UnlockedDatabase,
        _value: GObject.ParamSpecBoolean,
        checkbox: Gtk.CheckBox,
    ) -> None:
        if not unlocked_db.props.selection_mode:
            checkbox.set_active(False)

    def _on_entry_row_button_pressed(
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

    @property
    def safe_entry(self) -> SafeEntry:
        return self._safe_entry

    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.props.active:
            self.unlocked_database.selection_ui.add_entry(self)
        else:
            self.unlocked_database.selection_ui.remove_entry(self)

    def on_entry_copy_pass_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.password,
            _("Password copied to clipboard"),
        )

    def on_entry_copy_user_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.username,
            _("Username copied to clipboard"),
        )

    def _on_entry_name_changed(
            self, _safe_entry: SafeEntry, _value: GObject.ParamSpec) -> None:
        entry_name = self._safe_entry.props.name
        style_context = self._entry_name_label.get_style_context()
        if entry_name:
            style_context.remove_class("italic")
            self._entry_name_label.props.label = entry_name
        else:
            style_context.add_class("italic")
            self._entry_name_label.props.label = _("Title not specified")

    def _on_entry_username_changed(
            self, _safe_entry: SafeEntry, _value: GObject.ParamSpec) -> None:
        entry_username = self._safe_entry.props.username
        style_context = self._entry_username_label.get_style_context()
        if entry_username:
            style_context.remove_class("italic")
            self._entry_username_label.props.label = entry_username
        else:
            style_context.add_class("italic")
            self._entry_username_label.props.label = _("Title not specified")

    def _on_entry_color_changed(
            self, _safe_entry: SafeEntry, _value: GObject.ParamSpec) -> None:
        color = self._safe_entry.props.color
        image_style = self._entry_icon.get_style_context()
        image_style.add_class(color + "List")
        if color not in [Color.NONE.value, Color.YELLOW.value]:
            image_style.remove_class("DarkIcon")
            image_style.add_class("BrightIcon")
