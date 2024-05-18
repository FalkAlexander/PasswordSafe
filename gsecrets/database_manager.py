# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import io
import json
import logging
from pathlib import Path

from gi.repository import Gio, GLib, GObject, Gtk
from pykeepass import PyKeePass

import gsecrets.config_manager as config
from gsecrets.safe_element import SafeEntry, SafeGroup
from gsecrets.utils import LazyValue, compare_passwords

QUARK = GLib.quark_from_string("secrets")


class DatabaseManager(GObject.Object):
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes
    """Implements database functionality that is independent of the UI.

    Useful attributes:
     .path: str containing the filepath of the database
     .is_dirty: bool telling whether the database is in a dirty state

    Group objects are of type `pykeepass.group.Group`
    Entry objects are of type `pykeepass.entry.Entry`
    Instances of both have useful attributes:
    .uuid: a `uuid.UUID` object
    """

    # self.db contains a `PyKeePass` database
    _elements_loaded = False
    password_try = ""
    _is_dirty = False  # Does the database need saving?
    save_running = False
    _opened = False

    # Used for checking if there are changes in the file.
    file_size: int | None = None
    file_mtime: int | None = None

    # Only used for setting the credentials to their actual values in case of
    # errors.
    old_password: str = ""
    composition_key: bytes | None = None

    trash_bin: SafeGroup | None = None
    root: SafeGroup | None = None

    locked = GObject.Property(type=bool, default=False)
    is_dirty = GObject.Property(type=bool, default=False)

    # To be emitted when the elements list model needs to be re sorted.
    sorting_changed = GObject.Signal(arg_types=(bool,))

    def __init__(self, key_providers: list, database_path: str) -> None:
        """Initialize the database handling logic.

        :param str database_path: The database path
        """
        super().__init__()

        self.entries = Gio.ListStore.new(SafeEntry)
        self.groups = Gio.ListStore.new(SafeGroup)

        self._key_providers = key_providers
        self._path = database_path
        self.db: PyKeePass = None

    def unlock_async(
        self,
        password: str,
        composition_key: bytes | None = None,
        callback: Gio.AsyncReadyCallback = None,
    ) -> None:
        """Unlocks and opens a safe.

        This pykeepass to open a safe database. If the database cannot
        be opened, an exception is raised.

        :param str password: password to use or an empty string
        :param str composition_key: composition_key as bytes
        :param GAsyncReadyCallback: callback run after the unlock operation ends
        """
        self._opened = False

        def unlock_task(task, _source_object, _task_data, _cancellable):
            if Path(self._path).suffix == ".kdb":
                # NOTE kdb is a an older format for Keepass databases.
                err = GLib.Error.new_literal(
                    QUARK,
                    "The kdb Format is not Supported",
                    0,
                )
                task.return_error(err)
                return

            try:
                db = PyKeePass(
                    self.path,
                    password,
                    io.BytesIO(composition_key) if composition_key else None,
                )
            except Exception as err:  # pylint: disable=broad-except
                err = GLib.Error.new_literal(QUARK, str(err), 1)
                task.return_error(err)
            else:
                self.composition_key = composition_key
                self._update_file_monitor()
                task.return_value(db)

        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(unlock_task)

    def unlock_finish(self, result):
        """Finish unlocking.

        Can raise errors.
        """
        _success, db = result.propagate_value()

        self.db = db
        self._opened = True
        logging.debug("Opening of safe %s was successful", self.path)

        if not self._elements_loaded:
            self.entries.splice(0, 0, [SafeEntry(self, e) for e in db.entries])
            self.groups.splice(0, 0, [SafeGroup(self, g) for g in db.groups])

            self._elements_loaded = True

        self.notify("description")
        self.notify("name")

    #
    # Database Modifications
    #

    def save_async(self, callback: Gio.AsyncReadyCallback) -> None:
        """Write all changes to database.

        This consists in two parts, we first save it to a byte stream in memory
        and then we write the contents of the stream into the database using
        Gio. This is done in this way since pykeepass save is not atomic,
        whereas GFile operations are.

        Note that certain operations in pykeepass can fail at the middle of the
        operation, nuking the database in the process.
        """
        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(self._save_task)

    def _save_task(self, task, _obj, _data, _cancellable):
        if self.save_running:
            task.return_boolean(False)
            logging.debug("Save already running")
            return

        if not self.is_dirty:
            task.return_boolean(False)
            logging.debug("Safe is not dirty")
            return

        logging.debug("Saving database %s", self.path)
        self.save_running = True

        try:
            self.db.save()
        except Exception as err:  # pylint: disable=broad-except
            err = GLib.Error.new_literal(QUARK, str(err), 2)
            task.return_error(err)
        else:
            self._update_file_monitor()
            task.return_boolean(True)

    def save_finish(self, result: Gio.AsyncResult) -> bool:
        """Finish save_async.

        Returns whether the safe was saved. Can raise GLib.Error.
        """
        self.save_running = False
        is_saved = result.propagate_boolean()

        self.is_dirty = False
        if is_saved:
            logging.debug("Database %s saved successfully", self.path)

        return is_saved

    def set_credentials_async(
        self,
        password: str,
        composition_key: bytes | None = None,
        callback: Gio.AsyncReadyCallback = None,
    ) -> None:
        """Set credentials for safe.

        It does almost the same as save_async, with the difference that
        correctly handles errors, it won't leave the database in a state where
        its fields have the incorrect values.
        """

        def set_credentials_task(task, obj, data, cancellable):
            self.old_password = self.password
            self.password = password

            self.composition_key = composition_key
            if composition_key:
                self.db.keyfile = io.BytesIO(composition_key)
            else:
                self.db.keyfile = None

            self.is_dirty = True

            self._save_task(task, obj, data, cancellable)

        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(set_credentials_task)

    def set_credentials_finish(self, result):
        self.save_running = False
        try:
            is_saved = result.propagate_boolean()
        except GLib.Error:
            self.password = self.old_password

            raise

        self.is_dirty = False
        if is_saved:
            logging.debug("Credentials changed successfully")

        return is_saved

    def add_to_history(self) -> None:
        uri = Gio.File.new_for_path(self._path).get_uri()

        recents = Gtk.RecentManager.get_default()
        recents.add_item(uri)

        # Set last opened database.
        config.set_last_opened_database(uri)

        if not config.get_remember_composite_key():
            return

        keyprovider_pairs = config.get_last_used_key_provider()

        data = {}
        for key_provider in self._key_providers:
            if key_provider.available and key_provider.key:
                provider_config = key_provider.config()
                data[type(key_provider).__name__] = provider_config

        keyprovider_pairs[uri] = json.dumps(data)
        config.set_last_used_key_provider(keyprovider_pairs)

    def _update_file_monitor(self):
        """Update the modified time and size of the database.

        This is a blocking operation.
        """
        gfile = Gio.File.new_for_path(self._path)
        attributes = (
            f"{Gio.FILE_ATTRIBUTE_STANDARD_SIZE},{Gio.FILE_ATTRIBUTE_TIME_MODIFIED}"
        )
        try:
            info = gfile.query_info(attributes, Gio.FileQueryInfoFlags.NONE, None)
        except GLib.Error:
            logging.exception("Could not read file size")
        else:
            self.file_size = info.get_size()
            self.file_mtime = info.get_modification_date_time().to_unix()

    def check_file_changes_async(self, callback: Gio.AsyncReadyCallback) -> None:
        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(self._check_file_changes_task)

    def _check_file_changes_task(self, task, _obj, _data, _cancellable):
        gfile = Gio.File.new_for_path(self._path)
        attributes = (
            f"{Gio.FILE_ATTRIBUTE_STANDARD_SIZE},{Gio.FILE_ATTRIBUTE_TIME_MODIFIED}"
        )
        try:
            info = gfile.query_info(attributes, Gio.FileQueryInfoFlags.NONE, None)
        except GLib.Error as err:
            err = GLib.Error.new_literal(QUARK, str(err), 3)
            task.return_error(err)
        else:
            if (
                self.file_size != info.get_size()
                or self.file_mtime != info.get_modification_date_time().to_unix()
            ):
                task.return_boolean(True)
            else:
                task.return_boolean(False)

    def check_file_changes_finish(self, result: Gio.AsyncResult) -> bool:
        """Finish check_file_changes_async.

        Returns whether the file was changed, can raise GLib.Error.
        """
        return result.propagate_boolean()

    @property
    def password(self) -> str:
        """Get the current password or '' if not set."""
        return self.db.password or ""

    @password.setter
    def password(self, new_password: str | None) -> None:
        """Set database password (None if a old_composition key is used)."""
        self.db.password = new_password
        self.is_dirty = True

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        """Get the database name or '' if not set."""
        return self.db.database_name or ""

    @name.setter  # type: ignore
    def name(self, new_name: str | None) -> None:
        """Set database name."""
        self.db.database_name = new_name
        self.is_dirty = True

    @GObject.Property(type=str, default="")
    def description(self) -> str:
        """Get the database description or '' if not set."""
        return self.db.database_description or ""

    @description.setter  # type: ignore
    def description(self, new_description: str | None) -> None:
        """Set database description."""
        self.db.database_description = new_description
        self.is_dirty = True

    @property
    def default_username(self) -> str:
        """Get the default username or '' if not set."""
        return self.db.default_username or ""

    @default_username.setter
    def default_username(self, new_username: str | None) -> None:
        """Set default username."""
        self.db.default_username = new_username
        self.is_dirty = True

    #
    # Read Database
    #

    # Check if entry with title in group exists
    def check_entry_in_group_exists(self, title, group):
        entry = self.db.find_entries(
            title=title,
            group=group,
            recursive=False,
            history=False,
            first=True,
        )
        return entry is not None

    #
    # Database creation methods
    #

    # Set the first password entered by the user (for comparing reasons)
    def set_password_try(self, password):
        self.password_try = password

    def compare_passwords(self, password2: str) -> bool:
        """Compare the first password entered by the user with the second one.

        It also does not allow empty passwords.
        :returns: True if passwords match and are non-empty.
        """
        return compare_passwords(self.password_try, password2)

    def parent_checker(self, current_group, moved_group):
        """Return True if moved_group is an ancestor of current_group."""
        # recursively invoke ourself until we reach the root group
        if current_group.is_root_group:
            return False
        if current_group.uuid == moved_group.uuid:
            return True
        return self.parent_checker(current_group.parentgroup, moved_group)

    @property
    def version(self):
        """Returns the database version."""
        return self.db.version

    @property
    def opened(self) -> bool:
        return self._opened

    @property
    def path(self) -> str:
        return self._path

    def get_salt_as_lazy(self) -> LazyValue[bytes]:
        path = self.path
        return LazyValue(lambda: DatabaseManager.salt_from_path(path))

    # This is static so as there is no need to carry around a
    # DatabaseManager object in another thread
    @staticmethod
    def salt_from_path(path: str) -> bytes:
        db = PyKeePass(path, None, None, decrypt=False)
        return db.database_salt
