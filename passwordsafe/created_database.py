# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gtk
from passwordsafe.unlock_database import UnlockDatabase


class CreatedDatabase:
    builder = NotImplemented
    window = NotImplemented
    parent_widget = NotImplemented
    database_manager = NotImplemented
    stack = NotImplemented

    def __init__(self, window, widget, dbm):
        self.window = window
        self.parent_widget = widget
        self.database_manager = dbm
        self.success_page()

    #
    # Stack Pages
    #

    def success_page(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource(
            "/org/gnome/PasswordSafe/created_database.ui")

        self.stack = self.builder.get_object("database_creation_success_stack")
        self.stack.set_visible_child(self.stack.get_child_by_name("page0"))
        self.parent_widget.add(self.stack)

        finish_button = self.builder.get_object("finish_button")
        finish_button.connect("clicked", self.on_finish_button_clicked)

    #
    # Events
    #

    def on_finish_button_clicked(self, _widget):
        self.stack.destroy()
        UnlockDatabase(
            self.window, self.parent_widget,
            self.database_manager.database_path)
