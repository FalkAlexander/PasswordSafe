# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk
from passwordsafe.history_buffer import HistoryEntryBuffer, HistoryTextBuffer


class GroupPage:
    #
    # Global Variables
    #

    unlocked_database = NotImplemented

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    #
    # Header Bar
    #

    # Group creation/editing headerbar
    def set_group_edit_page_headerbar(self):
        secondary_menu_button = self.unlocked_database.headerbar_builder.get_object(
            "secondary_menu_button"
        )
        group_menu = self.unlocked_database.headerbar_builder.get_object(
            "group_menu"
        )
        secondary_menu_button.set_menu_model(group_menu)
        secondary_menu_button.show_all()

        self.unlocked_database.responsive_ui.headerbar_selection_button()
        self.unlocked_database.responsive_ui.action_bar()
        self.unlocked_database.responsive_ui.headerbar_title()

    #
    # Create Property Rows
    #

    def insert_group_properties_into_listbox(self, properties_list_box):
        group = self.unlocked_database.current_element

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/group_page.ui")

        name_property_row = builder.get_object("name_property_row")
        name_property_value_entry = builder.get_object("name_property_value_entry")
        name_property_value_entry.set_buffer(HistoryEntryBuffer([]))

        notes_property_row = builder.get_object("notes_property_row")
        notes_property_value_entry = builder.get_object("notes_property_value_entry")
        notes_property_value_entry.get_style_context().add_class("codeview")
        notes_property_value_entry.set_buffer(HistoryTextBuffer([]))
        buffer = notes_property_value_entry.get_buffer()

        name = self.unlocked_database.database_manager.get_group_name(group)
        name_property_value_entry.set_text(name)

        notes = self.unlocked_database.database_manager.get_notes(group)
        buffer.set_text(notes)

        name_property_value_entry.connect("changed", self.on_property_value_group_changed, "name")
        buffer.connect("changed", self.on_property_value_group_changed, "notes")

        properties_list_box.add(name_property_row)
        properties_list_box.add(notes_property_row)

        name_property_value_entry.grab_focus()

    #
    # Events
    #

    def on_property_value_group_changed(self, widget, type_name):
        self.unlocked_database.start_database_lock_timer()
        ele_uuid = self.unlocked_database.current_element.uuid

        scrolled_page = self.unlocked_database.get_current_page()
        scrolled_page.is_dirty = True

        if type_name == "name":
            self.unlocked_database.database_manager.set_group_name(ele_uuid, widget.get_text())

            for pathbar_button in self.unlocked_database.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.uuid == ele_uuid:
                        pathbar_button.set_label(widget.get_text())
        elif type_name == "notes":
            self.unlocked_database.database_manager.set_group_notes(ele_uuid, widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False))
