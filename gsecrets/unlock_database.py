# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import typing
from gettext import gettext as _
from pathlib import Path

from gi.repository import Adw, Gio, GLib, Gtk

import gsecrets.config_manager
from gsecrets import const
from gsecrets.database_manager import DatabaseManager
from gsecrets.err import QUARK, ErrorType
from gsecrets.fingerprint_verifier import FingerprintVerifier
from gsecrets.unlocked_database import UnlockedDatabase
from gsecrets.utils import compare_passwords

if typing.TYPE_CHECKING:
    from gsecrets.widgets.window import Window


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlock_database.ui")
class UnlockDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes

    __gtype_name__ = "UnlockDatabase"

    database_manager: DatabaseManager | None = None

    password_entry = Gtk.Template.Child()
    key_group = Gtk.Template.Child()
    provider_group = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    headerbar = Gtk.Template.Child()
    unlock_button = Gtk.Template.Child()
    banner = Gtk.Template.Child()
    _progress = Gtk.Template.Child()
    fingerprint_img = Gtk.Template.Child()

    FPRINT_MAX_TRIES = 3

    def __init__(self, window: Window, database_file: Gio.File) -> None:
        super().__init__()

        filepath = database_file.get_path()

        self.window = window
        self.composition_key = None

        # Reset headerbar to initial state if it already exists.
        self.headerbar.title.props.title = database_file.get_basename()

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == filepath
            if is_current:
                self.database_manager = database.database_manager

        if not self.database_manager:
            self.database_manager = DatabaseManager(
                window.key_providers.get_key_providers(),
                filepath,
            )

        if gsecrets.const.IS_DEVEL:
            self.status_page.props.icon_name = gsecrets.const.APP_ID

        self.fprint: FingerprintVerifier | None = None
        self.fprint_tries = 0
        if gsecrets.config_manager.get_fingerprint_quick_unlock():
            self._map_fingerprint_reader()

        self.quick_unlock_failed = False

        self.event_controller = Gtk.EventControllerFocus.new()
        self.add_controller(self.event_controller)
        self.event_controller.connect("enter", self.on_enter)
        self.event_controller.connect("leave", self.on_leave)

        settings = self.window.application.settings
        settings.connect(
            "changed::fingerprint-quick-unlock",
            self._on_fingerprint_settings_changed,
        )

        self.window.set_default_widget(self.unlock_button)

        for key_provider in self.window.key_providers.get_key_providers():
            if key_provider.available:
                widget = key_provider.create_unlock_widget(self.database_manager)
                self.provider_group.add(widget)

    def do_unmap(self):  # pylint: disable=arguments-differ
        Gtk.Widget.do_unmap(self)
        self._progress.end_pulse()
        self.remove_controller(self.event_controller)
        self._unmap_fingerprint_reader()

    def on_enter(self, _user_data):
        if self.database_manager and self.database_manager.password != "":
            if (
                gsecrets.config_manager.get_quick_unlock()
                and not self.quick_unlock_failed
            ):
                self.window.show_banner(_("Quick Unlock active"))
                self.provider_group.props.visible = False
            # only start reading if there are still tries left
            if self.fprint_tries < self.FPRINT_MAX_TRIES:
                self._start_fingerprint_reader()
        else:
            logging.debug("Quick unlock disabled as no password is available.")

    def on_leave(self, _user_data):
        if self.fprint_tries < self.FPRINT_MAX_TRIES:
            self._stop_fingerprint_reader()

    def grab_entry_focus(self):
        self.password_entry.grab_focus()

    def is_safe_open_elsewhere(self) -> bool:
        """Whether the safe is already open.

        Return True if the safe is already open but not in the
        current window.
        """
        is_current = False
        db_path = self.database_manager.path  # type: ignore
        is_open = self.window.application.is_safe_open(db_path)

        if database := self.window.unlocked_db:
            is_current = database.database_manager.path == db_path

        return is_open and not is_current

    def _on_generated_composite_key(self, providers, result):
        self._set_sensitive(True)

        try:
            self.composition_key = providers.generate_composite_key_finish(result)
        except GLib.Error:
            logging.exception("Could not generate composite key")
            self.window.send_notification(_("Failed to generate composite key"))
            return

        entered_pwd = self.password_entry.get_text()

        if self.is_safe_open_elsewhere():
            self.window.send_notification(
                # TRANSLATORS For example: "Safe ~/MySafe.kdbx is already open"
                _("Safe {path} is already open").format(
                    path=self.database_manager.path,
                ),
            )
            return

        if not self.database_manager.opened:
            self._open_database()
            return

        quick_unlock = (
            gsecrets.config_manager.get_quick_unlock()
            and not self.quick_unlock_failed
            and entered_pwd == self.database_manager.password[-4:]
        )

        full_unlock = (
            compare_passwords(entered_pwd, self.database_manager.password)
            and self.database_manager.composition_key == self.composition_key
        )

        if quick_unlock or full_unlock:
            self.database_manager.props.locked = False
            self.database_manager.add_to_history()
        else:
            self._unlock_failed()

    @Gtk.Template.Callback()
    def _on_entry_activated(self, _widget: Gtk.Widget) -> None:
        self.unlock_button.activate()

    @Gtk.Template.Callback()
    def _on_unlock_button_clicked(self, _widget: Gtk.Button) -> None:
        if not self.database_manager:
            return

        self._set_sensitive(False)
        self.window.key_providers.generate_composite_key_async(
            self.database_manager.get_salt_as_lazy(),
            self._on_generated_composite_key,
        )

    #
    # Open Database
    #

    def _open_database(self):
        self._progress.start_pulse()

        self._set_sensitive(False)

        password = self.password_entry.props.text

        self.database_manager.unlock_async(
            password,
            self.composition_key,
            self._unlock_callback,
        )

    def _unlock_callback(self, database_manager, result):
        try:
            database_manager.unlock_finish(result)
        except GLib.Error as err:
            if not err.matches(QUARK, ErrorType.CREDENTIALS_ERROR):
                logging.exception("Could not unlock safe")

            self._unlock_failed()
            return

        opened = Gio.File.new_for_path(database_manager.path)

        if gsecrets.config_manager.get_development_backup_mode():
            self.store_backup(opened)

        database_manager.add_to_history()

        if self.window.unlocked_db is None:
            database = UnlockedDatabase(self.window, database_manager)
            self.window.unlocked_db = database
            self.window.unlocked_db_bin.props.child = database

        self.window.view = self.window.View.UNLOCKED_DATABASE
        self._reset_page()

    #
    # Helper Functions
    #

    def _unlock_failed(self) -> None:
        self.window.send_notification(_("Failed to unlock Safe"))

        self.password_entry.add_css_class("error")
        self.password_entry.delete_text(0, -1)
        self._set_sensitive(True)
        self._progress.end_pulse()

        # Regrab the focus of the entry.
        self.password_entry.grab_focus()

    def _reset_page(self):
        self.password_entry.set_text("")
        self.password_entry.remove_css_class("error")

        self._set_sensitive(True)

        self._progress.end_pulse()

        self.quick_unlock_failed = True
        self.provider_group.props.visible = True

    def _set_sensitive(self, sensitive):
        delegate = self.password_entry.get_delegate()
        if delegate.has_focus() and not sensitive:
            self.window.props.focus_widget = None

        for key in self.key_group:
            key.set_sensitive(sensitive)

        for key in self.provider_group:
            key.set_sensitive(sensitive)

        self.unlock_button.set_sensitive(sensitive)
        self.headerbar.set_sensitive(sensitive)

    def store_backup(self, gfile):
        cache_dir = Path(GLib.get_user_cache_dir()) / const.SHORT_NAME / "backup"
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True)

        current_time = GLib.DateTime.new_now_local().format("%F_%T")
        basename = Path(gfile.get_basename()).stem
        backup_name = basename + "_backup_" + current_time + ".kdbx"
        backup = Gio.File.new_for_path(str(cache_dir / backup_name))

        def callback(gfile, result):
            try:
                gfile.copy_finish(result)
            except GLib.Error as err:
                logging.warning("Could not save database backup: %s", err.message)

        if GLib.check_version(2, 81, 0) is None:
            gfile.copy_async(
                backup,
                Gio.FileCopyFlags.NONE,
                GLib.PRIORITY_DEFAULT,
                None,
                None,
                callback,
            )
        else:
            gfile.copy_async(
                backup,
                Gio.FileCopyFlags.NONE,
                GLib.PRIORITY_DEFAULT,
                None,
                None,
                None,
                callback,
            )

    def show_banner(self, label: str) -> None:
        self.banner.set_title(label)
        self.banner.set_revealed(True)

    def close_banner(self):
        self.banner.set_revealed(False)

    #
    # Fingerprint-related stuff
    #

    def _on_fingerprint_settings_changed(self, _settings, _key):
        if gsecrets.config_manager.get_fingerprint_quick_unlock():
            logging.debug("Fingerprint got enabled, mapping fingerprint reader...")
            self._map_fingerprint_reader()
        else:
            logging.debug("Fingerprint got disabled, unmapping fingerprint reader...")
            self._unmap_fingerprint_reader()

    def _start_fingerprint_reader_cb(self) -> None:
        if not self.fprint:
            return

        async def cb():
            if await self.fprint.verify_start():
                self.fingerprint_img.props.visible = True

        app = Gio.Application.get_default()
        app.create_asyncio_task(cb())

    def _start_fingerprint_reader(self) -> None:
        if not self.fprint:
            return
        self.fprint.connect(self._start_fingerprint_reader_cb)

    def _stop_fingerprint_reader(self) -> None:
        if not self.fprint:
            return

        async def disconnect():
            await self.fprint.verify_stop()
            self.fprint.disconnect()
            self.fingerprint_img.props.visible = False

        app = Gio.Application.get_default()
        app.create_asyncio_task(disconnect())

    def _map_fingerprint_reader(self) -> None:
        logging.debug("Connecting to the fingerprint device...")
        try:
            self.fprint = FingerprintVerifier(
                self._on_fingerprint_success,
                self._on_fingerprint_retry,
                self._on_fingerprint_failure,
            )
        except RuntimeError as err:
            logging.debug("Failed initialize fingerprint: %s", err)

    def _unmap_fingerprint_reader(self) -> None:
        if not self.fprint:
            return
        logging.debug("Disconnecting the fingerprint device...")
        self._stop_fingerprint_reader()
        self.fprint = None

    def _on_fingerprint_success(self):
        """Success callback of the the FingerprintVerifier."""
        self.fingerprint_img.add_css_class("success")
        GLib.timeout_add(250, self._after_fingerprint_success)
        logging.debug("Fingerprint success")

    def _after_fingerprint_success(self):
        """Unlocks database after animation of _on_fingerprint_success."""
        self.database_manager.props.locked = False

    def _on_fingerprint_retry(self):
        """Retry callback of the the FingerprintVerifier."""
        self.fingerprint_img.add_css_class("retry")
        GLib.timeout_add(850, self._after_fingerprint_retry)
        logging.debug("Fingerprint retry")

    def _after_fingerprint_retry(self):
        """Cleans up animation after _on_fingerprint_retry."""
        self.fingerprint_img.remove_css_class("retry")

    def _on_fingerprint_failure(self):
        """Failure callback of the the FingerprintVerifier."""
        self.fprint_tries += 1

        async def start_fprint():
            status = await self.fprint.verify_start()
            if not status:
                # in case fingerprint sensor itself refuses
                self.fingerprint_img.add_css_class("error")
                self.window.send_notification(_("Please unlock using the password."))
                logging.debug(
                    "Retry after verify-no-match failed. Fingerprint disabled.",
                )

        if self.fprint_tries >= self.FPRINT_MAX_TRIES:
            # at most 3 tries for unlocking with the fingerprint sensor
            self.fingerprint_img.add_css_class("error")
            self.window.send_notification(
                _("Maximum tries reached. Please unlock using the password."),
            )
            self.fprint.disconnect()
            logging.debug("Max tries reached. Fingerprint disabled.")
        else:
            # else start verification again
            self.fingerprint_img.add_css_class("warning")
            GLib.timeout_add(850, self._after_fingerprint_warning)
            logging.debug("Fingerprint no-match for try %i", self.fprint_tries)
            app = Gio.Application.get_default()
            app.create_asyncio_task(start_fprint())

    def _after_fingerprint_warning(self):
        """Cleans up.

        Animation after _on_fingerprint_failure if FPRINT_MAX_TRIES not reached
        """
        self.fingerprint_img.remove_css_class("warning")
