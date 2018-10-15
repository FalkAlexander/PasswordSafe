from gettext import gettext as _


class SelectionUI:
    #
    # Global Variables
    #

    unlocked_database = NotImplemented
    selection_mode_active = False

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    def initialize(self):
        # Selection Headerbar
        selection_cancel_button = self.unlocked_database.builder.get_object("selection_cancel_button")
        selection_cancel_button.connect("clicked", self.on_selection_cancel_button_clicked)

        selection_delete_button = self.unlocked_database.builder.get_object("selection_delete_button")
        selection_delete_button.connect("clicked", self.on_selection_delete_button_clicked)

        selection_cut_button = self.unlocked_database.builder.get_object("selection_cut_button")
        selection_cut_button.connect("clicked", self.on_selection_cut_button_clicked)

    #
    # Selection Mode
    #

    # Selection headerbar
    def set_selection_headerbar(self, widget, select_row=None):
        self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(False)

        selection_options_button = self.unlocked_database.builder.get_object("selection_options_button")
        selection_button_box = self.unlocked_database.builder.get_object("selection_button_box")

        title_box = self.unlocked_database.builder.get_object("title_box")
        headerbar_right_box = self.unlocked_database.builder.get_object("headerbar_right_box")

        linkedbox_right = self.unlocked_database.builder.get_object("linkedbox_right")

        headerbar_right_box.remove(linkedbox_right)
        headerbar_right_box.add(selection_button_box)
        title_box.add(selection_options_button)

        context = self.unlocked_database.headerbar.get_style_context()
        context.add_class('selection-mode')

        self.unlocked_database.headerbar.set_show_close_button(False)

        self.unlocked_database.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(False)

        self.selection_mode_active = True

        self.prepare_selection_page(select_row)
        self.unlocked_database.responsive_ui.headerbar_title()

    def remove_selection_headerbar(self):
        for stack_page in self.unlocked_database.stack.get_children():
            if stack_page.check_is_edit_page() is False:
                list_box = stack_page.get_children()[0].get_children()[0].get_children()[0].get_children()[0]
                for row in list_box:
                    if hasattr(row, "checkbox_box") is True:
                        row.checkbox_box.hide()
                        row.selection_checkbox.set_active(False)
                    if hasattr(row, "edit_button") is True:
                        row.edit_button.show_all()

        selection_options_button = self.unlocked_database.builder.get_object("selection_options_button")
        selection_button_box = self.unlocked_database.builder.get_object("selection_button_box")

        title_box = self.unlocked_database.builder.get_object("title_box")
        headerbar_right_box = self.unlocked_database.builder.get_object("headerbar_right_box")

        linkedbox_right = self.unlocked_database.builder.get_object("linkedbox_right")

        headerbar_right_box.remove(selection_button_box)
        headerbar_right_box.add(linkedbox_right)
        title_box.remove(selection_options_button)
        self.unlocked_database.headerbar.set_show_close_button(True)

        context = self.unlocked_database.headerbar.get_style_context()
        context.remove_class('selection-mode')

        self.unlocked_database.entries_selected.clear()
        self.unlocked_database.groups_selected.clear()

        for element in self.unlocked_database.pathbar.get_children():
            if element.get_name() == "SeperatorLabel":
                el_context = element.get_style_context()
                el_context.remove_class('SeperatorLabelSelectedMode')
                el_context.add_class('SeperatorLabel')

        self.selection_mode_active = False
        self.unlocked_database.show_page_of_new_directory(False, False)

        self.unlocked_database.responsive_ui.headerbar_back_button()
        self.unlocked_database.responsive_ui.headerbar_selection_button()
        self.unlocked_database.responsive_ui.action_bar()
        self.unlocked_database.responsive_ui.headerbar_title()

    def prepare_selection_page(self, select_row=None):
        for stack_page in self.unlocked_database.stack.get_children():
            if stack_page.check_is_edit_page() is False:
                list_box = stack_page.get_children()[0].get_children()[0].get_children()[0].get_children()[0]
                for row in list_box:
                    if hasattr(row, "checkbox_box") is True:
                        row.checkbox_box.show()
                    if hasattr(row, "edit_button") is True:
                        row.edit_button.hide()

        if select_row is not None:
            select_row.selection_checkbox.set_active(True)

    #
    # Events
    #

    def on_selection_cancel_button_clicked(self, widget):
        self.remove_selection_headerbar()
        self.unlocked_database.show_page_of_new_directory(False, False)

    def on_selection_delete_button_clicked(self, widget):
        rebuild_pathbar = False
        reset_stack_page = False
        group = None

        for entry_row in self.unlocked_database.entries_selected:
            entry = self.unlocked_database.database_manager.get_entry_object_from_uuid(entry_row.get_uuid())
            self.unlocked_database.database_manager.delete_entry_from_database(entry)
            # If the deleted entry is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.is_pathbar_button_in_pathbar(entry_row.get_uuid()) is True:
                rebuild_pathbar = True

        for group_row in self.unlocked_database.groups_selected:
            group = self.unlocked_database.database_manager.get_group_object_from_uuid(group_row.get_uuid())
            self.unlocked_database.database_manager.delete_group_from_database(group)
            # If the deleted group is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.is_pathbar_button_in_pathbar(group_row.get_uuid()) is True:
                rebuild_pathbar = True
            if self.unlocked_database.database_manager.get_group_uuid_from_group_object(group) == self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group):
                rebuild_pathbar = True
                reset_stack_page = True

        for stack_page in self.unlocked_database.stack.get_children():
            if stack_page.check_is_edit_page() is False:
                stack_page.destroy()

        self.unlocked_database.show_page_of_new_directory(False, False)

        if rebuild_pathbar is True:
            self.unlocked_database.pathbar.rebuild_pathbar(self.unlocked_database.current_group)

        if reset_stack_page is True:
            self.unlocked_database.current_group = self.unlocked_database.database_manager.get_root_group()

        self.unlocked_database.show_database_action_revealer(_("Deletion completed"))

        self.unlocked_database.entries_selected.clear()
        self.unlocked_database.groups_selected.clear()
        self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(False)

        # It is more efficient to do this here and not in the database manager loop
        self.unlocked_database.database_manager.changes = True

    def on_selection_cut_button_clicked(self, widget):
        rebuild_pathbar = False

        for entry_row in self.unlocked_database.entries_selected:
            entry_uuid = entry_row.get_uuid()
            self.unlocked_database.database_manager.move_entry(entry_uuid, self.unlocked_database.current_group)
            # If the moved entry is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.is_pathbar_button_in_pathbar(entry_row.get_uuid()) is True:
                rebuild_pathbar = True

        move_conflict = False

        for group_row in self.unlocked_database.groups_selected:
            group_uuid = group_row.get_uuid()
            if self.unlocked_database.database_manager.parent_checker(self.unlocked_database.current_group, self.unlocked_database.database_manager.get_group_object_from_uuid(group_uuid)) is False:
                self.unlocked_database.database_manager.move_group(group_uuid, self.unlocked_database.current_group)
            else:
                move_conflict = True
            # If the moved group is in the pathbar, we need to rebuild the pathbar
            if self.unlocked_database.pathbar.is_pathbar_button_in_pathbar(group_row.get_uuid()) is True:
                rebuild_pathbar = True

        for stack_page in self.unlocked_database.stack.get_children():
            if stack_page.check_is_edit_page() is False:
                stack_page.destroy()

        self.unlocked_database.show_page_of_new_directory(False, False)

        if rebuild_pathbar is True:
            self.unlocked_database.pathbar.rebuild_pathbar(self.unlocked_database.current_group)

        if move_conflict is False:
            self.unlocked_database.show_database_action_revealer(_("Move completed"))
        else:
            self.unlocked_database.show_database_action_revealer(_("Skipped moving group into itself"))

        self.unlocked_database.entries_selected.clear()
        self.unlocked_database.groups_selected.clear()
        self.unlocked_database.builder.get_object("selection_delete_button").set_sensitive(False)
        self.unlocked_database.builder.get_object("selection_cut_button").set_sensitive(False)

        # It is more efficient to do this here and not in the database manager loop
        self.unlocked_database.database_manager.changes = True

    def on_selection_popover_button_clicked(self, action, param, selection_type):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group))
        viewport = scrolled_page.get_children()[0]
        overlay = viewport.get_children()[0]
        list_box = NotImplemented

        column = overlay.get_children()[0]
        list_box = column.get_children()[0]

        for row in list_box:
            if selection_type is "all":
                row.selection_checkbox.set_active(True)
            else:
                row.selection_checkbox.set_active(False)

    #
    # Helper
    #

    def row_selection_toggled(self, row):
        if row.selection_checkbox.get_active():
            row.selection_checkbox.set_active(False)
        else:
            row.selection_checkbox.set_active(True)
