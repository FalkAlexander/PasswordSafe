import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
import database 
from database import KeepassLoader
import logging_manager
from logging_manager import LoggingManager
import find_widget

class DatabaseOpenGui:

    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    stack = NotImplemented
    keepass_loader = NotImplemented
    logging_manager = NotImplemented
    current_path = "/"

    def __init__(self, window, widget, keepass_loader):
        self.window = window
        self.parent_widget = widget
        self.keepass_loader = keepass_loader
        self.assemble_listbox()
        self.pathbar_box

    #
    # Stack Pages
    #

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/entries_listbox.ui")

        scrolled_window = self.builder.get_object("scrolled_window")
        self.parent_widget.add(scrolled_window)

        self.stack = self.builder.get_object("list_stack")

        self.change_directory()
        
        self.set_headerbar()

    #
    # Headerbar
    #

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        #modelbutton = self.builder.get_object("menu_modelbutton_new")
        #popover = self.builder.get_object("menubutton_popover")

        #action = Gio.SimpleAction.new("new", None)
        #action.connect("activate", self.window.create_filechooser)
        #popover.bind_model(modelbutton, "app.new")
        #headerbar.add_action(action)

        #file_open_button = self.builder.get_object("menu_modelbutton_open")
        #file_open_button.connect("clicked", self.window.open_filechooser)

        #file_new_button = self.builder.get_object("menu_modelbutton_new")
        #file_new_button.connect("clicked", self.window.create_filechooser)

        save_button = self.builder.get_object("save_button")
        save_button.connect("clicked", self.on_save_button_clicked)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)
        self.assemble_pathbar(headerbar)

    #
    # Group and Entry Management
    #

    def assemble_pathbar(self, headerbar):
        self.pathbar_box = self.builder.get_object("pathbar_box")

        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        self.pathbar_box.pack_start(seperator_label, True, True, 0)
        self.pathbar_box.show_all()


    def add_directory_button_to_pathbar(self, name):
        self.pathbar_box.pack_end(self.directory_button(name), True, True, 0)
        seperator_label = Gtk.Label()
        seperator_label.set_text("/")
        self.pathbar_box.pack_end(seperator_label, True, True, 0)
        self.pathbar_box.show_all()


    def directory_button(self, directory_name):
        button = Gtk.Button()
        button.set_label(directory_name)
        button.set_relief(Gtk.ReliefStyle.NONE)

        return button


    def set_current_path(self, group_name):
        if self.current_path == "/":
            self.current_path = "/" + group_name + "/"
            self.add_directory_button_to_pathbar(group_name)
        else:
            self.current_path = self.current_path + group_name + "/"
            self.add_directory_button_to_pathbar(group_name)
        
        self.logging_manager.log_debug("current path is: " + self.current_path)
        self.change_directory()


    def change_directory(self):
        builder = Gtk.Builder()
        builder.add_from_file("ui/entries_listbox.ui")
        list_box = builder.get_object("list_box")
        list_box.connect("row-activated", self.on_list_box_row_activated)
        list_box.connect("row-selected", self.on_list_box_row_selected)

        self.add_stack_page(list_box)
        self.insert_groups_in_listbox(list_box)
        self.insert_entries_in_listbox(list_box)


    def add_stack_page(self, list_box):
        self.stack.add_named(list_box, self.current_path)
        self.stack.set_visible_child_name(self.current_path)


    def insert_groups_in_listbox(self, list_box):
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_warn(self.current_path)
        groups = self.keepass_loader.get_groups()
        for group in groups:
            if group.get_parent_group_path() == self.current_path:
                builder = Gtk.Builder()
                builder.add_from_file("ui/entries_listbox.ui")
                group_row = builder.get_object("group_row")

                group_name_label = builder.get_object("group_name_label")
                group_name_label.set_text(group.get_name())

                list_box.add(group_row)


    def insert_entries_in_listbox(self, list_box):
        entries = self.keepass_loader.get_entries(self.current_path)
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

            list_box.add(entry_row)

    #
    # Events
    #

    def on_list_box_row_activated(self, widget, list_box_row):
        group_name = find_widget.get_child_by_name(list_box_row, "name_label").get_text()
        self.set_current_path(group_name)


    def on_list_box_row_selected(self, widget, list_box_row):
        self.logging_manager.log_debug("selected")


    def on_save_button_clicked(self, widget):
        self.keepass_loader.save()
        self.logging_manager = LoggingManager(True)
        self.logging_manager.log_debug("Database has been saved")
