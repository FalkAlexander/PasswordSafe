from pykeepass import PyKeePass
from keepassgtk.logging_manager import LoggingManager
import keepassgtk.config_manager


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

    # Return the parent group object from the child group object
    def get_group_parent_group_from_object(self, group):
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

    # Return the belonging notes for a group object
    def get_group_notes_from_group_object(self, group):
        return group.notes

     # Return the belonging icon for a group object
    def get_group_icon_from_group_object(self, group):
        return group.icon

    # Return the belonging notes for a group uuid
    def get_group_notes_from_group_uuid(self, uuid):
        group = self.db.find_groups(uuid=uuid, first=True)
        return group.notes

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

    # Return the belonging url for an entry uuid
    def get_entry_url_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.url

    # Return the belonging url for an entry object
    def get_entry_url_from_entry_object(self, entry):
        return entry.url

    # Return the belonging notes for an entry uuid
    def get_entry_notes_from_entry_uuid(self, uuid):
        entry = self.db.find_entries(uuid=uuid, first=True)
        return entry.notes

    # Return the belonging notes for an entry object
    def get_entry_notes_from_entry_object(self, entry):
        return entry.notes

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

        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

        return group

    # Delete a group
    def delete_group_from_database(self, group):
        self.db.delete_group(group)
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()


    # Add new entry to database
    def add_entry_to_database(
            self, name, username, password, url, notes, icon, group_uuid):
        destination_group = self.get_group_object_from_uuid(group_uuid)
        entry = self.db.add_entry(
            destination_group, name, username, password, url=url, notes=notes,
            expiry_time=None, tags=None, icon=icon, force_creation=False)
        self.changes = True

        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

        return entry

    # Delete an entry
    def delete_entry_from_database(self, entry):
        self.db.delete_entry(entry)
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

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

    def set_entry_name(self, uuid, name):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.title = name
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_entry_username(self, uuid, username):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.username = username
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_entry_password(self, uuid, password):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.password = password
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_entry_url(self, uuid, url):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.url = url
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_entry_notes(self, uuid, notes):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.notes = notes
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_entry_icon(self, uuid, icon):
        entry = self.db.find_entries(uuid=uuid, first=True)
        entry.icon = icon
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    #
    # Group Modifications
    #

    def set_group_name(self, uuid, name):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.name = name
        self.changes = True
        if keepassgtk.config_manager.get_save_automatically() is True:
            self.save_database()

    def set_group_notes(self, uuid, notes):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.notes = notes

    def set_group_icon(self, uuid, icon):
        group = self.db.find_groups(uuid=uuid, first=True)
        group.icon = icon

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
        
    # Search for an entry or a group by (part of) name, username, url and notes, returns list of uuid's, search just for name optionally
    def global_search(self, string, just_name):
        uuid_list = []
        for group in self.db.groups:
            if string in group.name:
                uuid_list.append(group.uuid)
            if just_name is False:
                if string in group.notes:
                    uuid_list.append(group.uuid)
        
        for entry in self.db.entries:
            if string in entry.name:
                uuid_list.append(entry.uuid)
            if just_name is False:
                if string in entry.username or string in entry.url or string in entry.notes:
                   uuid_list.append(entry.uuid) 
                
        return uuid_list
    
    # Search one group for a string, search just for name optionally, returns list of uuid's of groups and entries
    def local_search(self, group, string, just_name):
        uuid_list = []
        for group in group.subgroups():
            if string in group.name:
                uuid_list.append(group.uuid)
            if just_name is False:
                if string in group.notes:
                    uuid_list.append(group.uuid)
        
        for entry in group.entries:
            if string in entry.name:
                uuid_list.append(entry.uuid)
            if just_name is False:
                if string in entry.username or string in entry.url or string in entry.notes:
                   uuid_list.append(entry.uuid)
            
        return uuid_list 

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
