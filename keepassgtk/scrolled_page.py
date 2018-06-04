from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class ScrolledPage(Gtk.ScrolledWindow):
    edit_page = False
    made_database_changes = False

    def __init__(self, edit):
        Gtk.ScrolledWindow.__init__(self)
        self.set_name("ScrolledPage")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.edit_page = edit

    def check_is_edit_page(self):
        return self.edit_page

    def get_made_database_changes(self):
        return self.made_database_changes

    def set_made_database_changes(self, bool):
        self.made_database_changes = bool
