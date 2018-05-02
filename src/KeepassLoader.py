import pykeepass
from pykeepass import PyKeePass

kp = 0
group = 0
database_path = ""
password_try = ""
password_check = ""
password = ""

def read_database():
    global kp
    kp = PyKeePass(database_path, password='liufhre86ewoiwejmrcu8owe')

def add_group():
    global group
    group = kp.add_group(kp.root_group, 'total_wichtig')

def add_entry():
    kp.add_entry(group, 'bsp', 'bsp', 'bsp')

def print_group():
    print(group.entries)

def save_group():
    kp.save()

def set_database_password(password):
    kp.set_credentials(password)
    save_database()

def change_database_password(database, old_password, new_password):
    kp = PyKeePass(database, old_password)
    read_database()
    kp.set_credentials(new_password)
    save_database()

def save_database():
    kp.save()

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
    if password_try == password_check:
        if password_try == "" and password_check == "":
            return False
        else:
            return True
    else:
        return False
