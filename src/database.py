import pykeepass
from pykeepass import PyKeePass
import group
from group import Group
import entry
from entry import Entry

class KeepassLoader:

    kp = NotImplemented
    database_path = ""
    password_try = ""
    password_check = ""
    password = "" # liufhre86ewoiwejmrcu8owe
    group_list = []

    def __init__(self, database_path, password):
        self.kp = PyKeePass(database_path, password)
        self.database_path = database_path

    def add_group(self, name, icon, note, parent_group):
        group = Group(name, icon, note, parent_group)
        self.kp.add_group(group.get_parent_group(), group.get_name())
        self.group_list.append(group)


    def add_entry(self, group_path, entry_name, username, password, url, notes, icon):
        entry = Entry(group_path, entry_name, username, password, url, notes, icon)
        self.kp.add_entry(self.kp.find_groups_by_path(entry.get_group_path()), entry.get_entry_name(), entry.get_username(), entry.get_password(), url=entry.get_url(), notes=entry.get_notes(), icon=entry.get_icon())


    def get_entries(self, group_path):
        group = self.kp.find_groups_by_path(group_path, first=True)
        #group = self.kp.find_groups(name="Untergruppe", first=True)
        print(group)
        print(group.entries)
        entry_list = []
        for entry in group.entries:
            entry_list.append(Entry(group, entry.title, entry.username, entry.password, entry.url, entry.notes, entry.icon))
        return entry_list


    def get_groups(self):
        group_list = []
        groups = self.kp.groups
        for group in groups:
            if group.path != "/":
                group_list.append(Group(group.name, group.path, icon=group.icon, notes="", parent_group=group.parent_group))
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


    def get_database(self):
        print(self.database_path)
        return self.database_path

    def get_root_group(self):
        return self.kp.root_group

    def set_password_try(self, password):
        self.password_try = password


    def set_password_check(self, password):
        self.password_check = password


    def compare_passwords(self):
        print("DEBUG: " + self.password_try + " (try)")
        print("DEBUG: " + self.password_check + " (check)")
        if self.password_try == self.password_check:
            if self.password_try == "" and self.password_check == "":
                print("DEBUG: Empty password")
                return False
            else:
                print("DEBUG: Passwords matching (success)")
                return True
        else:
            print("DEBUG: Passwords do not match")
            return False

