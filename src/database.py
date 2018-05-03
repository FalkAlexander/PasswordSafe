import pykeepass
from pykeepass import PyKeePass
import group.py
from group.py import Group
import entry.py
from entry.py import Entry

class KeepassLoader:

    kp = 0
    database_path = ""
    password_try = ""
    password_check = ""
    password = ""
    group_list = []

    def read_database(self):
        self.kp = PyKeePass(database_path, password='liufhre86ewoiwejmrcu8owe')

    def add_group(self):
        group = Group(name, icon, note, root_group)
        self.kp.add_group(group.get_root_group(), group.get_name())
        self.group_list.append(group)

    def add_entry():
        entry = Entry(group_path,entry_name,username,password,url,note,icon)
        self.kp.add_entry(self.kp.find_groups_by_path(entry.get_group_path)), entry.get_entry_name(), entry.get_username(), entry.get_password(), url=entry.get_url(), note=entry.get_note(), icon=entry.get_icon())

    def get_entries(self, group_path):
        group = self.kp.find_groups_by_path(group_path)
        entry_list = []
        for entry in group.entries:
            entry_list.append(entry)

        return entry_list


    def save(self):
        self.kp.save()

    def set_database_password(self, password):
        self.kp.set_credentials(password)
        self.password = password
        save()

    def change_database_password(self, old_password, new_password):
        kp = PyKeePass(database, old_password)
        read_database() #this is still with the initial password
        kp.set_credentials(new_password)
        save()

    def set_database(self, path):
        self.database_path = path

        self.kp = PyKeePass(self.database_path, password='liufhre86ewoiwejmrcu8owe') #this applies also just for initial configuration

    def get_database(self):
        return self.database_path

    def set_password_try(self, password):
        self.password_try = password

    def set_password_check(self, password):
        self.password_check = password

    def compare_passwords():
        print(self.password_try)
        print(self.password_check)
        if self.password_try == self.password_check:
            if self.password_try == "" and self.password_check == "":
                print("empty password")
                return False
            else:
                print("true")
                return True
        else:
            print("false")
            return False

