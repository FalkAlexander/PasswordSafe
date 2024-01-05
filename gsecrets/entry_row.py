# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gtk

from gsecrets.safe_element import EntryColor
from gsecrets.safe_element import SafeEntry

if typing.TYPE_CHECKING:
    from gsecrets.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/entry_row.ui")
class EntryRow(Adw.ActionRow):
    __gtype_name__ = "EntryRow"

    _checkbox_revealer = Gtk.Template.Child()
    _entry_icon = Gtk.Template.Child()
    selection_checkbox = Gtk.Template.Child()
    _entry_copy_user_button = Gtk.Template.Child()
    _entry_copy_pass_button = Gtk.Template.Child()
    _entry_copy_otp_button = Gtk.Template.Child()

    _safe_entry = None

    def __init__(self, database: UnlockedDatabase) -> None:
        super().__init__()

        self._signals = GObject.SignalGroup.new(SafeEntry)
        self._bindings = GObject.BindingGroup.new()

        self._bindings.bind(
            "icon-name",
            self._entry_icon,
            "icon-name",
            GObject.BindingFlags.SYNC_CREATE,
        )

        self._signals.connect_closure(
            "notify::name", self._on_entry_name_changed, False
        )
        self._signals.connect_closure(
            "notify::username", self._on_entry_username_changed, False
        )
        self._signals.connect_closure(
            "notify::password", self._on_entry_password_changed, False
        )
        self._signals.connect_closure(
            "notify::otp", self._on_entry_opt_token_changed, False
        )
        self._signals.connect_closure(
            "notify::color", self._on_entry_color_changed, False
        )
        self._signals.connect_closure(
            "notify::expired", self._on_entry_notify_expired, False
        )

        self.unlocked_database = database
        self.db_manager = database.database_manager

        # Selection Mode Checkboxes
        self.unlocked_database.bind_property(
            "selection_mode",
            self._checkbox_revealer,
            "reveal-child",
            GObject.BindingFlags.SYNC_CREATE,
        )

    @GObject.Property(type=SafeEntry)
    def safe_entry(self):
        return self._safe_entry

    @safe_entry.setter  # type: ignore
    def safe_entry(self, element):
        self._safe_entry = element

        self._signals.props.target = element
        self._bindings.props.source = element

        self._on_entry_name_changed(element, None)
        self._on_entry_username_changed(element, None)
        self._on_entry_password_changed(element, None)
        self._on_entry_opt_token_changed(element, None)
        self._on_entry_color_changed(element, None)
        self._on_entry_notify_expired(element, None)

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

    @Gtk.Template.Callback()
    def on_selection_checkbox_toggled(self, _widget):
        self.unlocked_database.start_database_lock_timer()

        if self.selection_checkbox.props.active:
            self.unlocked_database.selection_mode_headerbar.add_entry(self)
        else:
            self.unlocked_database.selection_mode_headerbar.remove_entry(self)

    @Gtk.Template.Callback()
    def on_entry_copy_pass_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.password,
            _("Password copied"),
        )

    @Gtk.Template.Callback()
    def on_entry_copy_user_button_clicked(self, _button):
        self.unlocked_database.send_to_clipboard(
            self._safe_entry.props.username,
            _("Username copied"),
        )

    @Gtk.Template.Callback()
    def on_entry_copy_otp_button_clicked(self, _button):
        if token := self._safe_entry.otp_token():
            self.unlocked_database.send_to_clipboard(
                token, _("One-Time Password copied"),
            )

    def _on_entry_name_changed(
        self, safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_name = GLib.markup_escape_text(safe_entry.props.name)
        if entry_name:
            self.remove_css_class("italic-title")
            self.props.title = entry_name
        else:
            self.add_css_class("italic-title")
            self.props.title = _("Title not Specified")

    def _on_entry_username_changed(
        self, safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_username = GLib.markup_escape_text(safe_entry.props.username)
        self.props.subtitle = entry_username
        self._entry_copy_user_button.set_visible(bool(entry_username))

    def _on_entry_password_changed(
        self, safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_password = GLib.markup_escape_text(safe_entry.props.password)
        self._entry_copy_pass_button.set_visible(bool(entry_password))

    def _on_entry_opt_token_changed(
        self, safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        entry_otp_token = safe_entry.otp_token()
        if entry_otp_token:
            self._entry_copy_otp_button.props.visible = True
        else:
            self._entry_copy_otp_button.props.visible = False

    def _on_entry_color_changed(
        self, safe_entry: SafeEntry, _value: GObject.ParamSpec
    ) -> None:
        # Clear current style
        for color in EntryColor:
            self._entry_icon.remove_css_class(color.value)

        color = safe_entry.props.color
        self._entry_icon.add_css_class(color)

    @Gtk.Template.Callback()
    def _on_long_press_gesture_pressed(self, _gesture, _x, _y):
        self.unlocked_database.props.selection_mode = True
        self.selection_checkbox.props.active = not self.selection_checkbox.props.active
