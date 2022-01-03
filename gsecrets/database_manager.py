# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import threading
import logging
from uuid import UUID

from gi.repository import Gio, GLib, GObject
from pykeepass import PyKeePass

from gsecrets.safe_element import SafeElement


class DatabaseManager(GObject.GObject):
    # pylint: disable=too-many-public-methods

    """Implements database functionality that is independent of the UI

    Useful attributes:
     .database_path: str containing the filepath of the database
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

    locked = GObject.Property(type=bool, default=False)
    is_dirty = GObject.Property(type=bool, default=False)

    def __init__(
        self,
        database_path: str,
        password: str | None = None,
        keyfile: str | None = None,
        keyfile_hash: str | None = None,
    ) -> None:
        super().__init__()

        # password remains accessible as self.db.password
        self.db = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path
        self.keyfile_hash = keyfile_hash

    #
    # Database Modifications
    #

    # Write all changes to database
    def save_database(self, notification=False):
        if not self.save_running and self.is_dirty:
            self.save_running = True

            # TODO This could be simplified a lot
            # if a copy of the keyfile was stored in memory.
            # This would require careful checks for functionality that
            # modifies the keyfile.
            if self.db.keyfile:
                gfile = Gio.File.new_for_path(self.db.keyfile)
                exists = gfile.query_exists()
                if not exists:
                    self.save_running = False
                    logging.error("Could not find keyfile")
                    if notification:
                        self.emit("save-notification", False)

                    return

            save_thread = threading.Thread(
                target=self.save_thread, args=[notification]
            )
            save_thread.daemon = False
            save_thread.start()

    def save_thread(self, notification: bool) -> None:
        succeeded = False
        try:
            self.db.save()
            succeeded = True
        except Exception as err:  # pylint: disable=broad-except
            logging.error("Error occurred while saving database: %s", err)
        finally:
            GLib.idle_add(self.save_thread_finished, succeeded, notification)

    def save_thread_finished(self, succeeded: bool, notification: bool) -> None:
        self.save_running = False

        if notification:
            self.emit("save-notification", succeeded)

        if succeeded:
            logging.debug("Saved database")
            self.is_dirty = False

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
