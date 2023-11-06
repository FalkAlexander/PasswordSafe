# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk

import gsecrets.config_manager
from gsecrets import const
from gsecrets.database_manager import DatabaseManager
from gsecrets.unlocked_database import UnlockedDatabase

if typing.TYPE_CHECKING:
    from gsecrets.widgets.window import Window


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlock_database.ui")
class UnlockDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "UnlockDatabase"

    database_manager: DatabaseManager | None = None

    password_entry = Gtk.Template.Child()
    key_group = Gtk.Template.Child()
    provider_group = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    headerbar = Gtk.Template.Child()
    unlock_button = Gtk.Template.Child()
    banner = Gtk.Template.Child()

    def __init__(self, window: Window, database_file: Gio.File) -> None:
        super().__init__()

        self.spinner = Gtk.Spinner.new()

        filepath = database_file.get_path()

        self.window = window
        self.keyfile = None
        self.keyfile_hash = None

        # Reset headerbar to initial state if it already exists.
        self.headerbar.title.props.title = database_file.get_basename()

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == filepath
            if is_current:
                self.database_manager = database.database_manager

        if not self.database_manager:
            self.database_manager = DatabaseManager(
                window.key_providers.get_key_providers(),
                filepath)

        if gsecrets.const.IS_DEVEL:
            self.status_page.props.icon_name = gsecrets.const.APP_ID

        self.window.set_default_widget(self.unlock_button)

        for key_provider in self.window.key_providers.get_key_providers():
            if key_provider.available:
                widget = key_provider.create_unlock_widget(self.database_manager)
                self.provider_group.add(widget)

    def do_unmap(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_unmap(self)
        self.spinner.props.spinning = False

    def grab_entry_focus(self):
        self.password_entry.grab_focus()

    def is_safe_open_elsewhere(self) -> bool:
        """Returns True if the safe is already open but not in the
        current window."""
        is_current = False
        db_path = self.database_manager.path  # type: ignore
        is_open = self.window.application.is_safe_open(db_path)

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == db_path

        return is_open and not is_current

    def _on_generated_composite_key(self, providers, result):
        self.unlock_button.set_sensitive(True)

        try:
            data = providers.generate_composite_key_finish(result)
            composite_key = data[0]
            self.keyfile = data[1]
            self.keyfile_hash = data[2]
        except GLib.Error as err:
            logging.error("Could not generate composite key: %s", err.message)
            self.window.send_notification(_("Failed to generate composite key"))
            return

        entered_pwd = self.password_entry.get_text()
        if not (entered_pwd or composite_key):
            return

        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                # pylint: disable=consider-using-f-string
                _("Safe {} is already open".format(self.database_manager.path))
            )
            return

        if not self.database_manager.opened:
            self._open_database()
            return

        if (
            entered_pwd == self.database_manager.password
            and self.database_manager.keyfile_hash == self.keyfile_hash
        ):
            self.database_manager.props.locked = False
            self.database_manager.add_to_history()
        else:
            self._unlock_failed()

    @Gtk.Template.Callback()
    def _on_unlock_button_clicked(self, widget: Gtk.Button) -> None:
        if not self.database_manager:
            return

        widget.set_sensitive(False)
        self.window.key_providers.generate_composite_key_async(
            self.database_manager.get_salt(),
            self._on_generated_composite_key)

    #
    # Open Database
    #

    def _open_database(self):
        self.unlock_button.props.child = self.spinner
        self.spinner.start()

        self._set_sensitive(False)

        password = self.password_entry.props.text

        self.database_manager.unlock_async(
            password,
            self.keyfile,
            self.keyfile_hash,
            self._unlock_callback,
        )

    def _unlock_callback(self, database_manager, result):
        try:
            database_manager.unlock_finish(result)
        except GLib.Error as err:
            logging.debug("Could not unlock safe: %s", err.message)
            self._unlock_failed()
            return

        opened = Gio.File.new_for_path(database_manager.path)

        if gsecrets.config_manager.get_development_backup_mode():
            self.store_backup(opened)

        database_manager.add_to_history()

        if self.window.unlocked_db is None:
            database = UnlockedDatabase(self.window, database_manager)
            self.window.unlocked_db = database
            self.window.unlocked_db_bin.props.child = database

        self.window.view = self.window.View.UNLOCKED_DATABASE
        self._reset_page()

    #
    # Helper Functions
    #

    def _unlock_failed(self) -> None:
        self.window.send_notification(_("Failed to unlock Safe"))

        self.password_entry.add_css_class("error")
        self.password_entry.delete_text(0, -1)
        self._set_sensitive(True)
        self._reset_unlock_button()

        # Regrab the focus of the entry.
        self.password_entry.grab_focus()

    def _reset_unlock_button(self):
        self.spinner.stop()
        self.unlock_button.props.label = _("Unlock")

    def _reset_page(self):
        self.keyfile_hash = None

        self.password_entry.set_text("")
        self.password_entry.remove_css_class("error")

        self._set_sensitive(True)

        self._reset_unlock_button()

    def _set_sensitive(self, sensitive):
        delegate = self.password_entry.get_delegate()
        if delegate.has_focus() and not sensitive:
            self.window.props.focus_widget = None

        for key in self.key_group:
            key.set_sensitive(sensitive)

        self.unlock_button.set_sensitive(sensitive)
        self.headerbar.set_sensitive(sensitive)

    def store_backup(self, gfile):
        cache_dir = os.path.join(GLib.get_user_cache_dir(), const.SHORT_NAME, "backup")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        current_time = GLib.DateTime.new_now_local().format("%F_%T")
        basename = os.path.splitext(gfile.get_basename())[0]
        backup_name = basename + "_backup_" + current_time + ".kdbx"
        backup = Gio.File.new_for_path(os.path.join(cache_dir, backup_name))

        def callback(gfile, result):
            try:
                gfile.copy_finish(result)
            except GLib.Error as err:
                logging.warning("Could not save database backup: %s", err.message)

        gfile.copy_async(
            backup,
            Gio.FileCopyFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            None,
            None,
            callback,
        )

    def show_banner(self, label: str) -> None:
        self.banner.set_title(label)
        self.banner.set_revealed(True)

    def close_banner(self):
        self.banner.set_revealed(False)
