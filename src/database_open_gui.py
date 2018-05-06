import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import database 
from database import KeepassLoader

class DatabaseOpenGui:

    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    stack = NotImplemented
    keepass_loader = NotImplemented

    def __init__(self, window, widget, keepass_loader):
        self.window = window
        self.parent_widget = widget
        self.keepass_loader = keepass_loader
        self.assemble_listbox()

    def assemble_listbox(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/entries_listbox.ui")

        self.stack = self.builder.get_object("list_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("0"))
        self.parent_widget.add(self.stack)
        
        self.set_headerbar()

        self.insert_groups_in_listbox()

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")

        file_open_button = self.builder.get_object("open_button")
        file_open_button.connect("clicked", self.window.open_filechooser)

        file_new_button = self.builder.get_object("new_button")
        file_new_button.connect("clicked", self.window.create_filechooser)

        self.parent_widget.set_headerbar(headerbar)
        self.window.set_titlebar(headerbar)

    # Example
    def insert_groups_in_listbox(self):
        list_box = self.builder.get_object("list_box")

        group = self.keepass_loader.kp.root_group
        for entry in group.entries:
            builder = Gtk.Builder()
            builder.add_from_file("ui/entries_listbox.ui")
            entry_row = builder.get_object("entry_row")

            name_label = builder.get_object("name_label")
            subtitle_label = builder.get_object("subtitle_label")
            password_input = builder.get_object("password_input")

            name_label.set_text(entry.title)
            subtitle_label.set_text(entry.url)
            password_input.set_text(entry.password)

            list_box.add(entry_row)





