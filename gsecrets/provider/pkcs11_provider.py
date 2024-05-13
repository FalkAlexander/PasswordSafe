# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import atexit
import logging
from gettext import gettext as _
from typing import TYPE_CHECKING

from gi.repository import Adw, Gio, GLib, GObject, Gtk

# pylint: disable=import-error
from PyKCS11 import (
    CKA_CLASS,
    CKA_KEY_TYPE,
    CKA_LABEL,
    CKA_SIGN,
    CKK_RSA,
    CKO_PRIVATE_KEY,
    PyKCS11,
    PyKCS11Lib,
)

import gsecrets.config_manager as config
from gsecrets import const
from gsecrets.provider.base_provider import BaseProvider

if TYPE_CHECKING:
    from gsecrets.database_manager import DatabaseManager
    from gsecrets.utils import LazyValue

MAGIC_ERROR = 0x100

# KeePass-Smart-Certificate-Key-Provider
# https://github.com/BodnarSoft/KeePass-Smart-Certificate-Key-Provider/
# Source/SmartCertificateKeyProvider.cs
# Static string: do not change as otherwise we are no longer compatible
KEEPASS_SCKP_TEXT = (
    "Data text for KeePass Password Safe Plugin"
    " - {F3EF424C-7517-4D58-A3FB-C1FB458FDDB6}!"
)


