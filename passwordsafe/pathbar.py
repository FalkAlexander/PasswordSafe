# SPDX-License-Identifier: GPL-3.0-only
from uuid import UUID
from gi.repository import Gtk
from pykeepass.group import Group

from passwordsafe.pathbar_button import PathbarButton


class Pathbar(Gtk.HBox):
    """Pathbar provides a breadcrumb-style Box with the current hierarchy"""
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

    def rebuild_pathbar(self, group: Group) -> None:
        """Rebuild the pathbar up to a certain group"""
        if self.database_manager.check_is_root_group(group):
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

        self.unlocked_database.switch_page(
            self.database_manager.get_root_group())

    def on_pathbar_button_clicked(self, pathbar_button):
        self.unlocked_database.start_database_lock_timer()
        pathbar_button_uuid = pathbar_button.uuid
        current_uuid = self.unlocked_database.current_element.uuid

        if pathbar_button_uuid != current_uuid:
            if pathbar_button.get_is_group() is True:
                self.remove_active_style()
                self.set_active_style(pathbar_button)

                if not self.check_values_of_edit_page(self.database_manager.get_group(pathbar_button_uuid)):
                    self.query_page_update()

                group = self.database_manager.get_group(
                    pathbar_button.uuid)
                self.unlocked_database.switch_page(group)
            elif pathbar_button.get_is_group() is False and self.unlocked_database.selection_ui.selection_mode_active is False:
                self.remove_active_style()
                self.set_active_style(pathbar_button)
                entry = self.database_manager.get_entry_object_from_uuid(
                    pathbar_button.uuid)
                self.unlocked_database.switch_page(entry)
    #
    # Helper Methods
    #

    def check_is_edit_page(self):
        """Return if the current page is an 'edit page'"""
        page = self.unlocked_database.get_current_page()
        return page.check_is_edit_page()

    def check_update_needed(self):
        """Returns True if the pathbar needs updating"""
        page = self.unlocked_database.get_current_page()
        return page.is_dirty

    def check_is_edit_page_from_group(self):
        ele_uuid = self.unlocked_database.current_element.uuid
        is_group = self.database_manager.check_is_group(ele_uuid)
        return is_group

    def query_page_update(self):
        if self.check_is_edit_page() is True:
            if self.check_update_needed() is True:
                edit_page = self.unlocked_database.current_element
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

                edit_page = self.unlocked_database.current_element
                self.unlocked_database.schedule_stack_page_for_destroy(edit_page.uuid)

    def page_update_queried(self):
        """Marks the curent page as not dirty"""
        page = self.unlocked_database.get_current_page()
        page.is_dirty = False

    def check_values_of_edit_page(self, parent_group: Group) -> bool:
        """Check all values of the group/entry - if all are blank we delete the entry/group and return true"""
        current_elt = self.unlocked_database.current_element
        notes = self.database_manager.get_notes(current_elt)
        icon = self.database_manager.get_icon(current_elt)

        if self.database_manager.check_is_group_object(current_elt):
            group_name = self.database_manager.get_group_name(current_elt)
            if not (group_name or notes or icon):
                parent_group = self.database_manager.get_parent_group(
                    current_elt)
                self.database_manager.delete_from_database(current_elt)
                self.rebuild_pathbar(parent_group)
                self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
                return True

            return False
        else:
            entry_title = self.database_manager.get_entry_name(current_elt)
            entry_username = self.database_manager.get_entry_username(
                current_elt)
            entry_password = self.database_manager.get_entry_password(
                current_elt)
            entry_url = self.database_manager.get_entry_url(current_elt)
            entry_attributes = self.database_manager.get_entry_attributes(
                current_elt)
            if not (entry_title or entry_username or entry_password
                    or entry_url or notes or (icon != "0")
                    or entry_attributes):
                parent_group = self.database_manager.get_parent_group(
                    current_elt)
                self.database_manager.delete_from_database(current_elt)
                self.rebuild_pathbar(parent_group)
                self.unlocked_database.schedule_stack_page_for_destroy(parent_group.uuid)
                return True

            return False

    def uuid_in_pathbar(self, uuid: UUID) -> bool:
        """Return True if the uuid entry is visible in the bar"""
        for button in self.get_children():
            if button.get_name() == "PathbarButtonDynamic" and \
               button.uuid == uuid:
                return True
        return False

    def get_pathbar_button(self, uuid: UUID) -> 'PathbarButton':
        for pathbar_button in self.get_children():
            if pathbar_button.get_name() == "PathbarButtonDynamic":
                if pathbar_button.uuid == uuid:
                    return pathbar_button
