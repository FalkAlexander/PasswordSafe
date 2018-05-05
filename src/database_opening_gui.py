import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import database
from database import KeepassLoader
import database_creation_success_gui
from database_creation_success_gui import DatabaseCreationSuccessGui

class DatabaseOpeningGui:
    builder = NotImplemented
    parent_widget = NotImplemented
    window = NotImplemented
    switched = False
    database_filepath = NotImplemented
    keepass_loader = NotImplemented

    def __init__(self, window, widget, filepath):
        self.window = window
        self.parent_widget = widget
        self.database_filepath = filepath
        self.unlock_database()
 
    def unlock_database(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/unlock_database.ui")

        self.set_headerbar()

        self.stack = self.builder.get_object("database_unlock_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))

        switch_to_keyfile_button = self.builder.get_object("switch_to_keyfile_button1")
        switch_to_keyfile_button.connect("clicked", self.on_switch_to_keyfile_button_clicked)

        switch_to_password_button = self.builder.get_object("switch_to_password_button2")
        switch_to_password_button.connect("clicked", self.on_switch_to_password_button_clicked)

        unlock_database_button = self.builder.get_object("password_unlock_button")
        unlock_database_button.connect("clicked", self.on_unlock_database_button_clicked)

        password_unlock_input = self.builder.get_object("password_unlock_input")
        password_unlock_input.connect("activate", self.on_unlock_database_button_clicked)
        password_unlock_input.connect("icon-press", self.on_unlock_input_secondary_clicked)
        #entry = Gtk.Entry()

        self.parent_widget.add(self.stack)

    def set_headerbar(self):
        headerbar = self.builder.get_object("headerbar")
        self.window.set_titlebar(headerbar)
        self.parent_widget.set_headerbar(headerbar)
        back_button = self.builder.get_object("back_button")
        back_button.connect("clicked", self.on_headerbar_back_button_clicked)

    def on_unlock_input_secondary_clicked(self, widget, position, eventbutton):
        if widget.get_visibility():
            widget.set_invisible_char("●")
            widget.set_visibility(False)
        else:
            widget.set_visibility(True)

    def on_headerbar_back_button_clicked(self, widget):
        self.window.close_tab(self.parent_widget)
        self.window.set_headerbar()

    def on_switch_to_keyfile_button_clicked(self, widget):
        self.stack.set_visible_child(self.stack.get_child_by_name("page1"))

    def on_switch_to_password_button_clicked(self, widget):
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))


    def on_unlock_database_button_clicked(self, widget):
        password_unlock_input = self.builder.get_object("password_unlock_input")

        if password_unlock_input.get_text() != "":
            try:
                self.keepass_loader = KeepassLoader(self.database_filepath, password_unlock_input.get_text())
                self.success_page()
                print("DEBUG: opening of database was successfull")
        
            #OSError:master key invalid
            except(OSError): 
                password_unlock_input.grab_focus()
                password_unlock_input.get_style_context().add_class("error")
                self.clear_input_fields()
                print("DEBUG: couldn't open database, wrong password")


    #when we have the database view page finished, it is shown here
    def success_page(self):
        self.clear_input_fields()
        self.parent_widget.remove(self.stack)
        DatabaseCreationSuccessGui(self.window, self.parent_widget)

    def clear_input_fields(self):
        password_unlock_input = self.builder.get_object("password_unlock_input")
        password_unlock_input.set_text("")
