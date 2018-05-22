import pykeepass
from pykeepass import PyKeePass
import group
from group import ExtendedGroup
import entry
from entry import ExtendedEntry
import logging_manager
from logging_manager import LoggingManager

class KeepassLoader:

    kp = NotImplemented
    database_path = ""
    password_try = ""
    password_check = ""
    password = ""

    def __init__(self, database_path, password=None, keyfile=None):
        self.kp = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path


    #
    # Group Transformation Methods
    #

    # Return the parent group object from the child group uuid

    def get_parent_group_from_uuid(self, uuid):
        group = self.kp.find_groups(uuid=uuid, first=True)
        return group.parentgroup

    # Return the belonging group object for a group uuid

    def get_group_object_from_uuid(self, uuid):
        return self.kp.find_groups(uuid=uuid, first=True)

    # Return the belonging group name for a group uuid

    def get_group_name_from_uuid(self, uuid):
        group = self.kp.find_groups(uuid=uuid, first=True)
        return group.name

    # Return the path for a group object

    def get_group_path_from_group_object(self, group):
        return group.path

    # Return the belonging group uuid for a group object

    def get_group_uuid_from_group_object(self, group):
        return group.uuid

    # Return the belonging name for a group object

    def get_group_name_from_group_object(self, group):
        return group.name

    # Return path for group uuid

    def get_group_path_from_group_uuid(self, uuid):
        group = self.kp.find_groups(uuid=uuid, first=True)
        return group.path

    #
    # Entry Transformation Methods
    #

    # Return the belonging name for an entry object

    def get_entry_name_from_entry_object(self, entry):
        return entry.name

    # Return entry name from entry uuid

    def get_entry_name_from_entry_uuid(self, uuid):
        entry = self.kp.find_entries(uuid=uuid, first=True)
        return entry.name

    # Return the belonging username for an entry object

    def get_entry_username_from_entry_object(self, entry):
        return entry.username

    # Return the belonging password for an entry object

    def get_entry_password_from_entry_object(self, entry):
        return entry.password

    #
    # Database Modifications
    #

    # Add new group to database

    def add_group_to_database(self, name, group_path, icon, parent_group_uuid):
        destination_group = self.get_group_object_from_uuid(parent_group_uuid)
        self.kp.add_group(destination_group, name, icon)

    # Add new entry to database

    def add_entry_to_database(self, name, username, password, url, notes, icon, group_uuid):
        destination_group = self.get_group_object_from_uuid(group_uuid)
        self.kp.add_entry(destination_group, name, username, password, url=url, notes=notes, expiry_time=None, tags=None, icon=icon, force_creation=False)

    # Write all changes to database

    def save_database(self):
        self.kp.save()

    # Set database password

    def set_database_password(self, new_password):
        self.kp.set_credentials(new_password)

    # Change database password

    def change_database_password(self, old_password, new_password):
        if self.password == old_password:
            self.kp.set_credentials(new_password)

    
    #
    # Read Database
    #

    def get_groups_in_root(self):
        return self.kp.find_groups(path="/")

    # Return list of all groups in folder

    def get_groups_in_folder(self, uuid):
        group_list = []
        parent_group = self.get_group_object_from_uuid(uuid)
        groups_in_database = self.kp.groups
        for group in groups_in_database:
            if group.parentgroup == parent_group:
                group_list.append(group)
        return group_list

    # Return list of all entries in folder

    def get_entries_in_folder(self, uuid):
        parent_group = self.get_group_object_from_uuid(uuid)
        return parent_group.entries

    # Return the database filesystem path

    def get_database(self):
        print(self.database_path)
        return self.database_path

    # Return the root group of the database instance

    def get_root_group(self):
        return self.kp.root_group

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
