# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from gsecrets.color_widget import Color

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeEntry
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/entry_row.ui")
class EntryRow(Adw.ActionRow):

    __gtype_name__ = "EntryRow"

    _checkbox_revealer = Gtk.Template.Child()
    _entry_icon = Gtk.Template.Child()
    selection_checkbox = Gtk.Template.Child()

    def __init__(self, database: UnlockedDatabase, safe_entry: SafeEntry) -> None:
        super().__init__()

        self._safe_entry: SafeEntry = safe_entry

        self.unlocked_database = database
        self.db_manager = database.database_manager

        self.assemble_entry_row()

    def assemble_entry_row(self):
        self._safe_entry.bind_property(
            "icon-name", self._entry_icon, "icon-name", GObject.BindingFlags.SYNC_CREATE
        )

        self._safe_entry.connect("notify::name", self._on_entry_name_changed)
        self._on_entry_name_changed(self._safe_entry, None)

        self._safe_entry.connect("notify::username", self._on_entry_username_changed)
        self._on_entry_username_changed(self._safe_entry, None)

        self._safe_entry.connect("notify::color", self._on_entry_color_changed)
        self._on_entry_color_changed(self._safe_entry, None)

        # Selection Mode Checkboxes
        self.unlocked_database.bind_property(
            "selection_mode",
            self._checkbox_revealer,
            "reveal-child",
            GObject.BindingFlags.SYNC_CREATE,
        )

        # Expiration Date
        self.safe_entry.connect(
            "notify::expired",
            self._on_entry_notify_expired,
        )
        self._on_entry_notify_expired(self.safe_entry, None)

    def _on_entry_notify_expired(self, safe_entry, _gparam):
        if safe_entry.expired and safe_entry.props.expires:
            self.add_css_class("strikethrough")
        else:
            self.remove_css_class("strikethrough")

    @Gtk.Template.Callback()
    def _on_entry_row_button_pressed(
        self,
        _gesture: Gtk.GestureClick,
        _n_press: int,
        _event_x: float,
        _event_y: float,
    ) -> None:
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
            self.unlocked_database.selection_mode_headerbar.add_entry(self)
        else:
            self.unlocked_database.selection_mode_headerbar.remove_entry(self)

    @Gtk.Template.Callback()
    def on_entry_copy_pass_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.password,
            _("Password Copied"),
        )

    @Gtk.Template.Callback()
    def on_entry_copy_user_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.username,
            _("Username Copied"),
        )

    def _on_entry_name_changed(
        self, _safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_name = self._safe_entry.props.name
        if entry_name:
            self.remove_css_class("italic-title")
            self.props.title = entry_name
        else:
            self.add_css_class("italic-title")
            self.props.title = _("Title not Specified")

    def _on_entry_username_changed(
        self, _safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_username = self._safe_entry.props.username
        if entry_username:
            self.remove_css_class("italic-subtitle")
            self.props.subtitle = entry_username
        else:
            self.add_css_class("italic-subtitle")
            self.props.subtitle = _("Username not specified")

    def _on_entry_color_changed(
        self, _safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        # Clear current style
        for color in Color:
            self._entry_icon.remove_css_class(color.value)

        color = self._safe_entry.props.color
        self._entry_icon.add_css_class(color)

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, _gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self.selection_checkbox.props.active = not self.selection_checkbox.props.active
