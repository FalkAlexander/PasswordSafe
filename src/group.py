import pykeepass
from pykeepass import PyKeePass

class Group:
    name = ""
    icon = ""
    notes = ""
    uuid = ""
    root_group = ""

    def __init__(self, name, icon, notes, root_group):
        self.name = name
        self.icon = icon
        self.notes = notes

    def change_name(self, name):
        self.name = name

    def change_icon(self, icon):
        self.icon = icon

    def change_notes(self, notes):
        self.note = note

    #def change_root_group(self, path):
        #todo

    def get_name(self):
        return self.name

    def get_icon(self):
        return self.icon

    def get_notes(self):
        return self.notes

    #def get_uuid(self):
        #build in method from library --> it's the path in form /root_group/sub_group/subsub_group

    def get_root_group(self):
        return self.root_group 