# SPDX-License-Identifier: GPL-3.0-only
import logging
from gi.repository import Adw, GLib, Gio, GObject
from gsecrets.provider.file_provider import FileProvider

KEY_PROVIDERS = [
    FileProvider,
]

class Providers(GObject.Object):
    def __init__(self, window: Adw.ApplicationWindow):
        super().__init__()

        self.providers = []

        for key_provider in KEY_PROVIDERS:
            self.providers.append(key_provider(window))

    def get_key_providers(self) -> list:
        return self.providers

    def generate_composite_key_async(self,
                                     salt,
                                     callback = None,
                                     cancellable = None) -> None:
        """Generate composite key

        Traverse all available key providers and request each raw_key.
        This one is appended to the main raw_key.
        """

        self.salt = salt

        def generate_composite_key_task(task, self, _task_data, _cancellable):
            raw_key = b""
            keyfile_path = ""
            keyfile_hash = ""

            # Generate composite key
            # It is safe to travel all providers as non configured ones do not
            # have a key.
            for provider in self.providers:
                logging.debug("Generate key for %s", type(provider).__name__)
                if provider.generate_key(self.salt):
                    logging.debug("Adding key from %s", type(provider).__name__)
                    raw_key += provider.key

            if len(raw_key) == 0:
                logging.debug("No key providers in use, returning None")
                task.return_value([None, "", ""])
                return

            # As long as pykeepass does not support keyfile as bytes, create tmp
            # file.
            try:
                (tmp, tmp_stream) = Gio.File.new_tmp()
                tmp_stream.get_output_stream().write_all(raw_key)
                tmp_stream.close()

                keyfile_path = tmp.get_path()
                keyfile_hash = GLib.compute_checksum_for_bytes(
                    GLib.ChecksumType.SHA1, GLib.Bytes(raw_key))
            except GLib.Error as err:
                logging.error("Could not write to stream: %s", err.message)
                task.return_error(err)

            task.return_value([raw_key, keyfile_path, keyfile_hash])

        task = Gio.Task.new(self, cancellable, callback)
        task.run_in_thread(generate_composite_key_task)

    def generate_composite_key_finish(self, result):
        try:
            _success, data = result.propagate_value()
            return data
        except GLib.Error as err:
            raise err
