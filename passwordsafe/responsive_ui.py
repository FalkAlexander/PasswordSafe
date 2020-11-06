import ntpath


class ResponsiveUI():
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
        """Move pathbar between top headerbar and bottom actionbar if needed"""

        db = self.unlocked_database  # pylint: disable=C0103
        page_name = db.current_element.uuid.urn
        page = db.stack.get_child_by_name(page_name)

        if db.window.mobile_width and not db.action_bar.get_children():
            # mobile width: hide pathbar in header
            db.headerbar_box.remove(self.unlocked_database.pathbar)
            db.headerbar_box.hide()
            # and put it in the bottom Action bar instead
            db.action_bar.add(self.unlocked_database.pathbar)
            db.action_bar.show()

            if (not page.edit_page
                    and not db.search_active):
                # Don't show pathbar on edit or search pages
                db.revealer.set_reveal_child(True)
            else:
                db.revealer.set_reveal_child(False)
        elif not db.window.mobile_width and db.action_bar.get_children():
            # Desktop width AND pathbar is in actionbar
            db.revealer.set_reveal_child(False)
            db.action_bar.remove(self.unlocked_database.pathbar)
            db.headerbar_box.add(self.unlocked_database.pathbar)
            db.headerbar_box.show()

    def headerbar_title(self):
        page_name = self.unlocked_database.current_element.uuid.urn
        scrolled_page = self.unlocked_database.stack.get_child_by_name(page_name)
        if self.unlocked_database.window.mobile_width and not self.unlocked_database.selection_ui.selection_mode_active:
            if self.unlocked_database.builder.get_object("title_box").get_children():
                return

            filename_label = self.unlocked_database.builder.get_object("filename_label")
            if scrolled_page.edit_page is False:
                filename_label.set_text(ntpath.basename(self.unlocked_database.database_manager.database_path))
            else:
                if self.unlocked_database.database_manager.check_is_group_object(self.unlocked_database.current_element) is False:
                    db_manager = self.unlocked_database.database_manager
                    entry_name = db_manager.get_entry_name(
                        self.unlocked_database.current_element)
                    filename_label.set_text(entry_name)
                else:
                    db_manager = self.unlocked_database.database_manager
                    group_name = db_manager.get_group_name(
                        self.unlocked_database.current_element)
                    filename_label.set_text(group_name)

            self.unlocked_database.builder.get_object("title_box").add(filename_label)
        else:
            if self.unlocked_database.builder.get_object("title_box").get_children():
                return

            self.unlocked_database.builder.get_object("title_box").remove(self.unlocked_database.builder.get_object("filename_label"))

    def headerbar_back_button(self):
        if (self.unlocked_database.window.mobile_width
                and not self.unlocked_database.selection_ui.selection_mode_active):
            self.unlocked_database.builder.get_object("pathbar_button_back_revealer").set_reveal_child(True)
        else:
            self.unlocked_database.builder.get_object("pathbar_button_back_revealer").set_reveal_child(False)

    def headerbar_selection_button(self):
        """Update the visibility of the headerbar buttons."""
        page_name = self.unlocked_database.current_element.uuid.urn
        scrolled_page = self.unlocked_database.stack.get_child_by_name(page_name)
        if self.unlocked_database.selection_ui.selection_mode_active:
            return

        if (self.unlocked_database.window.mobile_width
                and not scrolled_page.edit_page):
            self.unlocked_database.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(True)
            self.unlocked_database.builder.get_object("selection_button_revealer").set_reveal_child(False)
        else:
            self.unlocked_database.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(False)

            if self.unlocked_database.window.mobile_width:
                return

            self.unlocked_database.builder.get_object("selection_button_revealer").set_reveal_child(True)
