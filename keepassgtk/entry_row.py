from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class EntryRow(Gtk.ListBoxRow):
    database_manager = NotImplemented
    entry_uuid = NotImplemented
    label = NotImplemented
    password = NotImplemented
    type = "EntryRow"

    def __init__(self, dbm, entry):
        Gtk.ListBoxRow.__init__(self)
        self.database_manager = dbm

        self.entry_uuid = dbm.get_entry_uuid_from_entry_object(entry)
        self.label = dbm.get_entry_name_from_entry_object(entry)
        self.password = dbm.get_entry_password_from_entry_object(entry)

        self.assemble_entry_row()

    def assemble_entry_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/run/terminal/KeepassGtk/unlocked_database.ui")
        entry_box = builder.get_object("entry_box")

        entry_name_label = builder.get_object("entry_name_label")
        entry_subtitle_label = builder.get_object("entry_subtitle_label")
        entry_password_input = builder.get_object("entry_password_input")

        # Title/Name
        if self.label is not None:
            entry_name_label.set_text(self.label)
        else:
            entry_name_label.set_text("")

        # Subtitle
        subtitle = self.database_manager.get_entry_username_from_entry_uuid(self.entry_uuid)
        if subtitle is not None:
            entry_subtitle_label.set_text(
                self.database_manager.get_entry_username_from_entry_uuid(
                    self.entry_uuid))
        else:
            entry_subtitle_label.set_text("")

        # Password
        if self.password is not None:
            entry_password_input.set_text(self.password)
        else:
            entry_password_input.set_text("")

        self.add(entry_box)
        self.show_all()

    def get_entry_uuid(self):
        return self.entry_uuid

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def update_password(self):
        self.password = self.database_manager.get_entry_password(
            self.entry_uuid)

    def get_type(self):
        return self.type
