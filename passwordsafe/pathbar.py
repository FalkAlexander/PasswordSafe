from gi.repository import Gtk
from passwordsafe.pathbar_button import PathbarButton


class Pathbar(Gtk.HBox):
    unlocked_database = NotImplemented
    database_manager = NotImplemented
    path = NotImplemented
    builder = NotImplemented
    home_button = NotImplemented

    def __init__(self, unlocked_database, dbm, path):
        Gtk.HBox.__init__(self)
        self.set_name("Pathbar")
        self.unlocked_database = unlocked_database
        self.database_manager = dbm
        self.path = path

        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_database.ui")

        self.assemble_pathbar()

    #
    # Build Pathbar
    #

    def assemble_pathbar(self):
        self.first_appearance()
        self.set_halign(Gtk.Align.START)
        self.show_all()

    def first_appearance(self):
        self.home_button = self.builder.get_object("home_button")
        self.home_button.connect("clicked", self.on_home_button_clicked)
        self.set_active_style(self.home_button)
        self.pack_start(self.home_button, True, True, 0)

        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        seperator_label.set_name("SeperatorLabel")
        context = seperator_label.get_style_context()
        if self.unlocked_database.selection_ui.selection_mode_active is False:
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
        if self.unlocked_database.selection_ui.selection_mode_active is False:
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

        parent_group = self.database_manager.get_parent_group(uuid)
        while not parent_group.is_root_group:
            self.pack_end(
                self.create_pathbar_button(parent_group.uuid),
                True, True, 0)
            self.add_seperator_label()
            parent_group = self.database_manager.get_parent_group(
                parent_group.uuid)

        self.add_home_button()
        self.show_all()

    def create_pathbar_button(self, uuid):
        pathbar_button = PathbarButton(uuid)

        pathbar_button_name = NotImplemented

        if self.database_manager.check_is_group(uuid) is True:
            pathbar_button_name = self.database_manager.get_group_name(uuid)
            pathbar_button.set_is_group()
        else:
            pathbar_button_name = self.database_manager.get_entry_name(uuid)
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
            self.add_pathbar_button_to_pathbar(group.uuid)

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
        page_name = self.unlocked_database.current_group.uuid.urn
        if self.unlocked_database.stack.get_child_by_name(page_name):
            self.unlocked_database.switch_stack_page()
        else:
            self.unlocked_database.show_page_of_new_directory(False, False)

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_uuid = pathbar_button.get_uuid()
        current_uuid = self.unlocked_database.current_group.uuid

        if pathbar_button_uuid != current_uuid:
            if pathbar_button.get_is_group() is True:
                self.remove_active_style()
                self.set_active_style(pathbar_button)

                if not self.check_values_of_edit_page(self.database_manager.get_group(pathbar_button_uuid)):
                    self.query_page_update()

                self.unlocked_database.set_current_group(self.database_manager.get_group(pathbar_button.get_uuid()))
                self.unlocked_database.switch_stack_page()
            elif pathbar_button.get_is_group() is False and self.unlocked_database.selection_ui.selection_mode_active is False:
                self.remove_active_style()
                self.set_active_style(pathbar_button)
                self.unlocked_database.set_current_group(
                    self.database_manager.get_entry_object_from_uuid(
                        pathbar_button.get_uuid()))
                if self.unlocked_database.stack.get_child_by_name(pathbar_button_uuid.urn) is not None:
                    self.unlocked_database.switch_stack_page()
                else:
                    self.unlocked_database.show_page_of_new_directory(False, False)

    #
    # Helper Methods
    #

    def check_is_edit_page(self):
        """Return if the current page is an 'edit page'

        FIXME: current_group can also be an entry and not a group!
        """
        page_name = self.unlocked_database.current_group.uuid.urn
        page = self.unlocked_database.stack.get_child_by_name(page_name)
        return page.check_is_edit_page()

    def check_update_needed(self):
        """Returns True if the pathbar needs updating"""
        page_name = self.unlocked_database.current_group.uuid.urn
        page = self.unlocked_database.stack.get_child_by_name(page_name)
        return page.is_dirty

    def check_is_edit_page_from_group(self):
        # FIXME: current_group can be an Entry too!
        ele_uuid = self.unlocked_database.current_group.uuid
        is_group = self.database_manager.check_is_group(ele_uuid)
        return is_group

    def query_page_update(self):
        if self.check_is_edit_page() is True:
            if self.check_update_needed() is True:
                edit_page = self.unlocked_database.get_current_group()
                update_group = NotImplemented

                if self.check_is_edit_page_from_group() is True:
                    update_group = self.database_manager.get_parent_group(
                        edit_page)

                    if self.database_manager.check_is_root_group(update_group) is True:
                        update_group = self.database_manager.get_root_group()

                    self.unlocked_database.schedule_stack_page_for_destroy(edit_page.uuid)
                else:
                    update_group = self.database_manager.get_parent_group(edit_page)

                    if self.database_manager.check_is_root_group(update_group) is True:
                        update_group = self.database_manager.get_root_group()

                page_name = update_group.uuid
                self.unlocked_database.schedule_stack_page_for_destroy(page_name)

                self.page_update_queried()
            else:
                if self.check_is_edit_page_from_group() is False:
                    return

                edit_page = self.unlocked_database.get_current_group()
                self.unlocked_database.schedule_stack_page_for_destroy(edit_page.uuid)

    def page_update_queried(self):
        """Marks the curent page as not dirty"""
        page_name = self.unlocked_database.current_group.uuid.urn
        page = self.unlocked_database.stack.get_child_by_name(page_name)
        page.is_dirty = False

    # Check all values of the group/entry - if all are blank we delete the entry/group and return true (prevents crash)
    def check_values_of_edit_page(self, pathbar_button):
        current_group = self.unlocked_database.get_current_group()
        if self.check_is_edit_page_from_group() is True:
            group_name = self.database_manager.get_group_name(current_group)
            group_notes = self.database_manager.get_group_notes_from_group_object(current_group)
            group_icon = self.database_manager.get_group_icon_from_group_object(current_group)

            if (group_name is None or group_name == "") and (group_notes is None or group_notes == "") and (group_icon == "0"):
                parent_group = self.database_manager.get_parent_group(
                    current_group)
                self.database_manager.delete_group_from_database(current_group)
                self.rebuild_pathbar(pathbar_button)
                self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
                return True
            return False
        else:
            entry_title = self.database_manager.get_entry_name(current_group)
            entry_username = self.database_manager.get_entry_username_from_entry_object(current_group)
            entry_password = self.database_manager.get_entry_password_from_entry_object(current_group)
            entry_url = self.database_manager.get_entry_url_from_entry_object(current_group)
            entry_notes = self.database_manager.get_entry_notes_from_entry_object(current_group)
            entry_icon = self.database_manager.get_entry_icon_from_entry_object(current_group)
            entry_attributes = len(self.database_manager.get_entry_attributes_from_entry_object(current_group))

            if (entry_title is None or entry_title == "") and (entry_username is None or entry_username == "") and (entry_password is None or entry_password == "") and (entry_url is None or entry_url == "") and (entry_notes is None or entry_notes == "") and (entry_icon == "0") and (entry_attributes == 0):
                parent_group = self.database_manager.get_parent_group(current_group)
                self.database_manager.delete_entry_from_database(current_group)
                self.rebuild_pathbar(pathbar_button)
                self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
                return True
            return False

    def uuid_in_pathbar(self, uuid):
        """Return True if the uuid entry is visible in the bar"""
        for button in self.get_children():
            if button.get_name() == "PathbarButtonDynamic" and \
               button.get_uuid() == uuid:
                return True
        return False

    def get_pathbar_button(self, uuid):
        for pathbar_button in self.get_children():
            if pathbar_button.get_name() == "PathbarButtonDynamic":
                if pathbar_button.get_uuid() == uuid:
                    return pathbar_button
