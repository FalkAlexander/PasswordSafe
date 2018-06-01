from pykeepass import PyKeePass
from keepassgtk.logging_manager import LoggingManager


class DatabaseManager:
    logging_manager = LoggingManager(True)
    db = NotImplemented
    database_path = ""
    password_try = ""
    password_check = ""
    password = ""
    changes = False

    def __init__(self, database_path, password=None, keyfile=None):
        self.db = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path

    #
    # Group Transformation Methods
    #

    # Return the parent group object from the child group uuid
    def get_group_parent_group_from_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return group.parentgroup

    # Return the belonging group object for a group uuid
    def get_group_object_from_uuid(self, uuid):
        return self.db.find_groups(uuid=uuid, first=True)

    # Return the belonging group name for a group uuid
    def get_group_name_from_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
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
        return entry.title

    # Return entry name from entry uuid
    def get_entry_name_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.title

    # Return the belonging icon for an entry object
    def get_entry_icon_from_entry_object(self, entry):
        return entry.icon

    # Return entry icon from entry uuid
    def get_entry_icon_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.icon

    # Return the belonging username for an entry object
    def get_entry_username_from_entry_object(self, entry):
        return entry.username

    # Return the belonging username for an entry uuid
    def get_entry_username_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.username

    # Return the belonging password for an entry object
    def get_entry_password_from_entry_object(self, entry):
        return entry.password

    # Return the belonging password for an entry uuid
    def get_entry_password_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.password

    #
    # Database Modifications
    #

    # Add new group to database
    def add_group_to_database(self, name, group_path, icon, parent_group_uuid):
        destination_group = self.get_group_object_from_uuid(parent_group_uuid)
        self.db.add_group(destination_group, name, icon)
        self.changes = True

    # Add new entry to database
    def add_entry_to_database(
            self, name, username, password, url, notes, icon, group_uuid):
        destination_group = self.get_group_object_from_uuid(group_uuid)
        self.db.add_entry(
            destination_group, name, username, password, url=url, notes=notes,
            expiry_time=None, tags=None, icon=icon, force_creation=False)
        self.changes = True

    # Write all changes to database
    def save_database(self):
        self.db.save()
        self.changes = False
        self.logging_manager.log_debug("Saved database")

    # Set database password
    def set_database_password(self, new_password):
        self.db.set_credentials(new_password)

    # Change database password
    def change_database_password(self, old_password, new_password):
        if self.password == old_password:
            self.db.set_credentials(new_password)

    #
    # Entry Modifications
    #

    def set_entry_password(self, uuid, password):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.password = password
        self.changes = True

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

    # Check if object is group
    def check_is_group(self, uuid):
        if self.get_group_object_from_uuid(uuid) is None:
            return False
        else:
            return True


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

    # Get changes
    def made_database_changes(self):
        return self.changes