class Pkcs11Provider(BaseProvider):
    def __init__(self, window):
        super().__init__()
        self.window = window

        self._pkcs11 = None
        self._session = None

        self._active_certificate = None

        atexit.register(self._cleanup)

    def _cleanup(self):
        if self._session:
            try:
                self._session.logout()
            except PyKCS11.PyKCS11Error:
                logging.exception("Could not cleanup")

            self._session.closeSession()

    def scan_slots(self):
        slot_list = self._pkcs11.getSlotList(tokenPresent=True)
        if slot_list:
            self._session = self._pkcs11.openSession(
                slot_list[0],
                PyKCS11.CKF_RW_SESSION,
            )
            return True

        return False

    @property
    def available(self):
        return True

    def logout(self):
        try:
            self._session.logout()
        except PyKCS11.PyKCS11Error:
            logging.exception("Could not logout")

    def login(self, pin: str) -> bool:
        try:
            self._session.login(pin)
        except PyKCS11.PyKCS11Error as err:
            logging.exception("Could not login")

            if err.value != MAGIC_ERROR:
                return False

        logging.debug("Successfully logged in")

        return True

    def _create_model(self):
        model = Gtk.StringList()
        model.append(_("No Smartcard"))

        if not self._pkcs11:
            return model

        if not self.scan_slots():
            return model

        objects = self._session.findObjects(
            [(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_KEY_TYPE, CKK_RSA), (CKA_SIGN, True)],
        )
        for obj in objects:
            value = self._session.getAttributeValue(obj, [CKA_LABEL])[0]
            model.append(value)

        return model

    def create_unlock_widget(self, database_manager: DatabaseManager) -> Gtk.Widget:
        row = Adw.ComboRow()
        row.set_title(_("Smartcard"))
        row.set_subtitle(_("Select certificate"))
        row.connect("notify::selected", self._on_unlock_row_selected)

        self.refresh_stack = Gtk.Stack()
        self.refresh_button = get_refresh_button()
        self.refresh_button.connect("clicked", self._on_refresh_button_clicked, row)
        self.refresh_stack.add_named(self.refresh_button, "button")

        self.refresh_spinner = Gtk.Spinner()
        self.refresh_stack.add_named(self.refresh_spinner, "spinner")
        row.add_suffix(self.refresh_stack)
        self.refresh_stack.set_visible_child(self.refresh_button)

        self.fill_data(row, database_manager)

        row.set_selected(0)

        return row

    def _on_unlock_row_selected(
        self,
        widget: Adw.ComboRow,
        _param: GObject.ParamSpec,
    ) -> None:
        if selected_item := widget.get_selected_item():
            self._active_certificate = selected_item.get_string()

    def _refresh_pkcs11_async(
        self,
        callback: Gio.AsyncReadyCallback,
        row: Adw.ComboRow,
    ) -> None:
        def pkcs11_refresh(task, _source_object, _task_data, _cancellable):
            self._pkcs11 = None
            if not self._pkcs11:
                self._pkcs11 = PyKCS11Lib()

                try:
                    self._pkcs11.load(const.PKCS11_LIB)
                except PyKCS11.PyKCS11Error as err:
                    logging.warning("Could not load pkcs11 library: %s", err)
                    task.return_error(err)
                    return

            present = self.scan_slots()
            task.return_boolean(present)

        self.refresh_stack.set_visible_child(self.refresh_spinner)
        self.refresh_spinner.start()

        task = Gio.Task.new(self, None, callback, row)
        task.run_in_thread(pkcs11_refresh)

    def _refresh_pkcs11_finish(self, result):
        self.refresh_spinner.stop()
        self.refresh_stack.set_visible_child(self.refresh_button)
        return result.propagate_boolean()

    def _on_refresh_button_clicked(
        self,
        _button: Gtk.Button,
        row: Adw.ComboRow,
    ) -> None:
        self._refresh_pkcs11_async(self._on_pkcs11_refresh, row)

    def _on_pkcs11_refresh(
        self,
        _provider: Pkcs11Provider,
        result: Gio.AsyncResult,
        row: Adw.ComboRow,
    ) -> None:
        try:
            present = self._refresh_pkcs11_finish(result)
        except GLib.Error:
            present = False

        if not present:
            dialog = Adw.AlertDialog.new(
                _("No smartcard present"),
                _("Please insert smartcard and retry."),
            )

            dialog.add_response("ok", _("OK"))
            dialog.present(self.window)
            return

        entry = Adw.PasswordEntryRow(activates_default=True, title=_("Passphrase"))
        entry.add_css_class("card")

        dialog = Adw.AlertDialog.new(_("Unlock"), _("Unlock your smartcard"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("unlock", _("Unlock"))
        dialog.set_default_response("unlock")
        dialog.set_extra_child(entry)
        dialog.set_focus(entry)
        dialog.connect("response", self._on_pin_dialog_response, entry, row)
        dialog.present(self.window)

    def fill_data(
        self,
        row: Adw.ComboRow,
        database_manager: DatabaseManager | None = None,
    ) -> None:
        model = self._create_model()
        row.set_model(model)

        if not database_manager:
            return

        row_select = 0
        if (
            cfg := config.get_provider_config(database_manager.path, "Pkcs11Provider")
        ) and "serial" in cfg:
            model = row.get_model()

            for pos, info in enumerate(model):
                if info == cfg["serial"]:
                    row_select = pos
                    break

        row.set_selected(row_select)

    def _on_pin_dialog_response(
        self,
        _dialog: Adw.AlertDialog,
        response: str,
        entry: Gtk.Entry,
        row: Adw.ComboRow,
    ) -> None:
        if response == "unlock":
            pin = entry.get_text()

            ret = self.login(pin)
            if not ret:
                self.window.send_notification(_("Failed to unlock Smartcard"))
                return

            self.fill_data(row)

    def create_database_row(self):
        row = Adw.ComboRow()
        row.set_title(_("Smartcard"))
        row.set_subtitle(_("Use a smartcard"))
        row.connect("notify::selected", self._on_unlock_row_selected)

        self.refresh_stack = Gtk.Stack()
        self.refresh_button = get_refresh_button()
        self.refresh_button.connect("clicked", self._on_refresh_button_clicked, row)
        self.refresh_stack.add_named(self.refresh_button, "button")

        self.refresh_spinner = Gtk.Spinner()
        self.refresh_stack.add_named(self.refresh_spinner, "spinner")
        row.add_suffix(self.refresh_stack)
        self.refresh_stack.set_visible_child(self.refresh_button)

        self.fill_data(row)

        row.set_selected(0)

        return row

    def generate_key(self, _salt: LazyValue[bytes]) -> bool:
        if not self._session:
            return False

        objs = self._session.findObjects(
            [(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_LABEL, self._active_certificate)],
        )
        if len(objs) == 0:
            return False

        priv_key = objs[0]
        mecha = PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, None)

        try:
            signed = self._session.sign(priv_key, KEEPASS_SCKP_TEXT, mecha)
        except PyKCS11.PyKCS11Error as err:
            logging.exception("Could not sign data, abort")
            msg = "Could not sign data"
            raise ValueError(msg) from err

        signed_bytes = bytearray(signed)
        immutable_bytes = bytes(signed_bytes)

        self.raw_key = immutable_bytes

        return True

    def config(self) -> dict:
        return {"label": self._active_certificate}


def get_refresh_button():
    button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
    button.set_valign(Gtk.Align.CENTER)
    button.add_css_class("flat")
    button.set_tooltip_text(_("Refresh Certificate List"))
    return button
