import pykeepass
from pykeepass import PyKeePass
import group
from group import Group

class ExtendedGroup(Group):
    name = ""
    group_path = ""
    icon = ""
    notes = ""
    parent_group_uuid = ""
    uuid = ""

    def __init__(self, name, group_path, icon, notes, parent_group_uuid, uuid):
        self.name = name
        self.group_path = group_path
        self.icon = icon
        self.notes = notes
        self.parent_group_uuid = parent_group_uuid
        self.uuid = uuid

    #
    # Setter
    #

    def change_name(self, name):
        self.name = name

    def change_icon(self, icon):
        self.icon = icon

    def change_notes(self, notes):
        self.notes = notes

    def change_group_path(self, group_path, parent_group_uuid):
        self.group_path = group_path
        self.parent_group_uuid = parent_group_uuid

    #
    # Getter
    #

    def get_name(self):
        return self.name

    def get_group_path(self):
        return self.group_path

    def get_icon(self):
        return self.icon

    def get_notes(self):
        return self.notes

    def get_parent_group_uuid(self):
        return self.parent_group_uuid

    def get_uuid(self):
        return self.uuid

    