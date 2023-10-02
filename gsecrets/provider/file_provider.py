# SPDX-License-Identifier: GPL-3.0-only
from gettext import gettext as _
import logging
from gi.repository import Adw, Gio, GLib, Gtk

import gsecrets.config_manager as config

from gsecrets.database_manager import DatabaseManager

from gsecrets.utils import (
    KeyFileFilter,
    generate_keyfile_async,
    generate_keyfile_finish,
)
from gsecrets.provider.base_provider import BaseProvider


class FileProvider(BaseProvider):
    def __init__(self, window):
        super().__init__()

        self.raw_key = None
        self.keyfile_path = None
        self.keyfile_hash = ""
        self.unlock_row = None
        self.unlock_clear_button = None
        self.create_row = None
        self.create_clear_button = None
        self.window = window

    def create_unlock_widget(self, database_manager: DatabaseManager) -> Gtk.Widget:
        self.unlock_row = Adw.ActionRow()
        self.unlock_row.set_title(_("Keyfile"))
        if self.keyfile_path:
            self.unlock_row.set_subtitle(self.keyfile_path)

        button = Gtk.Button()
        button.set_valign(Gtk.Align.CENTER)
        button.add_css_class("flat")
        button.set_icon_name("folder-open-symbolic")
        button.set_tooltip_text(_("Select Keyfile"))
        button.connect('clicked', self._on_keyfile_button_clicked)
        self.unlock_row.add_suffix(button)

        self.unlock_clear_button = Gtk.Button()
        self.unlock_clear_button.set_visible(False)
        self.unlock_clear_button.set_valign(Gtk.Align.CENTER)
        self.unlock_clear_button.add_css_class("flat")
        self.unlock_clear_button.set_icon_name("edit-delete-symbolic")
        self.unlock_clear_button.set_tooltip_text(_("Clear Keyfile"))
        self.unlock_clear_button.connect('clicked', self._on_unlock_clear_keyfile)
        self.unlock_row.add_suffix(self.unlock_clear_button)

        pairs = config.get_provider_config(database_manager.path, 'FileProvider')

        self._set_keyfile(None)
        if pairs and pairs['url'] is not None:
            keyfile = Gio.File.new_for_path(pairs['url'])
            if keyfile.query_exists():
                self._set_keyfile(keyfile)

        return self.unlock_row

    def _on_unlock_clear_keyfile(self, _widget):
        self.keyfile_path = ""
        self.keyfile_hash = ""
        self.raw_key = None

        self.unlock_row.set_subtitle(_("Select keyfile"))
        self.unlock_clear_button.set_visible(False)

    def _on_keyfile_button_clicked(self, _widget: Gtk.Widget) -> None:
        """cb invoked when we unlock a database via keyfile"""
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(KeyFileFilter().file_filter)

        dialog = Gtk.FileDialog.new()
        dialog.props.filters = filters
        dialog.props.title = _("Select Keyfile")

        dialog.open(self.window, None, self._on_dialog_response)

    def _on_dialog_response(self, dialog: Gtk.Dialog, result: int) -> None:
        try:
            keyfile = dialog.open_finish(result)
        except GLib.Error as err:
            logging.error("Could not open file: %s", err.message)
        else:
            self._set_keyfile(keyfile)

    def _set_keyfile(self, keyfile: Gio.File) -> None:
        if keyfile is None:
            self._on_unlock_clear_keyfile(None)
            return

        self.keyfile_path = keyfile.get_path()
        keyfile.load_bytes_async(None, self.load_keyfile_callback)

        logging.debug("Keyfile selected: %s", self.keyfile_path)

    def load_keyfile_callback(self, keyfile, result):
        try:
            self.raw_key, _etag = keyfile.load_bytes_finish(result)
        except GLib.Error as err:
            logging.error("Could not set keyfile hash: %s", err.message)
            self.window.send_notification(_("Could not load keyfile"))
        else:
            keyfile_hash = GLib.compute_checksum_for_bytes(
                GLib.ChecksumType.SHA1, self.raw_key
            )
            file_path = keyfile.get_path()
            basename = keyfile.get_basename()
            if keyfile_hash:
                self.keyfile_hash = keyfile_hash
                self.keyfile_path = file_path

            if self.unlock_row:
                self.unlock_row.set_subtitle(basename)
                self.unlock_clear_button.set_visible(True)

            if self.create_row:
                self.create_row.set_subtitle(basename)
                self.create_row.set_visible(True)
        finally:
            if self.unlock_row:
                self.unlock_row.props.sensitive = True

    def create_database_row(self):
        self.create_row = Adw.ActionRow()
        self.create_row.set_title(_("Keyfile"))

        generate_button = Gtk.Button()
        generate_button.set_icon_name("document-new-symbolic")
        generate_button.set_tooltip_text(_("Generate Keyfile"))
        generate_button.connect("clicked", self.on_generate_keyfile_button_clicked)
        generate_button.add_css_class("flat")
        generate_button.set_valign(Gtk.Align.CENTER)
        self.create_row.add_suffix(generate_button)

        create_clear_button = Gtk.Button()
        create_clear_button.set_tooltip_text(_("Clear Keyfile"))
        create_clear_button.set_icon_name("edit-delete-symbolic")
        create_clear_button.connect("clicked", self._on_create_clear_keyfile)
        create_clear_button.add_css_class("flat")
        create_clear_button.set_valign(Gtk.Align.CENTER)
        self.create_clear_button = create_clear_button
        self.create_row.add_suffix(create_clear_button)

        self._on_create_clear_keyfile(None)

        return self.create_row

    def _on_create_clear_keyfile(self, _widget):
        self.keyfile_path = ""
        self.keyfile_hash = ""
        self.raw_key = None

        self.create_row.set_subtitle(_("Use a file to increase security"))
        self.create_clear_button.set_visible(False)

    @property
    def available(self):
        return True

    def _on_filechooser_response(self, dialog, result):
        try:
            keyfile = dialog.save_finish(result)
        except GLib.Error as err:
            logging.error("Could not save file: %s", err.message)
        else:
            keyfile_path = keyfile.get_path()
            logging.debug("New keyfile location: %s", keyfile_path)

            def callback(_gfile, result):
                try:
                    _res, _hash = generate_keyfile_finish(result)
                except GLib.Error as err:
                    logging.error("Could not create keyfile: %s", err.message)
                    self.window.send_notification(_("Could not create keyfile"))
                else:
                    self.create_clear_button.set_visible(True)
                    keyfile.load_bytes_async(None, self.load_keyfile_callback)

            generate_keyfile_async(keyfile, callback)

    def on_generate_keyfile_button_clicked(self, _widget: Gtk.Button) -> None:
        """cb invoked when we create a new keyfile for a newly created Safe"""
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(KeyFileFilter().file_filter)

        dialog = Gtk.FileDialog.new()
        dialog.props.filters = filters
        dialog.props.title = _("Generate Keyfile")
        dialog.props.accept_label = _("_Generate")
        dialog.props.initial_name = _("Keyfile")

        dialog.save(
            self.window,
            None,
            self._on_filechooser_response,
        )

    def config(self):
        ret = {}

        if self.keyfile_path:
            ret["url"] = self.keyfile_path

        return ret

    def clear_input_fields(self):
        self._on_create_clear_keyfile(None)
