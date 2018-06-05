from gi.repository import Gio, Gdk, Gtk
from keepassgtk.logging_manager import LoggingManager
from keepassgtk.pathbar import Pathbar
from keepassgtk.entry_row import EntryRow
from keepassgtk.group_row import GroupRow
from keepassgtk.scrolled_page import ScrolledPage
import gi
import ntpath
import threading
gi.require_version('Gtk', '3.0')


class UnlockedDatabase:
    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    scrolled_window = NotImplemented
    stack = NotImplemented
    database_manager = NotImplemented
    logging_manager = LoggingManager(True)
    current_group = NotImplemented
    pathbar = NotImplemented
    overlay = NotImplemented
    scheduled_page_destroy = []

    entry_marked_for_delete = NotImplemented
    group_marked_for_delete = NotImplemented
    group_marked_for_edit = NotImplemented

    def __init__(self, window, widget, dbm):
        self.window = window
        self.parent_widget = widget
        self.database_manager = dbm
        self.assemble_listbox()
        self.window.opened_databases.append(self)

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")

        self.overlay = Gtk.Overlay()
        self.parent_widget.add(self.overlay)

        database_action_overlay = self.builder.get_object("database_action_overlay")

        self.overlay.add_overlay(database_action_overlay)

        self.current_group = self.database_manager.get_root_group()

        self.stack = self.builder.get_object("list_stack")
        self.overlay.add(self.stack)
        self.overlay.show_all()

        self.set_headerbar()
        self.prepare_actions()

        self.show_page_of_new_directory(False)

    #
    # Headerbar
    #

    # Assemble headerbar
    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        lock_button = self.builder.get_object("lock_button")
        lock_button.connect("clicked", self.on_lock_button_clicked)

        mod_box = self.builder.get_object("mod_box")
        browser_buttons_box = self.builder.get_object("browser_buttons_box")
        mod_box.add(browser_buttons_box)

        add_entry_button = self.builder.get_object("add_entry_button")
        add_entry_button.connect("clicked", self.on_add_entry_button_clicked)

        add_group_button = self.builder.get_object("add_group_button")
        add_group_button.connect("clicked", self.on_add_group_button_clicked)

        add_property_button = self.builder.get_object("add_property_button")
        add_property_button.connect("clicked", self.on_add_property_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

        self.pathbar = Pathbar(self, self.database_manager, self.database_manager.get_root_group(), headerbar)

    # Group and entry browser headerbar
    def set_browser_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

        mod_box.add(self.builder.get_object("browser_buttons_box"))

    # Entry creation/editing page headerbar
    def set_entry_page_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

        mod_box.add(self.builder.get_object("entry_page_mod_box"))

    # Group creation/editing headerbar
    def set_group_edit_page_headerbar(self):
        mod_box = self.builder.get_object("mod_box")

        for child in mod_box.get_children():
            mod_box.remove(child)

    # Actions for MenuButton Popover
    def prepare_actions(self):
        delete_entry_action = Gio.SimpleAction.new("entry.delete", None)
        delete_entry_action.connect("activate", self.on_entry_delete_menu_button_clicked)
        self.window.application.add_action(delete_entry_action)

        edit_group_action = Gio.SimpleAction.new("group.edit", None)
        edit_group_action.connect("activate", self.on_group_edit_menu_button_clicked)
        self.window.application.add_action(edit_group_action)

        delete_group_action = Gio.SimpleAction.new("group.delete", None)
        delete_group_action.connect("activate", self.on_group_delete_menu_button_clicked)
        self.window.application.add_action(delete_group_action)

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self, edit_group):
        # First, remove stack pages which should not exist because they are scheduled for remove
        self.destroy_scheduled_stack_page()

        # Creation of group edit page
        if edit_group is True:
            self.destroy_scheduled_stack_page()

            builder = Gtk.Builder()
            builder.add_from_resource("/run/terminal/KeepassGtk/group_page.ui")

            scrolled_window = ScrolledPage(True)

            viewport = Gtk.Viewport()
            scrolled_window.properties_list_box = builder.get_object("properties_list_box")
            viewport.add(scrolled_window.properties_list_box)
            scrolled_window.add(viewport)
            scrolled_window.show_all()

            stack_page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
            if self.stack.get_child_by_name(stack_page_uuid) is not None:
                stack_page = self.stack.get_child_by_name(stack_page_uuid)
                stack_page.destroy()

            self.add_stack_page(scrolled_window)
            self.insert_group_properties_into_listbox(scrolled_window.properties_list_box)
            self.set_group_edit_page_headerbar()     
        # If the stack page with current group's uuid isn't existing - we need to create it (first time opening of group/entry)       
        elif self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is None and self.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group)) is None and edit_group is False:
            # Create not existing stack page for group
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/unlocked_database.ui")
                list_box = builder.get_object("list_box")
                list_box.connect("row-activated", self.on_list_box_row_activated)
                list_box.connect("row-selected", self.on_list_box_row_selected)

                scrolled_window = ScrolledPage(False)
                viewport = Gtk.Viewport()
                viewport.add(list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_groups_into_listbox(list_box)
                self.insert_entries_into_listbox(list_box)
            # Create not existing stack page for entry
            else:
                builder = Gtk.Builder()
                builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

                scrolled_window = ScrolledPage(True)

                viewport = Gtk.Viewport()
                scrolled_window.properties_list_box = builder.get_object("properties_list_box")
                viewport.add(scrolled_window.properties_list_box)
                scrolled_window.add(viewport)
                scrolled_window.show_all()

                self.add_stack_page(scrolled_window)
                self.insert_entry_properties_into_listbox(scrolled_window.properties_list_box, False)
        # Stack page with current group's uuid already exists, we only need to switch stack page
        else:
            # For group
            if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
                self.stack.set_visible_child_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
                self.set_browser_headerbar()
            # For entry
            else:
                self.stack.set_visible_child_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
                self.set_entry_page_headerbar()

    def add_stack_page(self, scrolled_window):
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            self.stack.add_named(scrolled_window, self.database_manager.get_group_uuid_from_group_object(self.current_group))
        else:
            self.stack.add_named(scrolled_window, self.database_manager.get_entry_uuid_from_entry_object(self.current_group))

        self.switch_stack_page()

    def switch_stack_page(self):
        page_uuid = NotImplemented

        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
            self.set_browser_headerbar()
        else:
            page_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
            self.set_entry_page_headerbar()

        if page_uuid in self.scheduled_page_destroy:
            stack_page = self.stack.get_child_by_name(page_uuid)

            if stack_page is not None:
                stack_page.destroy()
                
            self.scheduled_page_destroy.remove(page_uuid)
            self.show_page_of_new_directory(False)

        self.stack.set_visible_child_name(page_uuid)

    def update_current_stack_page(self):
        stack_page_name = self.database_manager.get_group_uuid_from_group_object(self.current_group)
        stack_page = self.stack.get_child_by_name(stack_page_name)
        stack_page.destroy()
        self.show_page_of_new_directory(False)

    def set_current_group(self, group):
        self.current_group = group

    def get_current_group(self):
        return self.current_group

    def schedule_stack_page_for_destroy(self, page_name):
        self.scheduled_page_destroy.append(page_name)

    def destroy_scheduled_stack_page(self):
        page_uuid = NotImplemented
        if self.database_manager.check_is_group(self.database_manager.get_group_uuid_from_group_object(self.current_group)) is True:
            page_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)
        else:
            page_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        if page_uuid in self.scheduled_page_destroy:
            stack_page_name = self.stack.get_child_by_name(page_uuid)
            if stack_page_name is not None:
                stack_page_name.destroy()
            self.scheduled_page_destroy.remove(page_uuid)

    #
    # Create Group & Entry Rows
    #

    def insert_groups_into_listbox(self, list_box):
        groups = NotImplemented

        if self.current_group.is_root_group:
            groups = self.database_manager.get_groups_in_root()
        else:
            groups = self.database_manager.get_groups_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))

        for group in groups:
            group_row = GroupRow(self, self.database_manager, group)
            list_box.add(group_row)

    def insert_entries_into_listbox(self, list_box):
        entries = self.database_manager.get_entries_in_folder(self.database_manager.get_group_uuid_from_group_object(self.current_group))

        for entry in entries:
            entry_row = EntryRow(self, self.database_manager, entry)
            list_box.add(entry_row)

    #
    # Create Property Rows
    #

    def insert_entry_properties_into_listbox(self, properties_list_box, add_all):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/entry_page.ui")

        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
        scrolled_page = self.stack.get_child_by_name(entry_uuid)

        if self.database_manager.has_entry_name(entry_uuid) is True or add_all is True:
            if scrolled_page.name_property_row is NotImplemented:
                scrolled_page.name_property_row = builder.get_object("name_property_row")
                scrolled_page.name_property_value_entry = builder.get_object("name_property_value_entry")
                value = self.database_manager.get_entry_name_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_name(entry_uuid) is True:
                    scrolled_page.name_property_value_entry.set_text(value)
                else:
                    scrolled_page.name_property_value_entry.set_text("")
                scrolled_page.name_property_value_entry.connect("changed", self.on_property_value_entry_changed, "name")
                properties_list_box.add(scrolled_page.name_property_row)
            elif scrolled_page.name_property_row is not "":
                value = self.database_manager.get_entry_name_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_name(entry_uuid) is True:
                    scrolled_page.name_property_value_entry.set_text(value)
                else:
                    scrolled_page.name_property_value_entry.set_text("")
                scrolled_page.name_property_value_entry.connect("changed", self.on_property_value_entry_changed, "name")
                properties_list_box.add(scrolled_page.name_property_row)

        if self.database_manager.has_entry_username(entry_uuid) is True or add_all is True:
            if scrolled_page.username_property_row is NotImplemented:
                scrolled_page.username_property_row = builder.get_object("username_property_row")
                scrolled_page.username_property_value_entry = builder.get_object("username_property_value_entry")
                value = self.database_manager.get_entry_username_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)
            elif scrolled_page.username_property_row is not "":
                value = self.database_manager.get_entry_username_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_username(entry_uuid) is True:
                    scrolled_page.username_property_value_entry.set_text(value)
                else:
                    scrolled_page.username_property_value_entry.set_text("")
                scrolled_page.username_property_value_entry.connect("changed", self.on_property_value_entry_changed, "username")
                properties_list_box.add(scrolled_page.username_property_row)

        if self.database_manager.has_entry_password(entry_uuid) is True or add_all is True:
            if scrolled_page.password_property_row is NotImplemented:
                scrolled_page.password_property_row = builder.get_object("password_property_row")
                scrolled_page.password_property_value_entry = builder.get_object("password_property_value_entry")
                value = self.database_manager.get_entry_password_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")
                properties_list_box.add(scrolled_page.password_property_row)
            elif scrolled_page.password_property_row is not "":
                value = self.database_manager.get_entry_password_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_password(entry_uuid) is True:
                    scrolled_page.password_property_value_entry.set_text(value)
                else:
                    scrolled_page.password_property_value_entry.set_text("")
                scrolled_page.password_property_value_entry.connect("changed", self.on_property_value_entry_changed, "password")
                properties_list_box.add(scrolled_page.password_property_row)

        if self.database_manager.has_entry_url(entry_uuid) is True or add_all is True:
            if scrolled_page.url_property_row is NotImplemented:
                scrolled_page.url_property_row = builder.get_object("url_property_row")
                scrolled_page.url_property_value_entry = builder.get_object("url_property_value_entry")
                value = self.database_manager.get_entry_url_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)
            elif scrolled_page.url_property_row is not "":
                value = self.database_manager.get_entry_url_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_url(entry_uuid) is True:
                    scrolled_page.url_property_value_entry.set_text(value)
                else:
                    scrolled_page.url_property_value_entry.set_text("")
                scrolled_page.url_property_value_entry.connect("changed", self.on_property_value_entry_changed, "url")
                properties_list_box.add(scrolled_page.url_property_row)

        if self.database_manager.has_entry_notes(entry_uuid) is True or add_all is True:
            if scrolled_page.notes_property_row is NotImplemented:
                scrolled_page.notes_property_row = builder.get_object("notes_property_row")
                scrolled_page.notes_property_value_entry = builder.get_object("notes_property_value_entry")
                value = self.database_manager.get_entry_notes_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_notes(entry_uuid) is True:
                    scrolled_page.notes_property_value_entry.set_text(value)
                else:
                    scrolled_page.notes_property_value_entry.set_text("")
                scrolled_page.notes_property_value_entry.connect("changed", self.on_property_value_entry_changed, "notes")
                properties_list_box.add(scrolled_page.notes_property_row)
            elif scrolled_page.notes_property_row is not "":
                value = self.database_manager.get_entry_notes_from_entry_uuid(entry_uuid)
                if self.database_manager.has_entry_notes(entry_uuid) is True:
                    scrolled_page.notes_property_value_entry.set_text(value)
                else:
                    scrolled_page.notes_property_value_entry.set_text("")
                scrolled_page.notes_property_value_entry.connect("changed", self.on_property_value_entry_changed, "notes")
                properties_list_box.add(scrolled_page.notes_property_row)

    def insert_group_properties_into_listbox(self, properties_list_box):
        group_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)

        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/group_page.ui")

        name_property_row = builder.get_object("name_property_row")
        name_property_value_entry = builder.get_object("name_property_value_entry")
        name_property_value_entry.connect("changed", self.on_property_value_group_changed, "name")

        notes_property_row = builder.get_object("notes_property_row")
        notes_property_value_entry = builder.get_object("notes_property_value_entry")
        notes_property_value_entry.connect("changed", self.on_property_value_group_changed, "notes")

        name_value = self.database_manager.get_group_name_from_uuid(group_uuid)
        notes_value = self.database_manager.get_group_notes_from_group_uuid(group_uuid)

        if self.database_manager.has_group_name(group_uuid) is True:
            name_property_value_entry.set_text(name_value)
        else:
            name_property_value_entry.set_text("")

        if self.database_manager.has_group_notes(group_uuid) is True:
            notes_property_value_entry.set_text(notes_value)
        else:
            notes_property_value_entry.set_text("")

        properties_list_box.add(name_property_row)
        properties_list_box.add(notes_property_row)

    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        if list_box_row.get_type() == "EntryRow":
            self.set_current_group(self.database_manager.get_entry_object_from_uuid(list_box_row.get_entry_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_entry_uuid())
            self.show_page_of_new_directory(False)
        elif list_box_row.get_type() == "GroupRow":
            self.set_current_group(self.database_manager.get_group_object_from_uuid(list_box_row.get_group_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_group_uuid())
            self.show_page_of_new_directory(False)

    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug(list_box_row.get_label() + " selected")

    def on_save_button_clicked(self, widget):
        self.database_manager.save_database()
        self.show_database_action_revealer("Database saved")

    def on_lock_button_clicked(self, widget):
        if self.database_manager.made_database_changes is True:
            self.show_save_dialog()
        else:
            self.lock_database()

    def on_save_dialog_save_button_clicked(self, widget, save_dialog):
        self.database_manager.save_database()
        save_dialog.destroy()

    def on_save_dialog_discard_button_clicked(self, widget, save_dialog):
        save_dialog.destroy()

    def on_add_entry_button_clicked(self, widget):
        self.database_manager.changes = True
        entry = self.database_manager.add_entry_to_database("", "", "", "", "", "0", self.database_manager.get_group_uuid_from_group_object(self.current_group))
        self.current_group = entry
        self.pathbar.add_pathbar_button_to_pathbar(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
        self.show_page_of_new_directory(False)

        self.show_database_action_revealer("Added Entry")

    def on_add_group_button_clicked(self, widget):
        self.database_manager.changes = True
        group = self.database_manager.add_group_to_database("", "0", "", self.current_group)
        self.current_group = group
        self.pathbar.add_pathbar_button_to_pathbar(self.database_manager.get_group_uuid_from_group_object(self.current_group))
        self.show_page_of_new_directory(True)

        self.show_database_action_revealer("Added Group")

    def on_add_property_button_clicked(self, widget):
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)
        scrolled_page = self.stack.get_child_by_name(entry_uuid)

        for row in scrolled_page.properties_list_box.get_children():
            scrolled_page.properties_list_box.remove(row)

        self.insert_entry_properties_into_listbox(scrolled_page.properties_list_box, True)

    def on_property_value_entry_changed(self, widget, type):
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.current_group)

        scrolled_page = self.stack.get_child_by_name(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
        scrolled_page.set_made_database_changes(True)

        if type == "name":
            self.database_manager.set_entry_name(entry_uuid, widget.get_text())

            pathbar_button = self.pathbar.get_pathbar_button(self.database_manager.get_entry_uuid_from_entry_object(self.current_group))
            pathbar_button.set_label(widget.get_text())

        elif type == "username":
            self.database_manager.set_entry_username(entry_uuid, widget.get_text())
        elif type == "password":
            self.database_manager.set_entry_password(entry_uuid, widget.get_text())
        elif type == "url":
            self.database_manager.set_entry_url(entry_uuid, widget.get_text())
        elif type == "notes":
            self.database_manager.set_entry_notes(entry_uuid, widget.get_text())

    def on_property_value_group_changed(self, widget, type):
        group_uuid = self.database_manager.get_group_uuid_from_group_object(self.current_group)

        scrolled_page = self.stack.get_child_by_name(self.database_manager.get_group_uuid_from_group_object(self.current_group))
        scrolled_page.set_made_database_changes(True)

        if type == "name":
            self.database_manager.set_group_name(group_uuid, widget.get_text())

            for pathbar_button in self.pathbar.get_children():
                if pathbar_button.get_name() == "PathbarButtonDynamic":
                    if pathbar_button.get_uuid() == self.database_manager.get_group_uuid_from_group_object(self.current_group):
                        pathbar_button.set_label(widget.get_text())
        elif type == "notes":
            self.database_manager.set_group_notes(group_uuid, widget.get_text())

    def on_entry_row_button_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.entry_marked_for_delete = self.database_manager.get_entry_object_from_uuid(widget.get_parent().get_entry_uuid())
            entry_context_popover = self.builder.get_object("entry_context_popover")
            entry_context_popover.set_relative_to(widget)
            entry_context_popover.show_all()
            entry_context_popover.popup()

    def on_entry_delete_menu_button_clicked(self, action, param):
        entry_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.entry_marked_for_delete)

        # If the deleted entry is in the pathbar, we need to rebuild the pathbar
        if self.pathbar.is_pathbar_button_in_pathbar(entry_uuid) is True:
            self.pathbar.rebuild_pathbar(self.current_group)

        self.database_manager.delete_entry_from_database(self.entry_marked_for_delete)
        self.update_current_stack_page()

    def on_group_row_button_pressed(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.group_marked_for_delete = self.database_manager.get_group_object_from_uuid(widget.get_parent().get_group_uuid())
            self.group_marked_for_edit = self.database_manager.get_group_object_from_uuid(widget.get_parent().get_group_uuid())
            group_context_popover = self.builder.get_object("group_context_popover")
            group_context_popover.set_relative_to(widget)
            group_context_popover.show_all()
            group_context_popover.popup()

    def on_group_delete_menu_button_clicked(self, action, param):
        group_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.group_marked_for_delete)

        # If the deleted group is in the pathbar, we need to rebuild the pathbar
        if self.pathbar.is_pathbar_button_in_pathbar(group_uuid) is True:
            self.pathbar.rebuild_pathbar(self.current_group)

        self.database_manager.delete_group_from_database(self.group_marked_for_delete)
        self.update_current_stack_page()

    def on_group_edit_menu_button_clicked(self, action, param):
        group_uuid = self.database_manager.get_entry_uuid_from_entry_object(self.group_marked_for_edit)

        self.set_current_group(self.group_marked_for_edit)
        self.pathbar.add_pathbar_button_to_pathbar(group_uuid)
        self.show_page_of_new_directory(True)

    #
    # Dialog Creator
    #

    def show_save_dialog(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/run/terminal/KeepassGtk/save_dialog.ui")

        save_dialog = builder.get_object("save_dialog")
        save_dialog.set_destroy_with_parent(True)
        save_dialog.set_modal(True)
        save_dialog.set_transient_for(self.window)

        discard_button = builder.get_object("discard_button")
        save_button = builder.get_object("save_button")

        discard_button.connect("clicked", self.on_save_dialog_discard_button_clicked, save_dialog)
        save_button.connect("clicked", self.on_save_dialog_save_button_clicked, save_dialog)

        save_dialog.present()

    def show_database_action_revealer(self, message):
        database_action_box = self.builder.get_object("database_action_box")
        context = database_action_box.get_style_context()
        context.add_class('NotifyRevealer')

        database_action_label = self.builder.get_object("database_action_label")
        database_action_label.set_text(message)

        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())
        revealer_timer = threading.Timer(3.0, self.hide_database_action_revealer)
        revealer_timer.start()

    def hide_database_action_revealer(self):
        database_action_revealer = self.builder.get_object("database_action_revealer")
        database_action_revealer.set_reveal_child(not database_action_revealer.get_reveal_child())

    def lock_database(self):
        self.window.opened_databases.remove(self)
        self.window.close_tab(self.parent_widget)
        self.window.start_database_opening_routine(ntpath.basename(self.database_manager.database_path), self.database_manager.database_path)
