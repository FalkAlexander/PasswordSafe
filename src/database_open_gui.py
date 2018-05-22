import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
import database 
from database import KeepassLoader
import logging_manager
from logging_manager import LoggingManager
import find_widget
import pathbar
from pathbar import Pathbar

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
        self.stack.add_named(list_box, self.keepass_loader.get_group_name_from_group_object(self.current_group))
        self.stack.set_visible_child_name(self.keepass_loader.get_group_name_from_group_object(self.current_group))

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
            builder = Gtk.Builder()
            builder.add_from_file("ui/entries_listbox.ui")
            group_row = builder.get_object("group_row")

            group_name_label = builder.get_object("group_name_label")
            group_name_label.set_text(self.keepass_loader.get_group_name_from_group_object(group))

            list_box.add(group_row)


    def insert_entries_into_listbox(self, list_box):
        entries = self.keepass_loader.get_entries_in_folder(self.keepass_loader.get_group_uuid_from_group_object(self.current_group))
        print(str(entries))
        for entry in entries:
            builder = Gtk.Builder()
            builder.add_from_file("ui/entries_listbox.ui")
            entry_row = builder.get_object("entry_row")

            entry_name_label = builder.get_object("entry_name_label")
            entry_subtitle_label = builder.get_object("entry_subtitle_label")
            entry_password_input = builder.get_object("entry_password_input")

            entry_name_label.set_text(self.keepass_loader.get_entry_name_from_entry_object(entry))
            entry_subtitle_label.set_text(self.keepass_loader.get_entry_username_from_entry_object(entry))
            entry_password_input.set_text(self.keepass_loader.get_entry_password_from_entry_object(entry))

            list_box.add(entry_row)


    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        self.logging_manager.log_debug("activated")
        #group_name = find_widget.get_child_by_name(list_box_row, "name_label").get_text()
        #self.set_current_path(group_name)


    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug("selected")


    def on_save_button_clicked(self, widget):
        self.keepass_loader.save()
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_debug("Database has been saved")
