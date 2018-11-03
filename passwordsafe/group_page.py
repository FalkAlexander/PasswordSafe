from gi.repository import Gtk


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
        self.unlocked_database.builder.get_object("linkedbox_right").hide()

        filename_label = self.unlocked_database.builder.get_object("filename_label")
        filename_label.set_text(self.unlocked_database.database_manager.get_group_name_from_group_object(self.unlocked_database.current_group))

        secondary_menupopover_button = self.unlocked_database.builder.get_object("secondary_menupopover_button")
        secondary_menupopover_button.show_all()

        duplicate_menu_entry = self.unlocked_database.builder.get_object("duplicate_menu_entry")
        duplicate_menu_entry.hide()

        references_menu_entry = self.unlocked_database.builder.get_object("references_menu_entry")
        references_menu_entry.hide()

        self.unlocked_database.responsive_ui.headerbar_back_button()
        self.unlocked_database.responsive_ui.headerbar_selection_button()
        self.unlocked_database.responsive_ui.action_bar()
        self.unlocked_database.responsive_ui.headerbar_title()

    #
    # Create Property Rows
    #

    def insert_group_properties_into_listbox(self, properties_list_box):
        group_uuid = self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group)

        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/PasswordSafe/group_page.ui")

        name_property_row = builder.get_object("name_property_row")
        name_property_value_entry = builder.get_object("name_property_value_entry")

        notes_property_row = builder.get_object("notes_property_row")
        notes_property_value_entry = builder.get_object("notes_property_value_entry")
        buffer = notes_property_value_entry.get_buffer()

        name_value = self.unlocked_database.database_manager.get_group_name_from_uuid(group_uuid)
        notes_value = self.unlocked_database.database_manager.get_group_notes_from_group_uuid(group_uuid)

        if self.unlocked_database.database_manager.has_group_name(group_uuid) is True:
            name_property_value_entry.set_text(name_value)
        else:
            name_property_value_entry.set_text("")

        if self.unlocked_database.database_manager.has_group_notes(group_uuid) is True:
            buffer.set_text(notes_value)
        else:
            buffer.set_text("")

        name_property_value_entry.connect("changed", self.on_property_value_group_changed, "name")
        buffer.connect("changed", self.on_property_value_group_changed, "notes")

        properties_list_box.add(name_property_row)
        properties_list_box.add(notes_property_row)

        name_property_value_entry.grab_focus()

    #
    # Events
    #

    def on_property_value_group_changed(self, widget, type):
        self.unlocked_database.start_database_lock_timer()
        group_uuid = self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group)

        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group))
        scrolled_page.set_made_database_changes(True)

        if type == "name":
            self.unlocked_database.database_manager.set_group_name(group_uuid, widget.get_text())

            for pathbar_button in self.unlocked_database.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.get_uuid() == self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group):
                        pathbar_button.set_label(widget.get_text())
        elif type == "notes":
            self.unlocked_database.database_manager.set_group_notes(group_uuid, widget.get_text(widget.get_start_iter(), widget.get_end_iter(), False))

