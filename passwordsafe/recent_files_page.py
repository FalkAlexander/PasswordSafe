# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os

from gi.repository import Adw, Gio, Gtk

import passwordsafe.config_manager as config


@Gtk.Template(resource_path="/org/gnome/PasswordSafe/recent_files_page.ui")
class RecentFilesPage(Gtk.Box):
    __gtype_name__ = "RecentFilesPage"

    _last_opened_listbox: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self):
        """Recently opened files page widget

        Shows the list of recently opened files
        for the user to pick one (or the welcome screen if there are none)"""
        super().__init__()

        user_home: Gio.File = Gio.File.new_for_path(os.path.expanduser("~"))
        self.list_model = Gio.ListStore.new(RecentFileRow)

        for path_uri in config.get_last_opened_list():
            gio_file: Gio.File = Gio.File.new_for_uri(path_uri)
            # TODO Remove the file from config if it does not exist.
            if not gio_file.query_exists():
                logging.info(
                    "Ignoring nonexistent recent file: %s", gio_file.get_path()
                )
                continue  # only work with existing files

            path: str = user_home.get_relative_path(gio_file) or gio_file.get_path()
            filename: str = os.path.splitext(gio_file.get_basename())[0]
            name: str = gio_file.get_uri()

            recent_file_row = RecentFileRow(filename, path, name)
            self.list_model.insert(0, recent_file_row)

        self._last_opened_listbox.bind_model(self.list_model, (lambda item: item))

    @property
    def is_empty(self) -> bool:
        """Return True is there are no recent files."""
        return self.list_model.get_n_items() == 0

    @Gtk.Template.Callback()
    def _on_last_opened_listbox_activated(self, _widget, list_box_row):
        """cb when we click on an entry in the recently opened files list

        Starts opening the database corresponding to the entry."""
        file_uri: str = list_box_row.get_name()
        window = Gio.Application.get_default().window
        window.start_database_opening_routine(Gio.File.new_for_uri(file_uri).get_path())


class RecentFileRow(Adw.ActionRow):
    __gtype_name__ = "RecentFileRow"

    def __init__(self, filename, path, name):
        super().__init__()

        self.set_title(filename)
        self.set_subtitle(path)
        self.set_name(name)
        self.set_selectable(False)
        self.set_activatable(True)
