import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

class PathbarButton(Gtk.Button):
    is_group = NotImplemented
    complete_path = NotImplemented

    def __init__(self, path):
        Gtk.Button.__init__(self)
        self.set_name("PathbarButton")
        self.complete_path = path

    def set_complete_path(self, path):
        self.complete_path = path

    def get_complete_path(self):
        return self.complete_path

    def set_is_group(self, boolean):
        self.is_group = boolean

    def check_if_group(self):
        return self.is_group
