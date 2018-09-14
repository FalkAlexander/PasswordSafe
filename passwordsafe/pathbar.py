from gi.repository import Gtk
from passwordsafe.pathbar_button import PathbarButton
from passwordsafe.logging_manager import LoggingManager
import gi


class Pathbar(Gtk.HBox):
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    path = NotImplemented
    headerbar = NotImplemented
    builder = NotImplemented
    home_button = NotImplemented
    logging_manager = LoggingManager(True)

    def __init__(self, unlocked_database, dbm, path, headerbar):
        Gtk.HBox.__init__(self)
        self.set_name("Pathbar")
        self.unlocked_database = unlocked_database
        self.database_manager = dbm
        self.path = path
        self.headerbar = headerbar

        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")

        self.assemble_pathbar()

    #
    # Build Pathbar
    #

    def assemble_pathbar(self):
        self.first_appearance()
        self.show_all()

        self.set_hexpand(False)
        self.set_halign(Gtk.Align.START)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_propagate_natural_width(True)
        scrolled_window.set_max_content_width(600)
        viewport = Gtk.Viewport()
        viewport.add(self)
        scrolled_window.add(viewport)

        self.headerbar.pack_start(scrolled_window)
        scrolled_window.show_all()

    def first_appearance(self):
        self.home_button = self.builder.get_object("home_button")
        self.home_button.connect("clicked", self.on_home_button_clicked)
        self.set_active_style(self.home_button)
        self.pack_start(self.home_button, True, True, 0)

        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        seperator_label.set_name("SeperatorLabel")
        context = seperator_label.get_style_context()
        if self.unlocked_database.selection_mode is False:
            context.add_class('SeperatorLabel')
        else:
            context.add_class('SeperatorLabelSelectedMode')
        self.pack_end(seperator_label, True, True, 0)

    def add_home_button(self):
        self.home_button = self.builder.get_object("home_button")
        self.home_button.connect("clicked", self.on_home_button_clicked)
        self.pack_end(self.home_button, True, True, 0)

    def add_seperator_label(self):
        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        seperator_label.set_name("SeperatorLabel")
        context = seperator_label.get_style_context()
        if self.unlocked_database.selection_mode is False:
            context.add_class('SeperatorLabel')
        else:
            context.add_class('SeperatorLabelSelectedMode')
        self.pack_end(seperator_label, True, True, 0)

    #
    # Pathbar Modifications
    #

    def add_pathbar_button_to_pathbar(self, uuid):
        self.clear_pathbar()
        pathbar_button_active = self.create_pathbar_button(uuid)

        self.remove_active_style()
        self.set_active_style(pathbar_button_active)
        self.pack_end(pathbar_button_active, True, True, 0)

        self.add_seperator_label()

        parent_group = NotImplemented

        if self.database_manager.check_is_group(uuid) is True:
            parent_group = self.database_manager.get_group_parent_group_from_uuid(uuid)
        else:
            parent_group = self.database_manager.get_entry_parent_group_from_uuid(uuid)

        while not parent_group.is_root_group:
            self.pack_end(self.create_pathbar_button(
                self.database_manager.get_group_uuid_from_group_object(
                    parent_group)),
                    True, True, 0)
            self.add_seperator_label()
            parent_group = self.database_manager.get_group_parent_group_from_uuid(
                self.database_manager.get_group_uuid_from_group_object(
                    parent_group))

        self.add_home_button()
        self.show_all()

    def create_pathbar_button(self, uuid):
        pathbar_button = PathbarButton(uuid)

        pathbar_button_name = NotImplemented

        if self.database_manager.check_is_group(uuid) is True:
            pathbar_button_name = self.database_manager.get_group_name_from_uuid(uuid)
            pathbar_button.set_is_group()
        else:
            pathbar_button_name = self.database_manager.get_entry_name_from_entry_uuid(uuid)
            pathbar_button.set_is_entry()

        if pathbar_button_name is not None:
            pathbar_button.set_label(pathbar_button_name)
        else:
            pathbar_button.set_label("Noname")

        pathbar_button.set_relief(Gtk.ReliefStyle.NONE)
        pathbar_button.activate()
        pathbar_button.connect("clicked", self.on_pathbar_button_clicked)

        return pathbar_button

    def clear_pathbar(self):
        self.remove_active_style()
        for widget in self.get_children():
            self.remove(widget)

    def set_active_style(self, pathbar_button):
        context = pathbar_button.get_style_context()
        context.add_class('PathbarButtonActive')

    def remove_active_style(self):
        for pathbar_button in self.get_children():
            context = pathbar_button.get_style_context()
            context.remove_class('PathbarButtonActive')

    def rebuild_pathbar(self, group):
        if self.database_manager.check_is_root_group(group) is True:
            self.clear_pathbar()
            self.first_appearance()
            self.show_all()
        else:
            self.add_pathbar_button_to_pathbar(self.database_manager.get_group_uuid_from_group_object(group))

    #
    # Events
    #

    def on_home_button_clicked(self, widget):
        self.unlocked_database.start_database_lock_timer()
        self.remove_active_style()
        self.set_active_style(widget)

        if self.check_values_of_edit_page(self.database_manager.get_root_group()) is False:
            self.query_page_update()

        self.unlocked_database.set_current_group(self.database_manager.get_root_group())

        if self.unlocked_database.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.unlocked_database.current_group)) is not None:
            self.unlocked_database.switch_stack_page()
        else:
            self.unlocked_database.show_page_of_new_directory(False, False)

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_uuid = pathbar_button.get_uuid()
        current_group_uuid = NotImplemented
        if self.database_manager.check_is_group(pathbar_button_uuid) is True:
            current_group_uuid = self.database_manager.get_group_uuid_from_group_object(self.unlocked_database.get_current_group())
        else:
            current_group_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.unlocked_database.get_current_group())

        if pathbar_button_uuid != current_group_uuid:
            if pathbar_button.get_is_group() is True:
                self.remove_active_style()
                self.set_active_style(pathbar_button)

                if self.check_values_of_edit_page(self.database_manager.get_group_object_from_uuid(pathbar_button_uuid)) is False:
                    self.query_page_update()

                self.unlocked_database.set_current_group(self.database_manager.get_group_object_from_uuid(pathbar_button.get_uuid()))
                self.unlocked_database.switch_stack_page()
            elif pathbar_button.get_is_group() is False and self.unlocked_database.selection_mode is False:
                self.remove_active_style()
                self.set_active_style(pathbar_button)
                self.unlocked_database.set_current_group(
                    self.database_manager.get_entry_object_from_uuid(
                        pathbar_button.get_uuid()))
                if self.unlocked_database.stack.get_child_by_name(pathbar_button_uuid) is not None:
                    self.unlocked_database.switch_stack_page()
                else:
                    self.unlocked_database.show_page_of_new_directory(False, False)

    #
    # Helper Methods
    #

    def check_is_edit_page(self):
        current_group = self.unlocked_database.get_current_group()
        scrolled_page = NotImplemented
        edit_page = NotImplemented

        if self.check_is_edit_page_from_group() is True:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(current_group))
        else:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(current_group))

        edit_page = scrolled_page.check_is_edit_page()
        return edit_page

    def check_update_needed(self):
        current_group = self.unlocked_database.get_current_group()
        scrolled_page = NotImplemented
        made_database_changes = NotImplemented

        if self.check_is_edit_page_from_group() is True:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(current_group))
        else:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(current_group))

        made_database_changes = scrolled_page.get_made_database_changes()
        return made_database_changes

    def check_is_edit_page_from_group(self):
        current_group = self.unlocked_database.get_current_group()
        from_group = NotImplemented

        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(current_group)) is True:
            from_group = True
        else:
            from_group = False

        return from_group
        
    def query_page_update(self):
        if self.check_is_edit_page() is True and self.check_update_needed() is True:
            edit_page = self.unlocked_database.get_current_group()
            update_group = NotImplemented

            if self.check_is_edit_page_from_group() is True:
                update_group = self.database_manager.get_group_parent_group_from_object(edit_page)

                if self.database_manager.check_is_root_group(update_group) is True:
                    update_group = self.database_manager.get_root_group()

                self.unlocked_database.schedule_stack_page_for_destroy(self.database_manager.get_group_uuid_from_group_object(edit_page))
            else:
                update_group = self.database_manager.get_entry_parent_group_from_entry_object(edit_page)

                if self.database_manager.check_is_root_group(update_group) is True:
                    update_group = self.database_manager.get_root_group()

            stack_page_name = self.database_manager.get_group_uuid_from_group_object(update_group)
            self.unlocked_database.schedule_stack_page_for_destroy(stack_page_name)

            self.page_update_queried()

    def page_update_queried(self):
        current_group = self.unlocked_database.get_current_group()
        scrolled_page = NotImplemented

        if self.check_is_edit_page_from_group() is True:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(current_group))
        else:
            scrolled_page = self.unlocked_database.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(current_group))

        scrolled_page.set_made_database_changes(False)

    # Check all values of the group/entry - if all are blank we delete the entry/group and return true (prevents crash)
    def check_values_of_edit_page(self, pathbar_button):
        current_group = self.unlocked_database.get_current_group()
        if self.check_is_edit_page_from_group() is True:
            group_name = self.database_manager.get_group_name_from_group_object(current_group)
            group_notes = self.database_manager.get_group_notes_from_group_object(current_group)
            group_icon = self.database_manager.get_group_icon_from_group_object(current_group)

            if (group_name is None or group_name is "") and (group_notes is None or group_notes is "") and (group_icon is "0"):
                parent_group = self.database_manager.get_group_parent_group_from_object(current_group)
                self.database_manager.delete_group_from_database(current_group)
                self.rebuild_pathbar(pathbar_button)
                self.unlocked_database.schedule_stack_page_for_destroy(self.database_manager.get_group_uuid_from_group_object(parent_group))
                return True
            else:
                return False
        else:
            entry_title = self.database_manager.get_entry_name_from_entry_object(current_group)
            entry_username = self.database_manager.get_entry_username_from_entry_object(current_group)
            entry_password = self.database_manager.get_entry_password_from_entry_object(current_group)
            entry_url = self.database_manager.get_entry_notes_from_entry_object(current_group)
            entry_notes = self.database_manager.get_entry_notes_from_entry_object(current_group)
            entry_icon = self.database_manager.get_entry_icon_from_entry_object(current_group)

            if (entry_title is None or entry_title is "") and (entry_username is None or entry_username is "") and (entry_password is None or entry_password is "") and (entry_url is None or entry_url is "") and (entry_notes is None or entry_notes is "") and (entry_icon is "0"):
                parent_group = self.database_manager.get_entry_parent_group_from_entry_object(current_group)
                self.database_manager.delete_entry_from_database(current_group)
                self.rebuild_pathbar(pathbar_button)
                self.unlocked_database.schedule_stack_page_for_destroy(self.database_manager.get_group_uuid_from_group_object(parent_group))
                return True
            else:
                return False

    def is_pathbar_button_in_pathbar(self, uuid):
        for pathbar_button in self.get_children():
            if pathbar_button.get_name() == "PathbarButtonDynamic":
                if pathbar_button.get_uuid() == uuid:
                    return True

        return False

    def get_pathbar_button(self, uuid):
        for pathbar_button in self.get_children():
            if pathbar_button.get_name() == "PathbarButtonDynamic":
                if pathbar_button.get_uuid() == uuid:
                    return pathbar_button
