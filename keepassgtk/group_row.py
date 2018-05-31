from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class GroupRow(Gtk.ListBoxRow):
    group_uuid = NotImplemented
    label = NotImplemented
    type = "GroupRow"

    def __init__(self, dbm, group):
        Gtk.ListBoxRow.__init__(self)
        self.set_name("GroupRow")

        self.group_uuid = dbm.get_group_uuid_from_group_object(group)
        self.label = dbm.get_group_name_from_group_object(group)

        self.assemble_group_row()

    def assemble_group_row(self):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/run/terminal/KeepassGtk/unlocked_database.ui")
        group_box = builder.get_object("group_box")

        group_name_label = builder.get_object("group_name_label")

        if self.label is not None:
            group_name_label.set_text(self.label)
        else:
            group_name_label.set_text("")

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
