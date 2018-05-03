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
    note = ""
    icon = ""

    def __init__(self,group_path,entry_name,username,password,url,note,icon):
        self.group_path = group_path
        self.entry_name = entry_name
        self.username = username
        self.password = password
        self.url = url
        self.note = note
        self.icon = icon

    def change_group_path(self, group_path):
        self.group_path = path
        #evtl method from library

    def change_entry_name(self, entry_name):
        self.entry_name = entry_name

    def change_username(self, username):
        self.username = username

    def change_password(self, password):
        self.password = password

    def change_url(self, url):
        self.url = url

    def change_note(self, note):
        self.note = note

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

    def get_note(self):
        return self.note

    def get_icon(self):
        return self.icon