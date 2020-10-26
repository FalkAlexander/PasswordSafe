from gi.repository import Gtk


class PathbarButton(Gtk.Button):
    uuid = NotImplemented
    is_group = NotImplemented

    def __init__(self, uuid):
        Gtk.Button.__init__(self)
        self.set_name("PathbarButtonDynamic")
        self.uuid = uuid

    def set_is_group(self):
        self.is_group = True

    def set_is_entry(self):
        self.is_group = False

    def get_is_group(self):
        return self.is_group

    def get_uuid(self):
        return self.uuid
