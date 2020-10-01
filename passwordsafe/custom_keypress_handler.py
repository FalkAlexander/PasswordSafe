import uuid as u

from gi.repository import Gtk, Gdk
import passwordsafe.pathbar_button


class CustomKeypressHandler:
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
    # Special Keys (e.g. type-to-search)
    #

    def register_custom_events(self):
        self.unlocked_database.window.connect("key-press-event", self.on_special_key_pressed)
        self.unlocked_database.window.connect("key-release-event", self.on_special_key_released)
        self.unlocked_database.window.connect("button-release-event", self._on_button_released)

    def on_special_key_pressed(self, _window, eventkey):
        group_uuid = self.unlocked_database.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group)

        if self.unlocked_database.window.container.page_num(self.unlocked_database.parent_widget) == self.unlocked_database.window.container.get_current_page():
            scrolled_page = self.unlocked_database.stack.get_child_by_name(group_uuid.urn)
            if self.unlocked_database.database_locked is False and self.unlocked_database.selection_ui.selection_mode_active is False and self.unlocked_database.stack.get_visible_child() is not self.unlocked_database.stack.get_child_by_name("search"):
                if scrolled_page.edit_page is True:
                    if eventkey.keyval == Gdk.KEY_Tab:
                        if self.unlocked_database.window.get_focus() is None:
                            return
                        if "TabBox" in self.unlocked_database.window.get_focus().get_name():
                            self.tab_to_next_input_entry(scrolled_page)
                            return True
                else:
                    if eventkey.string.isalpha() or eventkey.string.isnumeric():
                        self.unlocked_database.search.set_search_headerbar(self.unlocked_database.builder.get_object("search_button"))

    def tab_to_next_input_entry(self, scrolled_page):
        focus_widget = self.unlocked_database.window.get_focus()
        focus_widget_index = focus_widget.get_parent().get_children().index(focus_widget)
        new_index = focus_widget_index + 1
        if new_index < len(focus_widget.get_parent().get_children()):
            if focus_widget.get_parent().get_children()[new_index].get_name() == "TabBox_Next":
                self.unlocked_database.window.set_focus(focus_widget.get_parent().get_children()[new_index])
                return

        rows = scrolled_page.properties_list_box.get_children()
        current_row = self.iterate_parents(self.unlocked_database.window.get_focus())
        current_index = rows.index(current_row)
        new_index = current_index + 1
        if new_index < len(rows):
            next_row = rows[new_index]
        else:
            next_row = rows[0]

        if next_row.get_name() == "ShowAllRow":
            next_row = rows[0]

        self.interate_to_next_input(next_row)

    def interate_to_next_input(self, parent):
        if parent.get_name() == "TabBox":
            self.unlocked_database.window.set_focus(parent)
            return

        if hasattr(parent, "get_children"):
            for child in parent.get_children():
                if child.get_name() == "TabBox":
                    self.unlocked_database.window.set_focus(child)
                else:
                    self.interate_to_next_input(child)

    def iterate_parents(self, child):
        if isinstance(child, Gtk.ListBoxRow):
            return child
        elif hasattr(child, "get_parent"):
            if isinstance(child.get_parent(), Gtk.ListBoxRow):
                return child.get_parent()
            else:
                return self.iterate_parents(child.get_parent())

    def _goto_parent_group(self):
        """Go to the parent group of the pathbar."""
        uuid = u.UUID(self.unlocked_database.stack.get_visible_child_name())
        db_manager = self.unlocked_database.database_manager
        if self.unlocked_database.database_manager.check_is_group(uuid):
            parent_group = db_manager.get_group_parent_group_from_uuid(uuid)
        else:
            parent_group = db_manager.get_entry_parent_group_from_uuid(uuid)

        if db_manager.check_is_root_group(parent_group):
            pathbar = self.unlocked_database.pathbar
            pathbar.on_home_button_clicked(pathbar.home_button)

        pathbar_btn_type = passwordsafe.pathbar_button.PathbarButton
        for button in self.unlocked_database.pathbar:
            if (button.get_name() == "PathbarButtonDynamic"
                    and type(button) is pathbar_btn_type):
                if button.uuid == db_manager.get_group_uuid_from_group_object(parent_group):
                    pathbar = self.unlocked_database.pathbar
                    pathbar.on_pathbar_button_clicked(button)

    def _can_goto_parent_group(self):
        """Check that the current item in the pathbar has a parent."""
        current_group = self.unlocked_database.current_group
        db_view = self.unlocked_database
        db_manager = db_view.database_manager
        container = db_view.window.container
        current_page = container.get_current_page()
        search_view = db_view.stack.get_child_by_name("search")
        if (container.page_num(db_view.parent_widget) != current_page
                or db_view.database_locked
                or (db_manager.check_is_group_object(current_group)
                    and db_manager.check_is_root_group(current_group))
                or db_view.selection_ui.selection_mode_active
                or db_view.stack.get_visible_child() is search_view):
            return False

        return True

    def on_special_key_released(self, window, eventkey):
        if not self._can_goto_parent_group():
            return

        group_uuid = self.unlocked_database.current_group.uuid
        scrolled_page = self.unlocked_database.stack.get_child_by_name(group_uuid.urn)
        if (eventkey.keyval == Gdk.KEY_BackSpace
                and self.unlocked_database.database_manager.check_is_group(group_uuid)
                and not scrolled_page.edit_page):
            self._goto_parent_group()
        elif (eventkey.keyval == Gdk.KEY_Escape
              and scrolled_page.edit_page):
            self._goto_parent_group()

    def _on_button_released(self, widget, event):
        """Go to the parent group with the back button.

        :param Gtk.Widget widget: the main window
        :param Gtk.Event event: the event
        """
        # Mouse button 8 is the back button.
        if (event.button != 8
                or not self._can_goto_parent_group()):
            return False

        self._goto_parent_group()
        return True
