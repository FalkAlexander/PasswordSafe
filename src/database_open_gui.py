import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
import database 
from database import KeepassLoader
import logging_manager
from logging_manager import LoggingManager
import pathbar
from pathbar import Pathbar
import entry_row
from entry_row import EntryRow
import group_row
from group_row import GroupRow


class DatabaseOpenGui:

    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    stack = NotImplemented
    keepass_loader = NotImplemented
    logging_manager = NotImplemented
    current_group = NotImplemented
    pathbar = NotImplemented

    def __init__(self, window, widget, keepass_loader):
        self.window = window
        self.parent_widget = widget
        self.keepass_loader = keepass_loader
        self.assemble_listbox()
        self.logging_manager = LoggingManager(True)

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.current_group = self.keepass_loader.get_root_group()

        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/entries_listbox.ui")

        scrolled_window = self.builder.get_object("scrolled_window")
        self.parent_widget.add(scrolled_window)

        self.stack = self.builder.get_object("list_stack")

        self.set_headerbar()

        self.show_page_of_new_directory()

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

        self.pathbar = Pathbar(self, self.keepass_loader, self.keepass_loader.get_root_group(), headerbar)

    #
    # Group and Entry Management
    #

    def show_page_of_new_directory(self):
        builder = Gtk.Builder()
        builder.add_from_file("ui/entries_listbox.ui")
        list_box = builder.get_object("list_box")
        list_box.connect("row-activated", self.on_list_box_row_activated)
        list_box.connect("row-selected", self.on_list_box_row_selected)

        self.add_stack_page(list_box)
        self.insert_groups_into_listbox(list_box)
        self.insert_entries_into_listbox(list_box)


    def add_stack_page(self, list_box):
        print(str(self.current_group))
        self.stack.add_named(list_box, self.keepass_loader.get_group_uuid_from_group_object(self.current_group))
        self.switch_stack_page()
        
    def switch_stack_page(self):
        self.stack.set_visible_child_name(self.keepass_loader.get_group_uuid_from_group_object(self.current_group))

    def set_current_group(self, group):
        self.current_group = group


    #
    # Create Group & Entry Rows
    #

    def insert_groups_into_listbox(self, list_box):
        groups = NotImplemented

        if self.current_group.is_root_group:
            groups = self.keepass_loader.get_groups_in_root()
        else:
            groups = self.keepass_loader.get_groups_in_folder(self.keepass_loader.get_group_uuid_from_group_object(self.current_group))
        
        for group in groups:
            group_row = GroupRow(self.keepass_loader, group)
            list_box.add(group_row)


    def insert_entries_into_listbox(self, list_box):        
        entries = self.keepass_loader.get_entries_in_folder(self.keepass_loader.get_group_uuid_from_group_object(self.current_group))
        
        for entry in entries:
            entry_row = EntryRow(self.keepass_loader, entry)
            list_box.add(entry_row)


    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        if list_box_row.get_type() == "EntryRow":
            print(list_box_row.get_label())
        elif list_box_row.get_type() == "GroupRow":
            self.set_current_group(self.keepass_loader.get_group_object_from_uuid(list_box_row.get_group_uuid()))
            self.pathbar.add_pathbar_button_to_pathbar(list_box_row.get_group_uuid())
            self.show_page_of_new_directory()


    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug("selected")


    def on_save_button_clicked(self, widget):
        self.keepass_loader.save()
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_debug("Database has been saved")
