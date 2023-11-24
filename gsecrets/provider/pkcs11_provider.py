# SPDX-License-Identifier: GPL-3.0-only
import atexit
import logging

from gettext import gettext as _
from gi.repository import Adw, Gtk, GObject

# pylint: disable=import-error
from PyKCS11 import (
    PyKCS11Lib,
    PyKCS11,
    CKA_CLASS,
    CKO_PRIVATE_KEY,
    CKA_LABEL,
    CKA_KEY_TYPE,
    CKK_RSA,
    CKA_SIGN,
)

from gsecrets import const
from gsecrets.provider.base_provider import BaseProvider
import gsecrets.config_manager as config
from gsecrets.database_manager import DatabaseManager

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
            except PyKCS11.PyKCS11Error as err:
                logging.debug("Could not cleanup: %s", err)

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
        except PyKCS11.PyKCS11Error as err:
            logging.error("Could not logout: %s", err)

    def login(self, pin: str) -> bool:
        try:
            self._session.login(pin)
        except PyKCS11.PyKCS11Error as err:
            logging.error("Could not login: %s", err)

            if err.value != 0x100:
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
            [(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_KEY_TYPE, CKK_RSA), (CKA_SIGN, True)]
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

        refresh_button = get_refresh_button()
        refresh_button.connect("clicked", self._on_refresh_button_clicked, row)
        row.add_suffix(refresh_button)

        self.fill_data(row, database_manager)

        row.set_selected(0)

        return row

    def _on_unlock_row_selected(
        self, widget: Adw.ComboRow, _param: GObject.ParamSpec
    ) -> None:
        if selected_item := widget.get_selected_item():
            self._active_certificate = selected_item.get_string()

    def _on_refresh_button_clicked(
        self, _button: Gtk.Button, row: Adw.ComboRow
    ) -> None:
        if not self._pkcs11:
            self._pkcs11 = PyKCS11Lib()

            try:
                self._pkcs11.load(const.PKCS11_LIB)
            except PyKCS11.PyKCS11Error as err:
                logging.warning("Could not load pkcs11 library: %s", err)
                return

        present = self.scan_slots()
        if not present:
            dialog = Adw.MessageDialog(
                transient_for=self.window,
                heading=_("No smartcard present"),
                body=_("Please insert smartcard and retry."),
            )

            dialog.add_response("ok", _("OK"))
            dialog.present()
            return

        entry = Adw.PasswordEntryRow(
            activates_default=True,
            title=_("Passphrase"),
        )
        entry.add_css_class("card")

        dialog = Adw.MessageDialog(
            heading=_("Unlock"),
            modal=True,
            body=_("Unlock your smartcard"),
            transient_for=self.window,
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("unlock", _("Unlock"))
        dialog.set_default_response("unlock")
        dialog.set_extra_child(entry)
        dialog.connect("response", self._on_pin_dialog_response, entry, row)
        dialog.present()

    def fill_data(
        self, row: Adw.ComboRow, database_manager: DatabaseManager | None = None
    ) -> None:
        model = self._create_model()
        row.set_model(model)

        if not database_manager:
            return

        row_select = 0
        if cfg := config.get_provider_config(database_manager.path, "Pkcs11Provider"):
            if "serial" in cfg:
                model = row.get_model()

                for pos, info in enumerate(model):
                    if info == cfg["serial"]:
                        row_select = pos
                        break

        row.set_selected(row_select)

    def _on_pin_dialog_response(
        self,
        _dialog: Adw.MessageDialog,
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

        refresh_button = get_refresh_button()
        refresh_button.connect("clicked", self._on_refresh_button_clicked, row)
        row.add_suffix(refresh_button)

        self.fill_data(row)

        row.set_selected(0)

        return row

    def generate_key(self, _salt: bytes) -> bool:
        if not self._session:
            return False

        objs = self._session.findObjects(
            [(CKA_CLASS, CKO_PRIVATE_KEY), (CKA_LABEL, self._active_certificate)]
        )
        if len(objs) == 0:
            return False

        priv_key = objs[0]
        mecha = PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, None)

        try:
            signed = self._session.sign(priv_key, KEEPASS_SCKP_TEXT, mecha)
        except PyKCS11.PyKCS11Error as err:
            logging.error("Could not sign data, abort: %s", err)
            raise ValueError("Could not sign data") from err

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
