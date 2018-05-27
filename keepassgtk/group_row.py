import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from keepassgtk.database import KeepassLoader

class GroupRow(Gtk.ListBoxRow):
    keepass_loader = NotImplemented

    group_uuid = NotImplemented
    label = NotImplemented

    type = "GroupRow"

    def __init__(self, keepass_loader, group):
        Gtk.ListBoxRow.__init__(self)
        self.keepass_loader = keepass_loader

        self.group_uuid = keepass_loader.get_group_uuid_from_group_object(group)
        self.label = keepass_loader.get_group_name_from_group_object(group)

        self.assemble_group_row()


    def assemble_group_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/entries_listbox.ui")
        group_box = builder.get_object("group_box")

        group_name_label = builder.get_object("group_name_label")
        group_name_label.set_text(self.label)

        self.add(group_box)
        self.show_all()


    def get_group_uuid(self):
        return self.group_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def get_type(self):
        return self.type
