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
from gsecrets.utils import KeyFileFilter

if typing.TYPE_CHECKING:
    from gsecrets.widgets.window import Window


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlock_database.ui")
class UnlockDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "UnlockDatabase"

    keyfile_path = None
    _keyfile_hash = None

    database_manager: DatabaseManager | None = None

    clear_button = Gtk.Template.Child()
    keyfile_button = Gtk.Template.Child()
    keyfile_label = Gtk.Template.Child()
    keyfile_spinner = Gtk.Template.Child()
    keyfile_stack = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    spinner_stack = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    headerbar = Gtk.Template.Child()
    unlock_button = Gtk.Template.Child()

    def __init__(self, window: Window, database_file: Gio.File) -> None:
        self.install_action("clear-keyfile", None, self.on_clear_keyfile)

        super().__init__()

        filepath = database_file.get_path()

        self.window = window

        # Reset headerbar to initial state if it already exists.
        self.headerbar.title.props.title = database_file.get_basename()

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == filepath
            if is_current:
                self.database_manager = database.database_manager

        if not self.database_manager:
            self.database_manager = DatabaseManager(filepath)

        if gsecrets.config_manager.get_remember_composite_key():
            self._set_last_used_keyfile()

        if gsecrets.const.IS_DEVEL:
            self.status_page.props.icon_name = gsecrets.const.APP_ID

    def do_unmap(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_unmap(self)
        self.keyfile_spinner.props.spinning = False
        self.spinner.props.spinning = False

    def grab_entry_focus(self):
        self.password_entry.grab_focus()

    @Gtk.Template.Callback()
    def _on_keyfile_button_clicked(self, _widget):
        """cb invoked when we unlock a database via keyfile"""
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(KeyFileFilter().file_filter)

        dialog = Gtk.FileDialog.new()
        dialog.props.filters = filters
        dialog.props.title = _("Select Keyfile")

        dialog.open(self.window, None, self.on_dialog_response)

    def on_dialog_response(self, dialog, result):
        try:
            keyfile = dialog.open_finish(result)
        except GLib.Error as err:
            logging.debug("Could not open file: %s", err.message)
        else:
            self.set_keyfile(keyfile)

    def set_keyfile(self, keyfile: Gio.File) -> None:
        self.keyfile_path = keyfile.get_path()
        keyfile.load_bytes_async(None, self.load_keyfile_callback)

        self.keyfile_stack.props.visible_child_name = "spinner"
        self.keyfile_spinner.start()
        self.keyfile_button.props.sensitive = False

        logging.debug("Keyfile selected: %s", keyfile.get_path())

    def load_keyfile_callback(self, keyfile, result):
        try:
            gbytes, _etag = keyfile.load_bytes_finish(result)
        except GLib.Error as err:
            logging.debug("Could not set keyfile hash: %s", err.message)

            self._wrong_keyfile()
        else:
            keyfile_hash = GLib.compute_checksum_for_bytes(
                GLib.ChecksumType.SHA1, gbytes
            )
            file_path = keyfile.get_path()
            basename = keyfile.get_basename()
            if keyfile_hash:
                self.keyfile_hash = keyfile_hash
                self.keyfile_path = file_path

            self._reset_keyfile_button()
            self.keyfile_label.set_label(basename)
        finally:
            self.keyfile_stack.props.visible_child_name = "label"
            self.keyfile_spinner.stop()
            self.keyfile_button.props.sensitive = True

    def is_safe_open_elsewhere(self) -> bool:
        """Returns True if the safe is already open but not in the
        current window."""
        is_current = False
        db_path = self.database_manager.path  # type: ignore
        is_open = self.window.application.is_safe_open(db_path)

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == db_path

        return is_open and not is_current

    @Gtk.Template.Callback()
    def _on_password_entry_activate(self, _entry):
        self.unlock_button.activate()

    @Gtk.Template.Callback()
    def _on_unlock_button_clicked(self, _widget):
        entered_pwd = self.password_entry.get_text()
        if not (entered_pwd or self.keyfile_path):
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

    def _set_last_used_keyfile(self):
        pairs = gsecrets.config_manager.get_last_used_composite_key()
        uri = Gio.File.new_for_path(self.database_manager.path).get_uri()
        if pairs:
            keyfile_path = None

            for pair in pairs:
                if pair[0] == uri:
                    keyfile_path = pair[1]
                    break

            if keyfile_path is not None:
                keyfile = Gio.File.new_for_path(keyfile_path)
                if keyfile.query_exists():
                    self.set_keyfile(keyfile)

    #
    # Open Database
    #

    def _open_database(self):
        self.spinner_stack.props.visible_child_name = "spinner"
        self.spinner.start()

        self._set_sensitive(False)

        password = self.password_entry.props.text
        keyfile = self.keyfile_path

        self.database_manager.unlock_async(
            password,
            keyfile,
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

    def _wrong_keyfile(self):
        self.keyfile_button.add_css_class("destructive-action")

        self.keyfile_label.set_label(_("_Try Again"))

    def _reset_keyfile_button(self):
        self.keyfile_button.remove_css_class("destructive-action")

        self.keyfile_label.set_label(_("_Select Keyfile"))

    def _reset_unlock_button(self):
        self.spinner.stop()
        self.spinner_stack.props.visible_child_name = "image"

    def _reset_page(self):
        self.keyfile_path = None
        self.keyfile_hash = None

        self.password_entry.set_text("")
        self.password_entry.remove_css_class("error")

        self._set_sensitive(True)

        self._reset_keyfile_button()
        self._reset_unlock_button()

    def _set_sensitive(self, sensitive):
        self.password_entry.set_sensitive(sensitive)
        self.keyfile_button.set_sensitive(sensitive)
        self.unlock_button.set_sensitive(sensitive)
        self.headerbar.set_sensitive(sensitive)

        self.action_set_enabled("clear-keyfile", sensitive)

    def on_clear_keyfile(self, _widget, _name, _param):
        self.keyfile_path = None
        self.keyfile_hash = None

        self._reset_keyfile_button()

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

    @property
    def keyfile_hash(self) -> str | None:
        return self._keyfile_hash

    @keyfile_hash.setter  # type: ignore
    def keyfile_hash(self, keyfile_hash: str | None) -> None:
        self._keyfile_hash = keyfile_hash
        self.clear_button.props.visible = keyfile_hash is not None
