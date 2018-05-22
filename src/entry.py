import pykeepass
from pykeepass import PyKeePass
import pykeepass.entry
from pykeepass.entry import Entry

class ExtendedEntry(Entry):
    name = ""
    username = ""
    password = ""
    url = ""
    notes = ""
    icon = ""
    group_uuid = ""
    uuid = ""

    def __init__(self, name, username, password, url, notes, icon, group_uuid, uuid):
        self.name = name
        self.username = username
        self.password = password
        self.url = url
        self.notes = notes
        self.icon = icon
        self.group_uuid = group_uuid
        self.uuid = uuid

    #
    # Setter
    #

    def change_name(self, name):
        self.name = name

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

    def change_group_uuid(self, group_uuid):
        self.group_uuid = group_uuid

    #
    # Getter
    #

    def get_name(self):
        return self.name

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

    def get_group_uuid(self):
        return self.get_group_uuid

    def get_uuid(self):
        return self.uuid
