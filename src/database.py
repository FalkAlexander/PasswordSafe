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
    group_list = []
    group_counter = 0
    entry_counter = 0

    def __init__(self, database_path, password=None, keyfile=None):
        self.kp = PyKeePass(database_path, password, keyfile)
        self.database_path = database_path


    # Return group object from uuid

    def get_group_from_uuid(self, uuid):
        for group in self.group_list:
            if group.get_parent_group_uuid() == uuid:
                return group


    # Add new group/directory to list (from GUI)

    def add_group(self, name, group_path, icon, notes, parent_group_uuid):
        group = ExtendedGroup(name, group_path, icon, notes, parent_group_uuid, self.group_counter)
        self.kp.add_group(self.get_group_from_uuid(group.get_parent_group_uuid()), group.get_name())
        self.group_counter+=1
        self.group_list.append(group)


    # Add new entry to list (from GUI)

    def add_entry(self, name, username, password, url, notes, icon, group_uuid):
        entry = ExtendedEntry(name, username, password, url, notes, icon, group_uuid, self.entry_counter)
        self.kp.add_entry(self.get_group_from_uuid(entry.get_group_uuid()), entry.get_name(), entry.get_username(), entry.get_password(), url=entry.get_url(), notes=entry.get_notes(), icon=entry.get_icon())
        self.entry_counter+=1


    # Fill our list with the database entries

    def get_entries(self, uuid):
        group = self.get_group_from_uuid(uuid)
        entry_list = []
        if group is not None:
            for entry in group.entries:
                entry_list.append(ExtendedEntry(entry.name, entry.username, entry.password, entry.url, entry.notes, entry.icon, group.uuid, self.entry_counter))
                self.entry_counter+=1
            return entry_list


    def get_groups(self):
        group_list = []
        self.logging_manager = LoggingManager(True)
        groups = self.kp.groups
        for group in groups:
            if group.path != "/":
                self.logging_manager.log_debug("parent group path of " + group.name + " is: " + group.parentgroup.path)
                group_list.append(ExtendedGroup(group.name, group.path, group.icon, group.notes, #parent_group_uuid, self.group_counter))
                self.group_counter+=1
        return group_list



    #we wanted to turn off the automatic saving after each action and connect it instead to a button 
    def save(self):
        self.kp.save()


    #this method sets the initial password for the newly created database
    def set_database_password(self, new_password): 
        self.kp.set_credentials(new_password)
        self.save()


    #this method changes the password of existing database (therefore the old password must be typed in to prevent others changing your password)
    def change_database_password(self, old_password, new_password):
        if self.password == old_password:
            self.kp.set_credentials(new_password)
            self.save()

    #
    # Return the database filesystem path
    #

    def get_database(self):
        print(self.database_path)
        return self.database_path

    #
    # Return the root group of the database instance
    #

    def get_root_group(self):
        return self.kp.root_group

    #
    # Set the first password entered by the user (for comparing reasons)
    #

    def set_password_try(self, password):
        self.password_try = password

    #
    # Set the second password entered by the user (for comparing reasons)
    #

    def set_password_check(self, password):
        self.password_check = password

    #
    # Compare the first password entered by the user with the second one
    #

    def compare_passwords(self):
        if self.password_try == self.password_check:
            if self.password_try == "" and self.password_check == "":
                return False
            else:
                return True
        else:
            return False
