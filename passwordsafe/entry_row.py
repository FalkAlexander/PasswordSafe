# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import typing
from gettext import gettext as _
from gi.repository import GObject, Gtk

from passwordsafe.color_widget import Color

if typing.TYPE_CHECKING:
    from passwordsafe.safe_element import SafeEntry
    from passwordsafe.unlocked_database import UnlockedDatabase  # pylint: disable=ungrouped-imports


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/entry_row.ui")
class EntryRow(Gtk.ListBoxRow):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "EntryRow"

    selection_checkbox = Gtk.Template.Child()

    _entry_icon = Gtk.Template.Child()
    _entry_name_label = Gtk.Template.Child()
    _entry_username_label = Gtk.Template.Child()
    _entry_box_gesture = Gtk.Template.Child()
    _long_press_gesture = Gtk.Template.Child()

    type = "EntryRow"

    def __init__(self, database: UnlockedDatabase, safe_entry: SafeEntry) -> None:
        super().__init__()

        self.get_style_context().add_class("row")

        self._safe_entry: SafeEntry = safe_entry

        self.unlocked_database = database
        self.db_manager = database.database_manager

        self.assemble_entry_row()

    def assemble_entry_row(self):
        self._safe_entry.bind_property(
            "icon-name", self._entry_icon, "icon-name",
            GObject.BindingFlags.SYNC_CREATE)

        self._safe_entry.connect("notify::name", self._on_entry_name_changed)
        self._on_entry_name_changed(self._safe_entry, None)

        self._safe_entry.connect("notify::username", self._on_entry_username_changed)
        self._on_entry_username_changed(self._safe_entry, None)

        self._safe_entry.connect("notify::color", self._on_entry_color_changed)
        self._on_entry_color_changed(self._safe_entry, None)

        # Selection Mode Checkboxes
        self.unlocked_database.bind_property(
            "selection_mode",
            self.selection_checkbox,
            "visible",
            GObject.BindingFlags.SYNC_CREATE,
        )

    @Gtk.Template.Callback()
    def _on_entry_row_button_pressed(
            self, _gesture: Gtk.GestureClick, _n_press: int, _event_x: float,
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

    @Gtk.Template.Callback()
    def on_selection_checkbox_toggled(self, _widget):
        if self.selection_checkbox.props.active:
            self.unlocked_database.selection_ui.add_entry(self)
        else:
            self.unlocked_database.selection_ui.remove_entry(self)

    @Gtk.Template.Callback()
    def on_entry_copy_pass_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.password,
            _("Password copied to clipboard"),
        )

    @Gtk.Template.Callback()
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
            self._entry_username_label.props.label = _("No username specified")

    def _on_entry_color_changed(
            self, _safe_entry: SafeEntry, _value: GObject.ParamSpec) -> None:
        image_style = self._entry_icon.get_style_context()
        # Clear current style
        image_style.remove_class("DarkIcon")
        image_style.remove_class("BrightIcon")
        for color in Color:
            image_style.remove_class(color.value + "List")

        color = self._safe_entry.props.color
        image_style.add_class(color + "List")
        if color not in [Color.NONE.value, Color.YELLOW.value]:
            image_style.add_class("BrightIcon")
        else:
            image_style.add_class("DarkIcon")

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self.selection_checkbox.props.active = not self.selection_checkbox.props.active
