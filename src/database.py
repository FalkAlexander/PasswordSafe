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
        #####stopped here##########################

    def print_group():
        print(group.entries)

    def save():
        kp.save()

    def set_database_password(password):
        kp.set_credentials(password)
        save_database()

    def change_database_password(database, old_password, new_password):
        kp = PyKeePass(database, old_password)
        read_database()
        kp.set_credentials(new_password)
        save_database()

    def set_database(path):
        global database_path
        database_path = path

        global kp
        kp = PyKeePass(database_path, password='liufhre86ewoiwejmrcu8owe')

    def get_database():
        return database_path

    def set_password_try(password):
        global password_try
        password_try = password

    def set_password_check(password):
        global password_check
        password_check = password

    def compare_passwords():
        print(password_try)
        print(password_check)
        if password_try == password_check:
            if password_try == "" and password_check == "":
                print("false verkettet")
                return False
            else:
                print("true")
                return True
        else:
            print("false")
            return False

