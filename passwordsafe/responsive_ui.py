import ntpath


class ResponsiveUI:
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
    # Responsive Controls
    #

    def action_bar(self):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group).urn)
        if self.unlocked_database.window.mobile_width is True:
            if len(self.unlocked_database.pathbar.viewport.get_children()) is not 0:
                self.unlocked_database.pathbar.viewport.remove(self.unlocked_database.pathbar)
                self.unlocked_database.pathbar.pathbar_box.hide()

            if len(self.unlocked_database.action_bar_box.get_children()) is 0:
                self.unlocked_database.action_bar_box.add(self.unlocked_database.pathbar)

            if scrolled_page.edit_page is False and self.unlocked_database.stack.get_visible_child() is not self.unlocked_database.stack.get_child_by_name("search"):
                self.unlocked_database.revealer.set_reveal_child(True)
            else:
                self.unlocked_database.revealer.set_reveal_child(False)
        else:
            self.unlocked_database.revealer.set_reveal_child(False)

            if len(self.unlocked_database.action_bar_box.get_children()) is not 0:
                self.unlocked_database.action_bar_box.remove(self.unlocked_database.pathbar)

            if len(self.unlocked_database.pathbar.viewport.get_children()) is 0:
                self.unlocked_database.pathbar.viewport.add(self.unlocked_database.pathbar)
                self.unlocked_database.pathbar.pathbar_box.show()

    def headerbar_title(self):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group).urn)
        if self.unlocked_database.window.mobile_width is True and self.unlocked_database.selection_ui.selection_mode_active is False:
            if len(self.unlocked_database.builder.get_object("title_box").get_children()) is not 0:
                return

            filename_label = self.unlocked_database.builder.get_object("filename_label")
            if scrolled_page.edit_page is False:
                filename_label.set_text(ntpath.basename(self.unlocked_database.database_manager.database_path))
            else:
                if self.unlocked_database.database_manager.check_is_group_object(self.unlocked_database.current_group) is False:
                    filename_label.set_text(self.unlocked_database.database_manager.get_entry_name_from_entry_object(self.unlocked_database.current_group))
                else:
                    filename_label.set_text(self.unlocked_database.database_manager.get_group_name_from_group_object(self.unlocked_database.current_group))

            self.unlocked_database.builder.get_object("title_box").add(filename_label)
        else:
            if len(self.unlocked_database.builder.get_object("title_box").get_children()) is 0:
                return

            self.unlocked_database.builder.get_object("title_box").remove(self.unlocked_database.builder.get_object("filename_label"))

    def headerbar_back_button(self):
        if self.unlocked_database.window.mobile_width is True and self.unlocked_database.selection_ui.selection_mode_active is False:
            self.unlocked_database.builder.get_object("pathbar_button_back_revealer").set_reveal_child(True)
        else:
            self.unlocked_database.builder.get_object("pathbar_button_back_revealer").set_reveal_child(False)

    def headerbar_selection_button(self):
        scrolled_page = self.unlocked_database.stack.get_child_by_name(self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group).urn)
        if self.unlocked_database.selection_ui.selection_mode_active is True:
            return

        if self.unlocked_database.window.mobile_width is True and scrolled_page.edit_page is False:
            self.unlocked_database.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(True)
            self.unlocked_database.builder.get_object("selection_button_revealer").set_reveal_child(False)
        else:
            self.unlocked_database.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(False)

            if self.unlocked_database.window.mobile_width is True:
                return

            self.unlocked_database.builder.get_object("selection_button_revealer").set_reveal_child(True)
