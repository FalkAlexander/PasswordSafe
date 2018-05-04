import gi
import pykeepass
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

class DatabaseCreationSuccessGui:

    builder = NotImplemented
    parent_widget = NotImplemented
    stack = NotImplemented

    def __init__(self, widget):
        self.parent_widget = widget
        self.success_page()

    def success_page(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/create_database_success.ui")

        self.stack = self.builder.get_object("database_creation_success_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
        self.parent_widget.add(self.stack)
