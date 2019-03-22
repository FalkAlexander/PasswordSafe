from datetime import datetime
from dateutil import tz
from gettext import gettext as _
from gi.repository import Gio, GLib
from pykeepass.kdbx_parsing.kdbx import KDBX
from pykeepass import PyKeePass
import hashlib


class DatabaseManager:
    logging_manager = NotImplemented
    db = NotImplemented
    database_path = ""
    password_try = ""
    password_check = ""
    password = ""
    keyfile_hash = NotImplemented
    changes = False
    save_running = False
    scheduled_saves = 0
    database_file_descriptor = NotImplemented

    def __init__(self, database_path, password=None, keyfile=None, logging_manager=None):
        self.logging_manager = logging_manager
        self.db = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path
        self.database_file_descriptor = Gio.File.new_for_path(database_path)
        self.password = password

    #
    # Group Transformation Methods
    #

    # Return the parent group object from the child group uuid
    def get_group_parent_group_from_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return group.parentgroup

    # Return the parent group object from the child group object
    def get_group_parent_group_from_object(self, group):
        return group.parentgroup

    # Return the belonging group object for a group uuid
    def get_group_object_from_uuid(self, uuid):
        return self.db.find_groups(uuid=uuid, first=True)

    # Return the belonging group name for a group uuid
    def get_group_name_from_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return self.get_group_name_from_group_object(group)

    # Return the path for a group object
    def get_group_path_from_group_object(self, group):
        return group.path

    # Return the belonging group uuid for a group object
    def get_group_uuid_from_group_object(self, group):
        return group.uuid

    # Return the belonging name for a group object
    def get_group_name_from_group_object(self, group):
        if group.name is None:
            return ""
        else:
            return group.name

    # Return the belonging notes for a group object
    def get_group_notes_from_group_object(self, group):
        if group.notes is None:
            return ""
        else:
            return group.notes

    # Return the belonging icon for a group object
    def get_group_icon_from_group_object(self, group):
        return group.icon

    # Return the belonging notes for a group uuid
    def get_group_notes_from_group_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return self.get_group_notes_from_group_object(group)

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

    # Return parent group from entry uuid
    def get_entry_parent_group_from_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.parentgroup

    # Return parent group from entry object
    def get_entry_parent_group_from_entry_object(self, entry):
        return entry.parentgroup

    # Return the belonging name for an entry object
    def get_entry_name_from_entry_object(self, entry):
        if entry.title is None:
            return ""
        else:
            return entry.title

    # Return entry name from entry uuid
    def get_entry_name_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return self.get_entry_name_from_entry_object(entry)

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

    # Return the belonging notes for an entry uuid
    def get_entry_notes_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.notes

    # Return the belonging notes for an entry object
    def get_entry_notes_from_entry_object(self, entry):
        if entry.notes is None:
            return ""
        else:
            return entry.notes

    # Return the beloging expiry date for an entry uuid
    def get_entry_expiry_date_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.expiry_time

    # Return the beloging expiry date for an entry object
    def get_entry_expiry_date_from_entry_object(self, entry):
        return entry.expiry_time

    # Return the belonging color for an entry uuid
    def get_entry_color_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property("color_prop_LcljUMJZ9X") is None:
            return "NoneColorButton"
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
        else:
            return True

    def has_entry_username(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.username is None:
            return False
        else:
            return True

    def has_entry_password(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.password is None:
            return False
        else:
            return True

    def has_entry_url(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.url is None:
            return False
        else:
            return True

    def has_entry_notes(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.notes is None:
            return False
        else:
            return True

    def has_entry_icon(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.icon is None:
            return False
        else:
            return True

    def has_entry_expiry_date(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.expires

    def has_entry_expired(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.expired is False:
            return False
        else:
            return True

    def has_entry_color(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property("color_prop_LcljUMJZ9X") is None or entry.get_custom_property("color_prop_LcljUMJZ9X") == "NoneColorButton":
            return False
        else:
            return True

    def has_entry_attributes(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if len(entry.custom_properties) == 0:
            return False
        else:
            return True

    def has_entry_attribute(self, uuid, key):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if entry.get_custom_property(key) is None:
            return False
        else:
            return True

    def has_entry_attachments(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        if len(entry.attachments) == 0:
            return False
        else:
            return True

    #
    # Group Checks
    #

    def has_group_name(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.name is None:
            return False
        else:
            return True

    def has_group_notes(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.notes is None:
            return False
        else:
            return True

    def has_group_icon(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        if group.icon is None:
            return False
        else:
            return True

    #
    # Database Modifications
    #

    # Add new group to database
    def add_group_to_database(self, name, icon, notes, parent_group):
        group = self.db.add_group(parent_group, name, icon=icon, notes=notes)
        self.changes = True
        self.set_element_mtime(parent_group)

        return group

    # Delete a group
    def delete_group_from_database(self, group):
        self.db.delete_group(group)
        self.changes = True
        if group.parentgroup is not None:
            self.set_element_mtime(group.parentgroup)

    # Add new entry to database
    def add_entry_to_database(
            self, name, username, password, url, notes, icon, group_uuid):
        destination_group = self.get_group_object_from_uuid(group_uuid)
        entry = self.db.add_entry(
            destination_group, name, username, password, url=url, notes=notes,
            expiry_time=None, tags=None, icon=icon, force_creation=self.check_entry_in_group_exists("", destination_group))
        self.changes = True
        self.set_element_mtime(destination_group)

        return entry

    # Delete an entry
    def delete_entry_from_database(self, entry):
        self.db.delete_entry(entry)
        self.changes = True
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

        self.changes = True
        if entry.parentgroup is not None:
            self.set_element_mtime(entry.parentgroup)

    # Write all changes to database
    def save_database(self):
        if self.save_running is False and self.changes is True:
            self.save_running = True

            try:
                self.db.save()
                self.logging_manager.debug("Saved database")
                self.changes = False
            except Exception:
                self.logging_manager.error("Error occured while saving database")

            # Workaround
            # Fix created and proposed: https://github.com/pschmitt/pykeepass/pull/102
            self.db.kdbx = KDBX.parse_file(self.db.filename, password=self.db.password, keyfile=self.db.keyfile, transformed_key=None)

            self.save_running = False

    # Set database password
    def set_database_password(self, new_password):
        self.db.password = new_password
        self.changes = True

    # Set database keyfile
    def set_database_keyfile(self, new_keyfile):
        self.db.keyfile = new_keyfile
        self.changes = True

    #
    # Entry Modifications
    #

    def set_entry_name(self, uuid, name):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.title = name
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_username(self, uuid, username):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.username = username
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_password(self, uuid, password):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.password = password
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_url(self, uuid, url):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.url = url
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_notes(self, uuid, notes):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.notes = notes
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_icon(self, uuid, icon):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.icon = icon
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_expiry_date(self, uuid, date):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.expiry_time = date
        entry.expires
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_color(self, uuid, color):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.set_custom_property("color_prop_LcljUMJZ9X", color)
        self.changes = True
        self.set_element_mtime(entry)

    def set_entry_attribute(self, uuid, key, value):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.set_custom_property(key, value)
        self.changes = True
        self.set_element_mtime(entry)

    def delete_entry_attribute(self, uuid, key):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.delete_custom_property(key)
        self.changes = True
        self.set_element_mtime(entry)

    def add_entry_attachment(self, uuid, bytes, filename):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.add_attachment(self.db.add_binary(bytes), filename)
        self.changes = True

    def delete_entry_attachment(self, id):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.delete_binary(id)
        self.changes = True

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
        self.changes = True
        self.set_element_mtime(group)

    def set_group_notes(self, uuid, notes):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.notes = notes
        self.set_element_mtime(group)

    def set_group_icon(self, uuid, icon):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.icon = icon
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

    # Return list of all groups in folder
    def get_groups_in_folder(self, uuid):
        folder = self.get_group_object_from_uuid(uuid)
        return folder.subgroups

    # Return list of all entries in folder
    def get_entries_in_folder(self, uuid):
        parent_group = self.get_group_object_from_uuid(uuid)
        return parent_group.entries

    # Return the database filesystem path
    def get_database(self):
        return self.database_path

    # Return the root group of the database instance
    def get_root_group(self):
        return self.db.root_group

    # Check if root group
    def check_is_root_group(self, group):
        if group.is_root_group:
            return True
        else:
            return False

    # Check if entry with title in group exists
    def check_entry_in_group_exists(self, title, group):
        entry = self.db.find_entries(title=title, group=group, recursive=False, history=False, first=True)
        if entry is None:
            return False
        else:
            return True

    # Search for an entry or a group
    def search(self, string, fulltext, global_search=True, path=None):
        uuid_list = []

        if fulltext is False:
            for group in self.db.find_groups(name="(?i)" + string.replace(" ", ".*"), recursive=global_search, path=path, regex=True):
                if group.is_root_group is False:
                    uuid_list.append(group.uuid)
        else:
            for group in self.db.groups:
                if group.is_root_group is False and group.uuid not in uuid_list:
                    if string.lower() in self.get_group_notes_from_group_object(group):
                        uuid_list.append(group.uuid)

        if fulltext is False:
            for entry in self.db.find_entries(title="(?i)" + string.replace(" ", ".*"), recursive=global_search, path=path, regex=True):
                uuid_list.append(entry.uuid)
        else:
            for entry in self.db.entries:
                if entry.uuid not in uuid_list:
                    if string.lower() in self.get_entry_username_from_entry_object(entry):
                        uuid_list.append(entry.uuid)
                    elif string.lower() in self.get_entry_notes_from_entry_object(entry):
                        uuid_list.append(entry.uuid)

        return uuid_list

    # Check if object is group
    def check_is_group(self, uuid):
        if self.get_group_object_from_uuid(uuid) is None:
            return False
        else:
            return True

    def check_is_group_object(self, group):
        return hasattr(group, "name")

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

    # Set the second password entered by the user (for comparing reasons)
    def set_password_check(self, password):
        self.password_check = password

    # Compare the first password entered by the user with the second one
    def compare_passwords(self):
        if self.password_try == self.password_check:
            if self.password_try == "" and self.password_check == "":
                return False
            else:
                return True
        else:
            return False

    # Create keyfile hash
    def create_keyfile_hash(self, keyfile_path):
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

    # Get changes
    def made_database_changes(self):
        return self.changes

    def parent_checker(self, current_group, moved_group):
        if current_group.is_root_group:
            return False
        elif current_group.uuid == moved_group.uuid:
            return True
        else:
            return self.parent_checker(current_group.parentgroup, moved_group)

    def get_database_encryption(self):
        return self.db.encryption_algorithm

    def get_database_derivation(self):
        return self.db.version

