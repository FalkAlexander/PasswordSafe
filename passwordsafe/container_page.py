# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk


class ContainerPage(Gtk.Box):
    def __init__(self, headerbar, development_mode):
        super().__init__()

        self.show_all()
        self.development_mode = development_mode
        self.headerbar = headerbar
        self.set_name("BGPlatform")

    def set_headerbar(self, headerbar):
        self.headerbar = headerbar

        if self.development_mode is True:
            context = self.headerbar.get_style_context()
            context.add_class("devel")
