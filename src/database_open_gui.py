import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import database 
from database import KeepassLoader
import logging_manager
from logging_manager import LoggingManager

class DatabaseOpenGui:

    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    stack = NotImplemented
    keepass_loader = NotImplemented
    logging_manager

    def __init__(self, window, widget, keepass_loader):
        self.window = window
        self.parent_widget = widget
        self.keepass_loader = keepass_loader
        self.assemble_listbox()

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/entries_listbox.ui")

        self.stack = self.builder.get_object("list_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("0"))
        self.parent_widget.add(self.stack)
        
        self.set_headerbar()

        self.insert_groups_in_listbox("/")
    
    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")

        file_open_button = self.builder.get_object("open_button")
        file_open_button.connect("clicked", self.window.open_filechooser)

        file_new_button = self.builder.get_object("new_button")
        file_new_button.connect("clicked", self.window.create_filechooser)

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

    #
    # Group and Entry Management
    #

    def insert_groups_in_listbox(self, path):
        list_box = self.builder.get_object("list_box")

        groups = self.keepass_loader.get_groups()
        for group in groups:
            if group.get_group_path() == path:
                builder = Gtk.Builder()
                builder.add_from_file("ui/entries_listbox.ui")
                group_row = builder.get_object("group_row")

                group_label = builder.get_object("group_label")

                group_label.set_text(group.get_name())

                if group.get_group_path() != "/":
                    list_box.add(group_row)
                
                self.insert_entries_in_listbox(path)


    def insert_entries_in_listbox(self, group_path):
        list_box = self.builder.get_object("list_box")

        entries = self.keepass_loader.get_entries(group_path)
        for entry in entries:
            builder = Gtk.Builder()
            builder.add_from_file("ui/entries_listbox.ui")
            entry_row = builder.get_object("entry_row")

            name_label = builder.get_object("name_label")
            subtitle_label = builder.get_object("subtitle_label")
            password_input = builder.get_object("password_input")

            name_label.set_text(entry.get_entry_name())
            subtitle_label.set_text(entry.get_username())
            password_input.set_text(entry.get_password())

            list_box.add(entry_row)


    def on_save_button_clicked(self, widget):
        self.keepass_loader.save()
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_debug("Database has been saved")




