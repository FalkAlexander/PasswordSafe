# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from gsecrets.safe_element import SafeEntry
from gsecrets.unlocked_database import UnlockedDatabase

if typing.TYPE_CHECKING:
    from gsecrets.database_manager import DatabaseManager


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/credentials_group.ui")
class CredentialsGroup(Adw.PreferencesGroup):
    """Widget to set the username and password of an entry."""

    __gtype_name__ = "CredentialsGroup"

    _copy_password_button = Gtk.Template.Child()
    _generate_password_button = Gtk.Template.Child()
    _password_entry_row = Gtk.Template.Child()
    _username_entry_row = Gtk.Template.Child()

    _unlocked_database: UnlockedDatabase | None = None

    _safe_entry = None

    @property
    def username(self):
        return self._username_entry_row.props.text

    @GObject.Property(type=SafeEntry)
    def entry(self):
        return self._safe_entry

    @entry.setter  # type: ignore
    def entry(self, entry):
        self._safe_entry = entry
        self._password_entry_row.props.text = entry.props.password

        self._password_entry_row.get_delegate().connect(
            "notify::visibility", self._on_password_visibility_changed,
        )

        entry.bind_property(
            "username",
            self._username_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )
        entry.bind_property(
            "password",
            self._password_entry_row,
            "text",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

    @property
    def unlocked_database(self) -> UnlockedDatabase | None:
        return self._unlocked_database

    @unlocked_database.setter  # type: ignore
    def unlocked_database(self, unlocked_database: UnlockedDatabase) -> None:
        self._db_manager: DatabaseManager = unlocked_database.database_manager
        self._unlocked_database = unlocked_database

    @Gtk.Template.Callback()
    def _on_copy_password_button_clicked(self, _widget: Gtk.Button) -> None:
        self.copy_password()

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self._password_entry_row.props.text = password

    @Gtk.Template.Callback()
    def _on_password_value_changed(self, _entry: Gtk.Entry) -> None:
        """Invoked when the password entry has changed

        Take note that this callback is already invoked after the initial
        population of the entry when nothing has really been changed by
        the user, so be careful of doing things here that could have unwanted
        side-effects.
        """
        if self._unlocked_database:
            self._unlocked_database.start_database_lock_timer()

    @Gtk.Template.Callback()
    def _on_username_copy_button_clicked(self, _button):
        if self._unlocked_database:
            username = self._username_entry_row.props.text
            self._unlocked_database.send_to_clipboard(
                username,
                _("Username copied"),
            )

    @Gtk.Template.Callback()
    def _on_apply(self, _entry_row):
        if u_db := self._unlocked_database:
            u_db.window.send_notification(_("Saved in history"))

        self._safe_entry.save_history()

    def copy_password(self) -> None:
        if self._unlocked_database:
            password: str = self._password_entry_row.props.text
            self._unlocked_database.send_to_clipboard(
                password,
                _("Password copied"),
            )

    def _on_password_visibility_changed(self, _widget, _value):
        if self._password_entry_row.get_delegate().get_visibility():
            self._password_entry_row.add_css_class("monospace")
        else:
            self._password_entry_row.remove_css_class("monospace")
