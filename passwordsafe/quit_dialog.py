# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import os

from gi.repository import Gio, Gtk


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/quit_dialog.ui")
class QuitDialog(Gtk.MessageDialog):

    __gtype_name__ = "QuitDialog"

    unsaved_databases_list_box = Gtk.Template.Child()

    def __init__(self, window, unsaved_databases_list):
        super().__init__()

        self.set_transient_for(window)

        for database in unsaved_databases_list:
            unsaved_database_row = Gtk.ListBoxRow()
            check_button = Gtk.CheckButton()
            if "/home/" in database.database_manager.database_path:
                check_button.set_label(
                    "~/" + os.path.relpath(database.database_manager.database_path)
                )
            else:
                check_button.set_label(
                    Gio.File.new_for_path(
                        database.database_manager.database_path
                    ).get_uri()
                )
            check_button.connect(
                "toggled", self.on_save_check_button_toggled, [database, window]
            )
            check_button.set_active(True)
            unsaved_database_row.set_child(check_button)
            self.unsaved_databases_list_box.append(unsaved_database_row)

    def on_save_check_button_toggled(self, check_button, args):
        database, window = args
        if check_button.get_active():
            window.databases_to_save.append(database)
        else:
            window.databases_to_save.remove(database)
