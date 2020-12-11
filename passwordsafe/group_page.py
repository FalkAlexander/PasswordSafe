# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk
from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/group_page.ui")
class GroupPage(Gtk.ScrolledWindow):

    __gtype_name__ = "GroupPage"

    #
    # Global Variables
    #

    unlocked_database = NotImplemented

    #
    # Init
    #
    name_property_value_entry = Gtk.Template.Child()
    notes_property_value_entry = Gtk.Template.Child()

    edit_page = True
    is_dirty = False

    def __init__(self, u_d):
        super().__init__()

        self.unlocked_database = u_d
        self.insert_group_properties_into_listbox()

    #
    # Create Property Rows
    #

    def insert_group_properties_into_listbox(self):
        group = self.unlocked_database.current_element

        self.name_property_value_entry.set_buffer(HistoryEntryBuffer([]))

        self.notes_property_value_entry.set_buffer(HistoryTextBuffer([]))
        buffer = self.notes_property_value_entry.get_buffer()

        name = self.unlocked_database.database_manager.get_group_name(group)
        self.name_property_value_entry.set_text(name)

        self.name_property_value_entry.grab_focus()
        self.name_property_value_entry.connect(
            "changed", self.on_property_value_group_changed, "name")

        notes = self.unlocked_database.database_manager.get_notes(group)
        buffer.set_text(notes)
        buffer.connect("changed", self.on_property_value_group_changed, "notes")

        self.name_property_value_entry.grab_focus()

    #
    # Events
    #

    def on_property_value_group_changed(self, widget, name):
        self.unlocked_database.start_database_lock_timer()
        ele_uuid = self.unlocked_database.current_element.uuid

        self.is_dirty = True

        if name == "notes":
            self.unlocked_database.database_manager.set_group_notes(ele_uuid, widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False))
        elif name == "name":
            self.unlocked_database.database_manager.set_group_name(ele_uuid, widget.get_text())
            for pathbar_button in self.unlocked_database.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.element.uuid == ele_uuid:
                        pathbar_button.set_label(widget.get_text())
