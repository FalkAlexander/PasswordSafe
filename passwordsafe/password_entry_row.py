# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from gettext import gettext as _

from gi.repository import Adw, Gtk

if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager
    from passwordsafe.safe_element import SafeEntry
    from passwordsafe.unlocked_database import UnlockedDatabase


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/password_entry_row.ui")
class PasswordEntryRow(Adw.Bin):

    __gtype_name__ = "PasswordEntryRow"

    _generate_password_button = Gtk.Template.Child()
    _password_level_bar = Gtk.Template.Child()
    _password_value_entry = Gtk.Template.Child()
    _copy_password_button = Gtk.Template.Child()

    def __init__(self, unlocked_database: UnlockedDatabase) -> None:
        """Widget to set the password of an entry

        :param unlocked_database: unlocked database
        """
        super().__init__()

        self._unlocked_database: UnlockedDatabase = unlocked_database
        self._db_manager: DatabaseManager = unlocked_database.database_manager

        self._safe_entry: SafeEntry = unlocked_database.current_element

        self._password_value_entry.props.text = self._safe_entry.props.password
        self._password_value_entry.bind_property("text", self._safe_entry, "password")
        self._password_value_entry.props.enable_undo = True

    @Gtk.Template.Callback()
    def _on_copy_password_button_clicked(self, _widget: Gtk.Button) -> None:
        self.copy_password()

    @Gtk.Template.Callback()
    def on_password_generated(self, _popover, password):
        self._password_value_entry.props.text = password

    @Gtk.Template.Callback()
    def _on_password_value_changed(self, _entry: Gtk.Entry) -> None:
        """Invoked when the password entry has changed

        Take note that this callback is already invoked after the initial
        population of the entry when nothing has really been changed by
        the user, so be careful of doing things here that could have unwanted
        side-effects.
        """
        self._unlocked_database.start_database_lock_timer()

    def copy_password(self) -> None:
        password: str = self._password_value_entry.props.text
        self._unlocked_database.send_to_clipboard(
            password,
            _("Password Copied"),
        )
