import pykeepass
from pykeepass import PyKeePass

class Entry:
    #must have
    group_path = ""
    entry_name = ""
    username = ""
    password = ""

    #optional
    url = ""
    notes = ""
    icon = ""

    def __init__(self, group_path, entry_name, username, password, url, notes, icon):
        self.group_path = group_path
        self.entry_name = entry_name
        self.username = username
        self.password = password
        self.url = url
        self.notes = notes
        self.icon = icon

    def change_group_path(self, group_path):
        self.group_path = group_path
        #evtl method from library

    def change_entry_name(self, entry_name):
        self.entry_name = entry_name

    def change_username(self, username):
        self.username = username

    def change_password(self, password):
        self.password = password

    def change_url(self, url):
        self.url = url

    def change_notes(self, notes):
        self.notes = notes

    def change_icon(self, icon):
        self.icon = icon



    def get_group_path(self):
        return self.group_path

    def get_entry_name(self):
        return self.entry_name

    def get_username(self):
        return self.username

    def get_password(self):
        return self.password

    def get_url(self):
        return self.url

    def get_notes(self):
        return self.notes

    def get_icon(self):
        return self.icon