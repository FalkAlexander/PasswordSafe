import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import database_opening_gui
from database_opening_gui import DatabaseOpeningGui

class DatabaseCreationSuccessGui:

    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    keepass_loader = NotImplemented
    stack = NotImplemented

    def __init__(self, window, widget, kpl):
        self.window = window
        self.parent_widget = widget
        self.keepass_loader = kpl
        self.success_page()

    #
    # Stack Pages
    #

    def success_page(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/create_database_success.ui")

        self.stack = self.builder.get_object("database_creation_success_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
        self.parent_widget.add(self.stack)

        finish_button = self.builder.get_object("finish_button")
        finish_button.connect("clicked", self.on_finish_button_clicked)
        
        self.set_headerbar()

    #
    # Events
    #

    def on_finish_button_clicked(self, widget):
        self.stack.destroy()
        DatabaseOpeningGui(self.window, self.parent_widget, self.keepass_loader.database_path)

    #
    # Headerbar
    #
    
    def set_headerbar(self):
        headerbar = self.window.get_headerbar()
        self.parent_widget.set_headerbar(headerbar)
        self.window.set_headerbar()
