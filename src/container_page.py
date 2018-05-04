import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

class ContainerPage(Gtk.Box):
    notebook = NotImplemented
    page = NotImplemented

    def __init__(self, container):
        self.notebook = container
        self.page = Gtk.Box()
        self.add_child(self.page)

    def add_child(self, page):
        self.notebook.add(page)
