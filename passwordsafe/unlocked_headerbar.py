# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk, Handy


class UnlockedHeaderBar(Handy.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    def __new__(cls):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_headerbar.ui")

        new_object = builder.get_object("headerbar")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        self.builder = builder
