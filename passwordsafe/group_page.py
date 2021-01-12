# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk
from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/group_page.ui")
class GroupPage(Gtk.ScrolledWindow):

    __gtype_name__ = "GroupPage"

    name_property_value_entry = Gtk.Template.Child()
    notes_property_value_entry = Gtk.Template.Child()

    edit_page = True
    is_dirty = False

    def __init__(self, unlocked_database):
        super().__init__()

        self.unlocked_database = unlocked_database

        group = self.unlocked_database.current_element
        name = self.unlocked_database.database_manager.get_group_name(group)
        notes = self.unlocked_database.database_manager.get_notes(group)
        notes_buffer = HistoryTextBuffer([])

        # Setup Widgets
        notes_buffer.set_text(notes)
        self.name_property_value_entry.set_buffer(HistoryEntryBuffer([]))
        self.name_property_value_entry.set_text(name)
        self.name_property_value_entry.grab_focus()

        self.notes_property_value_entry.set_buffer(notes_buffer)
        notes_buffer.set_text(notes)

        # Connect Signals
        self.name_property_value_entry.connect(
            "changed", self.on_property_value_group_changed, "name")
        notes_buffer.connect("changed", self.on_property_value_group_changed, "notes")

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
