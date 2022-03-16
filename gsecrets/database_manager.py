# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import io
import logging
import threading
from pathlib import Path
from typing import Callable
from uuid import UUID

from gi.repository import Gio, GLib, GObject
from pykeepass import PyKeePass

from gsecrets.safe_element import SafeElement


class DatabaseManager(GObject.GObject):
    # pylint: disable=too-many-public-methods

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
    password_try = ""
    _is_dirty = False  # Does the database need saving?
    save_running = False
    _opened = False

    locked = GObject.Property(type=bool, default=False)
    is_dirty = GObject.Property(type=bool, default=False)

    def __init__(self, database_path: str) -> None:
        """Initialize the database handling logic.

        :param str database_path: The database path
        """
        super().__init__()

        self._path = database_path
        self.db: PyKeePass = None
        self.keyfile_hash: str = ""

    def unlock(self, password: str, keyfile: str = "", keyfile_hash: str = "") -> None:
        """Unlocks an opens a safe.

        This pykeepass to open a safe database. If the database cannot
        be opened, an exception is raised.

        :param str password: password to use or an empty string
        :param str keyfile: keyfile path to use or an empty string
        :param str keyfile_hash: keyfile_hash to set
        """
        self._opened = False
        self.keyfile_hash = keyfile_hash

        if Path(self._path).suffix == ".kdb":
            # NOTE kdb is a an older format for Keepass databases.
            logging.error("The kdb Format is not Supported")
            raise OSError("The kdb Format is not Supported")

        try:
            self.db = PyKeePass(self.path, password, keyfile)
        except Exception as err:  # pylint: disable=broad-except
            logging.debug("Could not open safe: %s", err)
            raise OSError("Failed to Unlock Safe") from err
        else:
            logging.debug("Opening of safe %s was successful", self.path)
            self._opened = True

    def _unlock_wrapper(  # pylint: disable=too-many-arguments
        self,
        password: str,
        keyfile: str = "",
        keyfile_hash: str = "",
        success_cb: Callable[[DatabaseManager], None] = None,
        error_cb: Callable[[], None] = None,
    ) -> None:
        try:
            self.unlock(password, keyfile, keyfile_hash)
        except OSError:
            GLib.idle_add(error_cb)
        else:
            GLib.idle_add(success_cb, self)

    def unlock_async(  # pylint: disable=too-many-arguments
        self,
        password: str,
        keyfile: str = "",
        keyfile_hash: str = "",
        success_cb: Callable[[DatabaseManager], None] = None,
        error_cb: Callable[[], None] = None,
    ) -> None:
        unlock_thread = threading.Thread(
            target=self._unlock_wrapper,
            args=[password, keyfile, keyfile_hash, success_cb, error_cb],
        )
        unlock_thread.start()

    #
    # Database Modifications
    #

    # Write all changes to database
    #
    # This consists in two parts, we first save it to a byte stream in memory
    # and then we write the contents of the stream into the database using Gio.
    # This is done in this way since pykeepass save is not atomic, whereas GFile
    # operations are.
    #
    # Note that certain operations in pykeepass can fail at the middle of the
    # operation, nuking the database in the process.
    def save_database(self, notification=False):
        if not self.save_running and self.is_dirty:
            self.save_running = True

            save_thread = threading.Thread(
                target=self.save_thread, args=[notification]
            )
            save_thread.daemon = False
            save_thread.start()

    def save_thread(self, notification: bool) -> None:
        succeeded = False
        stream = io.BytesIO()
        try:
            self.db.save(filename=stream)
            succeeded = True
        except Exception as err:  # pylint: disable=broad-except
            logging.error("Error occurred while saving database: %s", err)
        finally:
            GLib.idle_add(self.save_thread_finished, succeeded, notification, stream)

    def save_thread_finished(
        self, succeeded: bool, notification: bool, stream: io.BytesIO
    ) -> None:
        owned_bytes = stream.getvalue()
        if succeeded and owned_bytes:
            gfile = Gio.File.new_for_path(self.path)
            gbytes = GLib.Bytes.new(owned_bytes)
            gfile.replace_contents_bytes_async(
                gbytes,
                None,
                False,
                Gio.FileCreateFlags.NONE,
                None,
                self.replace_contents_cb,
                notification,
            )
        else:
            self.save_running = False
            if notification:
                self.emit("save-notification", False)

    def replace_contents_cb(self, gfile, result, notification):
        succeeded = False
        try:
            gfile.replace_contents_finish(result)
        except GLib.Error as err:  # pylint: disable=broad-except
            logging.error("Could not save database: %s", err)
        else:
            logging.debug("Saved database")
            self.is_dirty = False
            succeeded = True
        finally:
            self.save_running = False
            if notification:
                self.emit("save-notification", succeeded)

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

    # TODO This should be renamed to "saved" and it should have a argument
    # telling whether this should present a notification, probably by saying if
    # this was an automatic save.
    @GObject.Signal(arg_types=(bool,))
    def save_notification(self, _saved):
        return

    @GObject.Signal(
        arg_types=(
            SafeElement,
            object,
        )
    )
    def element_added(self, _element: SafeElement, _parent_uuid: UUID) -> None:
        """Signal emitted when a new element was added to the database
        it carries the UUID in string format of the parent group to which
        the entry was added."""
        logging.debug("Added new element to safe")

    @GObject.Signal(arg_types=(object,))
    def element_removed(self, element_uuid: UUID) -> None:
        logging.debug("Element %s removed from safe", element_uuid)

    @GObject.Signal(arg_types=(SafeElement, object, object))
    def element_moved(
        self,
        _moved_element: SafeElement,
        _old_location_uuid: UUID,
        _new_location_uuid: UUID,
    ) -> None:
        logging.debug("Element moved safe")

    @property
    def opened(self) -> bool:
        return self._opened

    @property
    def path(self) -> str:
        return self._path
