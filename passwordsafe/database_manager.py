from datetime import datetime
from dateutil import tz
from gettext import gettext as _
import hashlib
import logging
from typing import Optional, Union
from uuid import UUID

from gi.repository import Gio, GLib
from pykeepass.kdbx_parsing.kdbx import KDBX
from pykeepass.entry import Entry
from pykeepass.group import Group
from pykeepass import PyKeePass

from passwordsafe.color_widget import Color


class DatabaseManager():
    """Implements database functionality that is independent of the UI

    Group objects are of type `pykeepass.group.Group`
    Entry objects are of type `pykeepass.entry.Entry`
    Instances of both have useful attributes:
    .uuid: a `uuid.UUID` object
    """
    db = NotImplemented
    database_path = ""
    password_try = ""
    password = ""
    keyfile_hash = NotImplemented
    is_dirty = False  # Does the database need saving?
    save_running = False
    scheduled_saves = 0
    database_file_descriptor = NotImplemented

    def __init__(self, database_path, password=None, keyfile=None):
        self.db = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path
        self.database_file_descriptor = Gio.File.new_for_path(database_path)
        self.password = password

    #
    # Group Transformation Methods
    #

    def get_parent_group(
            self, data: Union[Entry, Group, UUID]) -> Optional[Group]:
        """Get parent group from an entry, a group or an uuid

        :param data: UUID, Entry or Group
        :returns: parent group
        :rtype: Group
        """
        if isinstance(data, UUID):
            if self.check_is_group(data):
                value: Union[Group, Entry] = self.db.find_groups(
                    uuid=data, first=True)
                if not value:
                    logging.warning(
                        "Trying to look up a non-existing UUID %s, this "
                        "should never happen", data)
                    return None
            else:
                value = self.db.find_entries(uuid=data, first=True)
                if not value:
                    logging.warning(
                        "Trying to look up a non-existing UUID %s, this "
                        "should never happen", data)
                    return None
        else:
            value = data

        return value.parentgroup

    def get_group(self, uuid: UUID) -> Optional[Group]:
        """Return the group object for a group uuid

        :returns: a `pykeepass.group.Group` object or None if it does not exist
        """
        assert type(uuid) == UUID, "uuid needs to be of type UUID"
        return self.db.find_groups(uuid=uuid, first=True)

    def get_group_name(self, data: Union[Group, UUID]) -> str:
        """Get group name from a group or an uuid

        :param data: a group or an uuid
        :returns: group name or an empty string if it does not exist
        :rtype: str
        """
        if isinstance(data, UUID):
            group: Group = self.db.find_groups(uuid=data, first=True)
            if not group:
                logging.warning(
                    "Trying to look up a non-existing UUID %s, this should "
                    "never happen", data)
                return ""
        else:
            group = data

        return group.name or ""

    # Return the belonging icon for a group object
    def get_group_icon_from_group_object(self, group):
        return group.icon

    def get_notes(self, data: Union[Entry, Group, UUID]) -> str:
        """Get notes from an entry, a group or an uuid

        :param data: a group or an uuid
        :returns: notes or an empty string if it does not exist
        :rtype: str
        """
        if isinstance(data, UUID):
            if self.check_is_group(data):
                value: Union[Entry, Group] = self.db.find_groups(
                    uuid=data, first=True)
                if not value:
                    logging.warning(
                        "Trying to look up a non-existing UUID %s, this "
                        "should never happen", data)
                    return ""
            else:
                value = self.db.find_entries(uuid=data, first=True)
                if not value:
                    logging.warning(
                        "Trying to look up a non-existing UUID %s, this "
                        "should never happen", data)
                    return ""
        else:
            value = data

        return value.notes or ""

    # Return path for group uuid
    def get_group_path_from_group_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return group.path

    #
    # Entry Transformation Methods
    #

    # Return the belonging entry object for a entry uuid
    def get_entry_object_from_uuid(self, uuid):
        return self.db.find_entries(uuid=uuid, first=True)

    # Return entry uuid from entry object
    def get_entry_uuid_from_entry_object(self, entry):
        return entry.uuid

    def get_entry_name(self, data: Union[Entry, UUID]) -> str:
        """Get entry name from an uuid or an entry

        :param data: UUID or Entry
        :returns: entry name or an empty string if it does not exist
        :rtype: str
        """
        if isinstance(data, UUID):
            entry: Entry = self.db.find_entries(uuid=data, first=True)
            if not entry:
                logging.warning(
                    "Trying to look up a non-existing UUID %s, this should "
                    "never happen", data)
                return ""
        else:
            entry = data

        return entry.title or ""

    # Return the belonging icon for an entry object
    def get_entry_icon_from_entry_object(self, entry):
        return entry.icon

    # Return entry icon from entry uuid
    def get_entry_icon_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.icon

    # Return the belonging username for an entry object
    def get_entry_username_from_entry_object(self, entry):
        if entry.username is None:
            return ""
        else:
            return entry.username

    # Return the belonging username for an entry uuid
    def get_entry_username_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return self.get_entry_username_from_entry_object(entry)

    # Return the belonging password for an entry object
    def get_entry_password_from_entry_object(self, entry):
        if entry.password is None:
            return ""
        else:
            return entry.password

    # Return the belonging password for an entry uuid
    def get_entry_password_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return self.get_entry_password_from_entry_object(entry)

    # Return the belonging url for an entry uuid
    def get_entry_url_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return self.get_entry_url_from_entry_object(entry)

    # Return the belonging url for an entry object
    def get_entry_url_from_entry_object(self, entry):
        if entry.url is None:
            return ""
        else:
            return entry.url

    # Return the belonging color for an entry uuid
    def get_entry_color_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property("color_prop_LcljUMJZ9X") is None:
            return Color.NONE.value
        else:
            return entry.get_custom_property("color_prop_LcljUMJZ9X")

    # Return the belonging value for an attribute
    def get_entry_attribute_value_from_entry_uuid(self, uuid, key):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property(key) is None:
            return ""
        else:
            return entry.get_custom_property(key)

    # Return all attributes for an entry uuid
    def get_entry_attributes_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.custom_properties

    # Return all attributes for an entry object
    def get_entry_attributes_from_entry_object(self, entry):
        return entry.custom_properties

    # Return all attachments for an entry uuid
    def get_entry_attachments_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.attachments

    # Return all attachments for an entry object
    def get_entry_attachments_from_entry_object(self, entry):
        return entry.attachments

    #
    # Entry Checks
    #

    def has_entry_name(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.title is None:
            return False
        return True

    def has_entry_username(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.username is None:
            return False
        return True

    def has_entry_password(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.password is None:
            return False
        return True

    def has_entry_url(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.url is None:
            return False
        return True

    def has_entry_notes(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.notes is None:
            return False
        return True

    def has_entry_icon(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.icon is None:
            return False
        return True

    def has_entry_expiry_date(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.expires

    def has_entry_expired(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.expired is False:
            return False
        return True

    def has_entry_color(self, uuid: UUID) -> bool:
        entry: Entry = self.db.find_entries(uuid=uuid, first=True)
        color_property: Optional[str] = entry.get_custom_property(
            "color_prop_LcljUMJZ9X")
        if (not color_property
                or color_property == Color.NONE.value):
            return False
        return True

    def has_entry_attributes(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if len(entry.custom_properties) == 0:
            return False
        return True

    def has_entry_attribute(self, uuid, key):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property(key) is None:
            return False
        return True

    def has_entry_attachments(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if len(entry.attachments) == 0:
            return False
        return True

    #
    # Group Checks
    #

    def has_group_name(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.name is None:
            return False
        return True

    def has_group_notes(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.notes is None:
            return False
        return True

    def has_group_icon(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.icon is None:
            return False
        return True

    #
    # Database Modifications
    #

    # Add new group to database
    def add_group_to_database(self, name, icon, notes, parent_group):
        group = self.db.add_group(parent_group, name, icon=icon, notes=notes)
        self.is_dirty = True
        self.set_element_mtime(parent_group)

        return group

    # Delete a group
    def delete_group_from_database(self, group):
        self.db.delete_group(group)
        self.is_dirty = True
        if group.parentgroup is not None:
            self.set_element_mtime(group.parentgroup)

    # Add new entry to database
    def add_entry_to_database(
            self, name, username, password, url, notes, icon, group_uuid):
        destination_group = self.get_group(group_uuid)
        entry = self.db.add_entry(
            destination_group, name, username, password, url=url, notes=notes,
            expiry_time=None, tags=None, icon=icon, force_creation=self.check_entry_in_group_exists("", destination_group))
        self.is_dirty = True
        self.set_element_mtime(destination_group)

        return entry

    # Delete an entry
    def delete_entry_from_database(self, entry):
        self.db.delete_entry(entry)
        self.is_dirty = True
        if entry.parentgroup is not None:
            self.set_element_mtime(entry.parentgroup)

    # Duplicate an entry
    def duplicate_entry(self, entry):
        title = entry.title
        if title is None:
            title = ""

        username = entry.username
        if username is None:
            username = ""

        password = entry.password
        if password is None:
            password = ""

        # NOTE: With clone is meant a duplicated object, not the process of cloning/duplication; "the" clone
        clone_entry = self.db.add_entry(entry.parentgroup, title + " - " + _("Clone"), username, password, url=entry.url, notes=entry.notes, expiry_time=entry.expiry_time, tags=entry.tags, icon=entry.icon, force_creation=True)

        # Add custom properties
        for key in entry.custom_properties:
            value = entry.custom_properties[key]
            if value is None:
                value = ""
            clone_entry.set_custom_property(key, value)

        self.is_dirty = True
        if entry.parentgroup is not None:
            self.set_element_mtime(entry.parentgroup)

    # Write all changes to database
    def save_database(self):
        if self.save_running is False and self.is_dirty:
            self.save_running = True

            try:
                self.db.save()
                logging.debug("Saved database")
                self.is_dirty = False
            except Exception:
                logging.error("Error occured while saving database")

            # Workaround
            # Fix created and proposed: https://github.com/pschmitt/pykeepass/pull/102
            self.db.kdbx = KDBX.parse_file(self.db.filename, password=self.db.password, keyfile=self.db.keyfile, transformed_key=None)

            self.save_running = False

    # Set database password
    def set_database_password(self, new_password):
        self.db.password = new_password
        self.is_dirty = True

    # Set database keyfile
    def set_database_keyfile(self, new_keyfile):
        self.db.keyfile = new_keyfile
        self.is_dirty = True

    #
    # Entry Modifications
    #

    def set_entry_name(self, uuid, name):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.title = name
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_username(self, uuid, username):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.username = username
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_password(self, uuid, password):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.password = password
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_url(self, uuid, url):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.url = url
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_notes(self, uuid, notes):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.notes = notes
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_icon(self, uuid, icon):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.icon = icon
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_expiry_date(self, uuid, date):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.expiry_time = date
        # entry.expires
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_color(self, uuid, color):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.set_custom_property("color_prop_LcljUMJZ9X", color)
        self.is_dirty = True
        self.set_element_mtime(entry)

    def set_entry_attribute(self, uuid, key, value):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.set_custom_property(key, value)
        self.is_dirty = True
        self.set_element_mtime(entry)

    def delete_entry_attribute(self, uuid, key):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.delete_custom_property(key)
        self.is_dirty = True
        self.set_element_mtime(entry)

    def add_entry_attachment(self, uuid, byte_buffer, filename):
        entry = self.db.find_entries(uuid=uuid, first=True)
        attachment_id = self.db.add_binary(byte_buffer)
        attachment = entry.add_attachment(attachment_id, filename)
        self.is_dirty = True
        return attachment

    def delete_entry_attachment(self, uuid, attachment):
        entry = self.db.find_entries(uuid=uuid, first=True)
        try:
            self.db.delete_binary(attachment.id)
            entry.delete_attachment(attachment)
        except Exception:
            logging.warning("Skipping attachment handling...")
        self.is_dirty = True

    # Move an entry to another group
    def move_entry(self, uuid, destination_group_object):
        entry = self.db.find_entries(uuid=uuid, first=True)
        self.db.move_entry(entry, destination_group_object)
        if entry.parentgroup is not None:
            self.set_element_mtime(entry.parentgroup)
        self.set_element_mtime(destination_group_object)

    def set_element_ctime(self, element):
        element.ctime = datetime.utcnow()

    def set_element_atime(self, element):
        element.atime = datetime.utcnow()

    def set_element_mtime(self, element):
        element.mtime = datetime.utcnow()

    #
    # Group Modifications
    #

    def set_group_name(self, uuid, name):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.name = name
        self.is_dirty = True
        self.set_element_mtime(group)

    def set_group_notes(self, uuid, notes):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.notes = notes
        self.is_dirty = True
        self.set_element_mtime(group)

    def set_group_icon(self, uuid, icon):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.icon = icon
        self.is_dirty = True
        self.set_element_mtime(group)

    # Move an group
    def move_group(self, uuid, destination_group_object):
        group = self.db.find_groups(uuid=uuid, first=True)
        self.db.move_group(group, destination_group_object)
        if group.parentgroup is not None:
            self.set_element_mtime(group.parentgroup)
        self.set_element_mtime(destination_group_object)

    #
    # Read Database
    #

    def get_groups_in_root(self):
        return self.db.root_group.subgroups

    def get_groups_in_folder(self, uuid):
        """Return list of all subgroups in a group"""
        folder = self.get_group(uuid)
        return folder.subgroups

    def get_entries_in_folder(self, uuid):
        """Return list of all entries in a group"""
        parent_group = self.get_group(uuid)
        return parent_group.entries

    # Return the database filesystem path
    def get_database(self):
        return self.database_path

    # Return the root group of the database instance
    def get_root_group(self):
        return self.db.root_group

    # Check if root group
    def check_is_root_group(self, group):
        return group.is_root_group

    # Check if entry with title in group exists
    def check_entry_in_group_exists(self, title, group):
        entry = self.db.find_entries(title=title, group=group, recursive=False, history=False, first=True)
        if entry is None:
            return False
        return True

    # Search for an entry or a group
    def search(self, string, fulltext, global_search=True, path=None):
        uuid_list = []

        # if fulltext is False:
        #     for group in self.db.find_groups(name="(?i)" + string.replace(" ", ".*"), recursive=global_search, path=path, regex=True):
        #         if group.is_root_group is False:
        #             uuid_list.append(group.uuid)
        # else:
        #     for group in self.db.groups:
        #         if group.is_root_group is False and group.uuid not in uuid_list:
        #             if string.lower() in self.get_notes(group):
        #                 uuid_list.append(group.uuid)

        # if fulltext is False:
        #     for entry in self.db.find_entries(title="(?i)" + string.replace(" ", ".*"), recursive=global_search, path=path, regex=True):
        #         uuid_list.append(entry.uuid)
        # else:
        #     for entry in self.db.entries:
        #         if entry.uuid not in uuid_list:
        #             if string.lower() in self.get_entry_username_from_entry_object(entry):
        #                 uuid_list.append(entry.uuid)
        #             elif string.lower() in self.get_notes(entry):
        #                 uuid_list.append(entry.uuid)

        # Workaround
        if fulltext is False:
            for group in self.db.groups:
                if group.is_root_group is False and group.uuid not in uuid_list:
                    if group.name is not None:
                        if string.lower() in group.name.lower():
                            if global_search is True:
                                uuid_list.append(group.uuid)
                            else:
                                if group.path[:-1].rsplit("/", 1)[0] == path.replace("//", ""):
                                    uuid_list.append(group.uuid)
        else:
            for group in self.db.groups:
                if group.is_root_group is False and group.uuid not in uuid_list:
                    if string.lower() in self.get_notes(group).lower():
                        if global_search is True:
                            uuid_list.append(group.uuid)
                        else:
                            if group.path[:-1].rsplit("/", 1)[0] == path.replace("//", ""):
                                uuid_list.append(group.uuid)

        if fulltext is False:
            for entry in self.db.entries:
                if entry.uuid not in uuid_list:
                    if entry.title is not None:
                        if string.lower() in entry.title.lower():
                            if global_search is True:
                                uuid_list.append(entry.uuid)
                            else:
                                if entry.path.rsplit("/", 1)[0] == path.replace("//", ""):
                                    uuid_list.append(entry.uuid)
        else:
            for entry in self.db.entries:
                if entry.uuid not in uuid_list:
                    if string.lower() in self.get_entry_username_from_entry_object(entry).lower():
                        if global_search is True:
                            uuid_list.append(entry.uuid)
                        else:
                            if entry.path.rsplit("/", 1)[0] == path.replace("//", ""):
                                uuid_list.append(entry.uuid)
                    elif string.lower() in self.get_notes(entry).lower():
                        if global_search is True:
                            uuid_list.append(entry.uuid)
                        else:
                            if entry.path.rsplit("/", 1)[0] == path.replace("//", ""):
                                uuid_list.append(entry.uuid)
                    elif string.lower() in self.get_entry_url_from_entry_object(entry).lower():
                        if global_search is True:
                            uuid_list.append(entry.uuid)
                        else:
                            if entry.path.rsplit("/", 1)[0] == path.replace("//", ""):
                                uuid_list.append(entry.uuid)

        return uuid_list

    def check_is_group(self, uuid):
        """Whether uuid is a group uuid"""
        return self.get_group(uuid) is not None

    def check_is_group_object(self, group):
        return hasattr(group, "name")

    def get_attachment_from_id(self, attachment_id):
        return self.db.find_attachments(id=attachment_id, first=True)

    #
    # Properties
    #

    def get_element_creation_date(self, element):
        if element.ctime is not None:
            local_timestamp = element.ctime.astimezone(tz.tzlocal())
            timestamp = GLib.DateTime.new_local(
                int(datetime.strftime(local_timestamp, "%Y")),
                int(datetime.strftime(local_timestamp, "%m")),
                int(datetime.strftime(local_timestamp, "%d")),
                int(datetime.strftime(local_timestamp, "%H")),
                int(datetime.strftime(local_timestamp, "%M")),
                float(datetime.strftime(local_timestamp, "%S")))
            return timestamp.format("%c")
        else:
            return "-"

    def get_element_acessed_date(self, element):
        if element.atime is not None:
            local_timestamp = element.atime.astimezone(tz.tzlocal())
            timestamp = GLib.DateTime.new_local(
                int(datetime.strftime(local_timestamp, "%Y")),
                int(datetime.strftime(local_timestamp, "%m")),
                int(datetime.strftime(local_timestamp, "%d")),
                int(datetime.strftime(local_timestamp, "%H")),
                int(datetime.strftime(local_timestamp, "%M")),
                float(datetime.strftime(local_timestamp, "%S")))
            return timestamp.format("%c")
        else:
            return "-"

    def get_element_modified_date(self, element):
        if element.mtime is not None:
            local_timestamp = element.mtime.astimezone(tz.tzlocal())
            timestamp = GLib.DateTime.new_local(
                int(datetime.strftime(local_timestamp, "%Y")),
                int(datetime.strftime(local_timestamp, "%m")),
                int(datetime.strftime(local_timestamp, "%d")),
                int(datetime.strftime(local_timestamp, "%H")),
                int(datetime.strftime(local_timestamp, "%M")),
                float(datetime.strftime(local_timestamp, "%S")))
            return timestamp.format("%c")
        else:
            return "-"
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

    def create_keyfile_hash(self, keyfile_path):
        """Create keyfile hash and returns it"""
        hasher = hashlib.sha512()
        with open(keyfile_path, 'rb') as file:
            buffer = 0
            while buffer != b'':
                buffer = file.read(1024)
                hasher.update(buffer)
        return hasher.hexdigest()

    # Set keyfile hash
    def set_keyfile_hash(self, keyfile_path):
        self.keyfile_hash = self.create_keyfile_hash(keyfile_path)

    def parent_checker(self, current_group, moved_group):
        if current_group.is_root_group:
            return False
        elif current_group.uuid == moved_group.uuid:
            return True
        else:
            return self.parent_checker(current_group.parentgroup, moved_group)

    @property
    def encryption(self):
        """returns the encryption algorithm"""
        return self.db.encryption_algorithm

    @property
    def version(self):
        """returns the database version"""
        return self.db.version
