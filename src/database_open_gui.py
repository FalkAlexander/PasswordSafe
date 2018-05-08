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
    logging_manager = NotImplemented
    list_box = NotImplemented

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

        scrolled_window = self.builder.get_object("scrolled_window")
        self.parent_widget.add(scrolled_window)

        self.stack = self.builder.get_object("list_stack")
        #scrolled_window.add(self.stack)
        #self.stack.add(scrolled_window)

        self.list_box = self.builder.get_object("list_box")
        self.list_box.connect("row-activated", self.on_list_box_row_activated)
        self.list_box.connect("row-selected", self.on_list_box_row_selected)
        frame = self.builder.get_object("frame")
        frame.add(self.stack)
        self.stack.add(self.list_box)
        self.stack.set_visible_child(self.stack.get_child_by_name("0"))
        
        self.set_headerbar()

        self.inital_groups_insert_in_listbox()
        self.initial_entries_insert_in_listbox()

        #frame.show_all()
    
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

    def inital_groups_insert_in_listbox(self):
        self.logging_manager = LoggingManager(True)
        groups = self.keepass_loader.get_groups()
        for group in groups:
            if group.get_parent_group_path() == "/":
                builder = Gtk.Builder()
                builder.add_from_file("ui/entries_listbox.ui")
                group_row = builder.get_object("group_row")

                group_name_label = builder.get_object("group_name_label")
                group_name_label.set_text(group.get_group_path())
                self.logging_manager.log_debug("group path to be shown is: " + group.get_group_path())

                self.list_box.add(group_row)


    def initial_entries_insert_in_listbox(self):
        entries = self.keepass_loader.get_entries("/")
        for entry in entries:
            builder = Gtk.Builder()
            builder.add_from_file("ui/entries_listbox.ui")
            entry_row = builder.get_object("entry_row")

            entry_name_label = builder.get_object("entry_name_label")
            entry_subtitle_label = builder.get_object("entry_subtitle_label")
            entry_password_input = builder.get_object("entry_password_input")

            entry_name_label.set_text(entry.get_entry_name())
            entry_subtitle_label.set_text(entry.get_username())
            entry_password_input.set_text(entry.get_password())

            self.list_box.add(entry_row)

    def on_list_box_row_activated(self, widget, list_box_row):
        self.logging_manager.log_debug("activated")
        
        lbr = Gtk.ListBoxRow()
        lbr.get_path_for_child

        list_box_row_child = list_box_row.get_child()
        entry_box_children = list_box_row_child.get_children()
        self.logging_manager.log_error(str(entry_box_children))
        #group_name_label = self.get_child_by_name(entry_box_children, "group_name_label")
        #entry_name_label = self.get_child_by_name(entry_box_children, "entry_name_label")
        #if group_name_label is None:
        #    print(entry_name_label.get_text())
        #else:
        #    print(group_name_label.get_text())
        



    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug("selected")


    def on_save_button_clicked(self, widget):
        self.keepass_loader.save()
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_debug("Database has been saved")


    #
    # Helper Functions
    #

    def get_child_by_name(self, children, name):
        for widget in children:
            if widget.get_name() == name:
                return widget

