# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from gettext import gettext as _
from typing import TYPE_CHECKING

import usb
import yubico
from gi.repository import Adw, Gio, GObject, Gtk

import gsecrets.config_manager as config
from gsecrets.provider.base_provider import BaseProvider

if TYPE_CHECKING:
    from gsecrets.database_manager import DatabaseManager
    from gsecrets.utils import LazyValue


class YubiKeyInfo(GObject.Object):
    __gtype_name__ = "YubiKeyInfo"

    def __init__(self, description: str | None = None, serial: int = 0, slot: int = 0):
        super().__init__()

        self._description = description
        self._serial = serial
        self._slot = slot
        self._raw_key = None

    @GObject.Property(type=str)
    def label(self):
        if not self._description:
            return _("No Key")

        # TRANSLATORS For example: YubiKey 4 [123456] - Slot 2
        return _("{description} [{serial}] - Slot {slot}").format(
            description=self._description,
            serial=str(self._serial),
            slot=self._slot,
        )

    @GObject.Property(type=str)
    def description(self):
        return self._description

    @GObject.Property(type=str)
    def serial(self):
        return self._serial

    @GObject.Property(type=str)
    def slot(self):
        return self._slot


class YubiKeyProvider(BaseProvider):
    def __init__(self, _window):
        super().__init__()

        self.active_key: YubiKeyInfo = None
        self.unlock_row: Adw.ComboRow = None
        self.create_row: Adw.ComboRow = None

        # NOTE: There is currently a bug which prevents yubikey rescan
        # running under flatpak, that's why we can simply collect all yubikeys
        # here in one go and set available according to the list length
        # Needs to be fixed asap
        self.yubikeys = self.get_all_yubikeys(False)

    def get_all_yubikeys(self, debug: bool) -> list:
        """Look for YubiKeys.

        We look with ever increasing `skip' value until an error is returned.

        Return all instances of class YubiKey we got before failing.
        """
        res = []
        for _idx in range(4):
            try:
                yubikey = yubico.find_yubikey(debug=debug, skip=_idx)
            except yubico.yubikey.YubiKeyError:
                break
            else:
                try:
                    serial = yubikey.serial()
                except yubico.yubikey.YubiKeyTimeout:
                    logging.exception("Timeout getting yubikey serial")
                except yubico.yubikey.YubiKeyError:
                    logging.exception("Could not read yubikey serial")
                else:
                    logging.debug(
                        "Found %s [%s]",
                        yubikey.description,
                        str(serial),
                    )

                    res += [
                        YubiKeyInfo(yubikey.description, serial, slot)
                        for slot in yubikey.status().valid_configs()
                    ]
                finally:
                    # This must be done as otherwise usb access is broken
                    del yubikey

        return res

    def get_yubikey(self, serial: int, debug: bool = False) -> yubico.YubiKey:
        """Get a specific yubikey based on it's serial."""
        try:
            for _idx in range(4):
                yubikey = yubico.find_yubikey(debug=debug, skip=_idx)

                if yubikey.serial() == serial:
                    return yubikey

                del yubikey
        except yubico.yubikey.YubiKeyError:
            pass

        return None

    @property
    def available(self):
        return len(self.yubikeys) != 0

    def _create_model(self):
        model = Gio.ListStore.new(YubiKeyInfo)
        model.append(YubiKeyInfo())

        for this in self.yubikeys:
            model.append(this)

        return model

    def create_unlock_widget(self, database_manager: DatabaseManager) -> Gtk.Widget:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        row = Adw.ComboRow()
        row.set_title(_("YubiKey"))
        row.set_subtitle(_("Select key"))
        row.set_factory(factory)
        row.connect("notify::selected", self._on_unlock_row_selected)
        self.unlock_row = row

        refresh_button = Gtk.Button()
        refresh_button.set_valign(Gtk.Align.CENTER)
        refresh_button.add_css_class("flat")
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text(_("Select YubiKey slot"))
        refresh_button.connect("clicked", self._on_refresh_button_clicked)
        row.add_suffix(refresh_button)

        self._on_refresh_button_clicked(row)
        row.set_selected(0)

        if (
            cfg := config.get_provider_config(database_manager.path, "YubiKeyProvider")
        ) and "serial" in cfg:
            model = row.get_model()

            for pos, info in enumerate(model):
                if info.serial == cfg["serial"] and info.slot == cfg["slot"]:
                    row.set_selected(pos)
                    break

        return row

    def _on_unlock_row_selected(
        self,
        widget: Adw.ComboRow,
        _param: GObject.ParamSpec,
    ) -> None:
        self.active_key = widget.get_selected_item()

    def _on_factory_setup(self, _factory, list_item):
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)

    def _on_factory_bind(self, _factory, list_item):
        label = list_item.get_child()
        info = list_item.get_item()
        label.props.label = info.props.label

    def _on_refresh_button_clicked(self, _row: Adw.ComboRow) -> None:
        model = self._create_model()

        self.unlock_row.set_model(model)
        self.unlock_row.set_selected(len(model) - 1)

    def create_database_row(self) -> None:
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        self.create_row = Adw.ComboRow()
        self.create_row.set_title(_("YubiKey"))
        self.create_row.set_factory(factory)
        self.create_row.connect("notify::selected", self._on_create_row_selected)

        refresh_button = Gtk.Button()
        refresh_button.set_valign(Gtk.Align.CENTER)
        refresh_button.add_css_class("flat")
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text(_("Select YubiKey slot"))
        refresh_button.connect(
            "clicked",
            self._on_yubikey_create_refresh_button_clicked,
        )
        self.create_row.add_suffix(refresh_button)

        self._on_yubikey_create_refresh_button_clicked(self.create_row)

        return self.create_row

    def _on_create_row_selected(
        self,
        widget: Adw.ComboRow,
        _param: GObject.ParamSpec,
    ) -> None:
        self.active_key = widget.get_selected_item()

    def _on_yubikey_create_refresh_button_clicked(self, _button: Gtk.Button) -> None:
        model = self._create_model()

        self.create_row.set_model(model)
        self.create_row.set_selected(0)

    def generate_key(self, salt: LazyValue[bytes]) -> bool:
        if self.active_key is None:
            return False

        try:
            if yubikey := self.get_yubikey(self.active_key.serial):
                self.emit(self.show_message, _("Touch YubiKey"))
                try:
                    self.raw_key = yubikey.challenge_response(
                        salt.value,
                        slot=self.active_key.slot,
                    )
                except yubico.yubikey_base.YubiKeyTimeout as ex:
                    self.emit(self.hide_message)
                    logging.debug("Timeout waiting for challenge response: %s", ex)
                    msg = "Timeout waiting for challenge response"
                    raise ValueError(msg) from ex

                self.emit(self.hide_message)

                # This must be done as otherwise usb access is broken
                del yubikey

                if self.raw_key is not None:
                    return True

        except usb.core.USBError as ex:
            logging.warning("USB error during yubikey key generation")
            msg = "USB error during yubikey key generation"
            raise ValueError(msg) from ex

        return False

    def config(self) -> dict:
        return {"serial": self.active_key.serial, "slot": self.active_key.slot}
