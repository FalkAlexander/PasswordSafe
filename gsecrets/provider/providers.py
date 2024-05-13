# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from gi.repository import Adw, Gio, GLib, GObject

from gsecrets.provider.file_provider import FileProvider
from gsecrets.provider.pkcs11_provider import Pkcs11Provider
from gsecrets.provider.yubikey_provider import YubiKeyProvider

if TYPE_CHECKING:
    from gsecrets.utils import LazyValue

KEY_PROVIDERS = [FileProvider, Pkcs11Provider, YubiKeyProvider]


class Providers(GObject.Object):
    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__()

        self.providers = []
        self.salt: LazyValue[bytes] | None = None

        for key_provider in KEY_PROVIDERS:
            self.providers.append(key_provider(window))

    def get_key_providers(self) -> list:
        return self.providers

    def generate_composite_key_async(
        self,
        salt: LazyValue[bytes],
        callback: Gio.AsyncReadyCallback,
        cancellable: GLib.Cancellable = None,
    ) -> None:
        """Generate composite key.

        Traverse all available key providers and request each raw_key.
        This one is appended to the main raw_key.
        """
        self.salt = salt

        def generate_composite_key_task(task, self, _task_data, _cancellable):
            raw_key = b""

            # Generate composite key
            # It is safe to travel all providers as non configured ones do not
            # have a key.
            for provider in self.providers:
                logging.debug("Generate key for %s", type(provider).__name__)
                try:
                    if provider.generate_key(self.salt):
                        logging.debug("Adding key from %s", type(provider).__name__)
                        raw_key += provider.key
                except ValueError as err:
                    task.return_error(GLib.Error(str(err)))
                    return

            if len(raw_key) == 0:
                logging.debug("No key providers in use, returning None")
                task.return_value(None)
                return

            task.return_value(raw_key)

        task = Gio.Task.new(self, cancellable, callback)
        task.run_in_thread(generate_composite_key_task)

    def generate_composite_key_finish(self, result):
        """Finish generate_composite_key_finish.

        Can raise GLib.Error
        """
        _success, composite_key = result.propagate_value()
        return composite_key
