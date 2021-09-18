# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os

from gi.repository import Adw, Gio, GObject, Gtk

import gsecrets.config_manager as config


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/recent_files_page.ui")
class RecentFilesPage(Gtk.Box):
    __gtype_name__ = "RecentFilesPage"

    _last_opened_listbox: Gtk.ListBox = Gtk.Template.Child()

    window = GObject.Property(type=Adw.ApplicationWindow)

    def __init__(self):
        """Recently opened files page widget

        Shows the list of recently opened files
        for the user to pick one (or the welcome screen if there are none)"""
        super().__init__()

        self.list_model = Gio.ListStore.new(Gio.File)

        for path_uri in config.get_last_opened_list():
            gio_file: Gio.File = Gio.File.new_for_uri(path_uri)
            # TODO Remove the file from config if it does not exist.
            if not gio_file.query_exists():
                logging.info(
                    "Ignoring nonexistent recent file: %s", gio_file.get_path()
                )
                continue  # only work with existing files

            self.list_model.insert(0, gio_file)

        self._last_opened_listbox.bind_model(self.list_model, RecentFileRow)

    @property
    def is_empty(self) -> bool:
        """Return True is there are no recent files."""
        return self.list_model.get_n_items() == 0

    @Gtk.Template.Callback()
    def _on_last_opened_listbox_activated(self, _widget, list_box_row):
        """cb when we click on an entry in the recently opened files list

        Starts opening the database corresponding to the entry."""
        file_path = list_box_row.gfile.get_path()
        database = self.props.window.unlocked_db

        if database:
            auto_save = config.get_save_automatically()
            is_dirty = database.database_manager.is_dirty
            is_current = database.database_manager.database_path == file_path

            if is_dirty and not is_current:
                app = Gio.Application.get_default()
                window = app.new_window()
                window.start_database_opening_routine(file_path)
                window.present()
            else:
                if is_current:
                    self.props.window.view = self.props.window.view.UNLOCK_DATABASE
                    return

                if auto_save:
                    database.save_database()

                self.props.window.unlocked_db.do_dispose()
                self.props.window.unlocked_db = None
                self.props.window.start_database_opening_routine(file_path)

        else:
            self.props.window.start_database_opening_routine(file_path)


class RecentFileRow(Adw.ActionRow):
    __gtype_name__ = "RecentFileRow"

    def __init__(self, gfile: Gio.File):
        super().__init__()

        self.gfile = gfile

        user_home: Gio.File = Gio.File.new_for_path(os.path.expanduser("~"))
        filename: str = os.path.splitext(gfile.get_basename())[0]
        name: str = gfile.get_uri()
        path: str = user_home.get_relative_path(gfile) or gfile.get_path()

        self.set_title(filename)
        self.set_subtitle(path)
        self.set_name(name)
        self.set_selectable(False)
        self.set_activatable(True)
        # TODO This is done so that it does not grab focus,
        # and then the focus in not on the password entry.
        self.set_focus_on_click(False)
