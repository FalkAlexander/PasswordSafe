import pykeepass
from pykeepass import PyKeePass
import group
from group import Group
import entry
from entry import Entry

class KeepassLoader:

    kp = 0
    database_path = ""
    password_try = ""
    password_check = ""
    password = "" # liufhre86ewoiwejmrcu8owe
    group_list = []

    def __init__(self, database_path, password):
        self.kp = PyKeePass(self.database_path, password)

    def add_group(self, name, icon, note, root_group):
        group = Group(name, icon, note, root_group)
        self.kp.add_group(group.get_root_group(), group.get_name())
        self.group_list.append(group)

    def add_entry(self, group_path, entry_name, username, password, url, notes, icon):
        entry = Entry(group_path, entry_name, username, password, url, notes, icon)
        self.kp.add_entry(self.kp.find_groups_by_path(entry.get_group_path()), entry.get_entry_name(), entry.get_username(), entry.get_password(), url=entry.get_url(), notes=entry.get_notes(), icon=entry.get_icon())

    def get_entries(self, group_path):
        group = self.kp.find_groups_by_path(group_path)
        entry_list = []
        for entry in group.entries:
            entry_list.append(entry)

        return entry_list


    def save(self):
        self.kp.save()

    def change_database_password(self, old_password, new_password):
        if old_password == self.password:
            self.kp.set_credentials(new_password)
            self.save()
        else:
            print("DEBUG: Password cannot be changed, no matching passwords")

    def get_database(self):
        return self.database_path

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

