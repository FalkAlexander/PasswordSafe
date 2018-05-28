from gi.repository import Gtk
import gi
gi.require_version('Gtk', '3.0')


class ContainerPage(Gtk.Box):
    headerbar = NotImplemented

    def __init__(self, headerbar):
        Gtk.Box.__init__(self, spacing=1)
        self.show_all()
        self.headerbar = headerbar

    def set_headerbar(self, headerbar):
        self.headerbar = headerbar

    def get_headerbar(self):
        return self.headerbar
