# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import GObject, Gtk, Handy


class UnlockedHeaderBar(Handy.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    def __new__(cls, unlocked_database):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_headerbar.ui")

        new_object = builder.get_object("headerbar")
        new_object.finish_initializing(builder, unlocked_database)
        return new_object

    def finish_initializing(self, builder, unlocked_database):
        self.builder = builder
        self._unlocked_database = unlocked_database

        self._selection_button_box = self.builder.get_object(
            "selection_button_box")
        self._unlocked_database.bind_property(
            "selection-mode", self._selection_button_box, "visible",
            GObject.BindingFlags.SYNC_CREATE)
