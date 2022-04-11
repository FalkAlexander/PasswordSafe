# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import io
import logging
from pathlib import Path

from gi.repository import Gio, GLib, GObject
from pykeepass import PyKeePass

import gsecrets.config_manager as config
from gsecrets.safe_element import SafeEntry, SafeGroup

QUARK = GLib.quark_from_string("secrets")


class DatabaseManager(GObject.Object):
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    """Implements database functionality that is independent of the UI

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

    # Only used for setting the credentials to their actual values in case of
    # errors.
    old_password: str = ""
    old_keyfile: str = ""
    old_keyfile_hash: str = ""

    locked = GObject.Property(type=bool, default=False)
    is_dirty = GObject.Property(type=bool, default=False)

    def __init__(self, database_path: str) -> None:
        """Initialize the database handling logic.

        :param str database_path: The database path
        """
        super().__init__()

        self.entries = Gio.ListStore.new(SafeEntry)
        self.groups = Gio.ListStore.new(SafeGroup)

        self._path = database_path
        self.db: PyKeePass = None
        self.keyfile_hash: str = ""

    def unlock_async(
        self,
        password: str,
        keyfile: str = "",
        keyfile_hash: str = "",
        callback: Gio.AsyncReadyCallback = None,
    ) -> None:
        """Unlocks an opens a safe.

        This pykeepass to open a safe database. If the database cannot
        be opened, an exception is raised.

        :param str password: password to use or an empty string
        :param str keyfile: keyfile path to use or an empty string
        :param str keyfile_hash: keyfile_hash to set
        :param GAsyncReadyCallback: callback run after the unlock operation ends
        """
        self._opened = False

        def unlock_task(task, _source_object, _task_data, _cancellable):
            if Path(self._path).suffix == ".kdb":
                # NOTE kdb is a an older format for Keepass databases.
                err = GLib.Error.new_literal(
                    QUARK, "The kdb Format is not Supported", 0
                )
                task.return_error(err)
                return

            try:
                db = PyKeePass(self.path, password, keyfile)
            except Exception as err:  # pylint: disable=broad-except
                err = GLib.Error.new_literal(QUARK, str(err), 1)
                task.return_error(err)
            else:
                self.keyfile_hash = keyfile_hash
                task.return_value(db)

        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(unlock_task)

    def unlock_finish(self, result):
        try:
            _success, db = result.propagate_value()
        except GLib.Error as err:
            raise err
        else:
            self.db = db
            self._opened = True
            logging.debug("Opening of safe %s was successful", self.path)

            if not self._elements_loaded:
                self.entries.splice(0, 0, [SafeEntry(self, e) for e in db.entries])
                self.groups.splice(0, 0, [SafeGroup(self, g) for g in db.groups])

                self._elements_loaded = True

    #
    # Database Modifications
    #

    def save_async(self, callback: Gio.AsyncReadyCallback) -> None:
        """Write all changes to database

        This consists in two parts, we first save it to a byte stream in memory
        and then we write the contents of the stream into the database using
        Gio. This is done in this way since pykeepass save is not atomic,
        whereas GFile operations are.

        Note that certain operations in pykeepass can fail at the middle of the
        operation, nuking the database in the process."""
        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(self._save_task)

    def _save_task(self, task, _obj, _data, _cancellable):
        stream = io.BytesIO()

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
            self.db.save(filename=stream)
        except Exception as err:  # pylint: disable=broad-except
            err = GLib.Error.new_literal(QUARK, str(err), 2)
            task.return_error(err)
        else:
            owned_bytes = stream.getvalue()
            if owned_bytes is None:
                error = GLib.Error.new_literal(QUARK, "Stream is empty", 3)
                task.return_error(error)
                return

            gfile = Gio.File.new_for_path(self.path)
            try:
                gfile.replace_contents(
                    owned_bytes,
                    None,
                    False,
                    Gio.FileCreateFlags.NONE,
                    None,
                )
            except GLib.Error as err:
                task.return_error(err)
            else:
                task.return_boolean(True)

    def save_finish(self, result: Gio.AsyncResult) -> bool:
        """Finishes save_async, returns whether the safe was saved.
        Can raise GLib.Error."""
        self.save_running = False
        try:
            is_saved = result.propagate_boolean()
        except GLib.Error as err:
            raise err
        else:
            self.is_dirty = False
            if is_saved:
                logging.debug("Database %s saved successfully", self.path)

            return is_saved

    def set_credentials_async(
        self, password, keyfile="", keyfile_hash="", callback=None
    ):
        """Sets credentials for safe

        It does almost the same as save_async, with the difference that
        correctly handles errors, it won't leave the database in a state where
        its fields have the incorrect values.
        """

        def set_credentials_task(task, obj, data, cancellable):
            self.old_password = self.password
            self.password = password

            self.old_keyfile = self.keyfile
            self.keyfile = keyfile

            self.old_keyfile_hash = self.keyfile_hash
            self.keyfile_hash = keyfile_hash

            self._save_task(task, obj, data, cancellable)

        task = Gio.Task.new(self, None, callback)
        task.run_in_thread(set_credentials_task)

    def set_credentials_finish(self, result):
        self.save_running = False
        try:
            is_saved = result.propagate_boolean()
        except GLib.Error as err:
            self.password = self.old_password
            self.keyfile = self.old_keyfile
            self.keyfile_hash = self.old_keyfile_hash

            raise err
        else:
            self.is_dirty = False
            if is_saved:
                logging.debug("Credentials changed successfully")

            return is_saved

    def add_to_history(self) -> None:
        # Add database uri to history.
        uri = Gio.File.new_for_path(self._path).get_uri()
        uri_list = config.get_last_opened_list()

        if uri in uri_list:
            uri_list.sort(key=uri.__eq__)
        else:
            uri_list.append(uri)

        config.set_last_opened_list(uri_list[-10:])

    @property
    def password(self) -> str:
        """Get the current password or '' if not set"""
        return self.db.password or ""

    @password.setter
    def password(self, new_password: str | None) -> None:
        """Set database password (None if a keyfile is used)"""
        self.db.password = new_password
        self.is_dirty = True

    @property
    def keyfile(self) -> str:
        """Get the current keyfile or None if it is not set."""
        return self.db.keyfile

    @keyfile.setter
    def keyfile(self, new_keyfile: str | None) -> None:
        self.db.keyfile = new_keyfile
        self.is_dirty = True

    #
    # Read Database
    #

    # Check if entry with title in group exists
    def check_entry_in_group_exists(self, title, group):
        entry = self.db.find_entries(
            title=title, group=group, recursive=False, history=False, first=True
        )
        if entry is None:
            return False
        return True

    #
    # Database creation methods
    #

    # Set the first password entered by the user (for comparing reasons)
    def set_password_try(self, password):
        self.password_try = password

    def compare_passwords(self, password2: str) -> bool:
        """Compare the first password entered by the user with the second one

        It also does not allow empty passwords.
        :returns: True if passwords match and are non-empty.
        """
        if password2 and self.password_try == password2:
            return True
        return False

    def parent_checker(self, current_group, moved_group):
        """Returns True if moved_group is an ancestor of current_group"""
        # recursively invoke ourself until we reach the root group
        if current_group.is_root_group:
            return False
        if current_group.uuid == moved_group.uuid:
            return True
        return self.parent_checker(current_group.parentgroup, moved_group)

    @property
    def version(self):
        """returns the database version"""
        return self.db.version

    @property
    def opened(self) -> bool:
        return self._opened

    @property
    def path(self) -> str:
        return self._path
