from gi.repository import Gtk


class ContainerPage(Gtk.Box):
    development_mode = NotImplemented
    headerbar = NotImplemented

    def __init__(self, headerbar, development_mode):
        Gtk.Box.__init__(self, spacing=1)
        self.show_all()
        self.development_mode = development_mode
        self.headerbar = headerbar

    def set_headerbar(self, headerbar):
        self.headerbar = headerbar

        if self.development_mode is True:
            context = self.headerbar.get_style_context()
            context.add_class("devel")

    def get_headerbar(self):
        return self.headerbar
