# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


class ScrolledPage(Gtk.ScrolledWindow):
    edit_page = False

    def __init__(self, edit):
        Gtk.ScrolledWindow.__init__(self)
        self.set_name("ScrolledPage")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.edit_page = edit
