import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

class ContainerPage(Gtk.Box):
    text = ""

    def __init__(self, info):
        Gtk.Box.__init__(self, spacing=1)
        self.show_all()
        self.text = info

    def get_instance_text(self):
        return self.text
