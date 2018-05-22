import database 
from database import KeepassLoader
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class EntryRow(Gtk.ListBoxRow):
    keepass_loader = NotImplemented

    entry_uuid = NotImplemented
    label = NotImplemented
    password = NotImplemented

    type = "EntryRow"

    def __init__(self, keepass_loader, entry):
        Gtk.ListBoxRow.__init__(self)
        self.keepass_loader = keepass_loader

        self.entry_uuid = keepass_loader.get_entry_uuid_from_entry_object(entry)
        self.label = keepass_loader.get_entry_name_from_entry_object(entry)
        self.password = keepass_loader.get_entry_password_from_entry_object(entry)

        self.assemble_entry_row()


    def assemble_entry_row(self):
        builder = Gtk.Builder()
        builder.add_from_file("ui/entries_listbox.ui")
        entry_box = builder.get_object("entry_box")

        entry_name_label = builder.get_object("entry_name_label")
        entry_subtitle_label = builder.get_object("entry_subtitle_label")
        entry_password_input = builder.get_object("entry_password_input")

        entry_name_label.set_text(self.label)
        entry_subtitle_label.set_text(self.keepass_loader.get_entry_username_from_entry_uuid(self.entry_uuid))
        entry_password_input.set_text(self.password)

        self.add(entry_box)
        self.show_all()


    def get_entry_uuid(self):
        return self.entry_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def update_password(self):
        self.password = self.keepass_loader.get_entry_password(self.entry_uuid)

    def get_type(self):
        return self.type