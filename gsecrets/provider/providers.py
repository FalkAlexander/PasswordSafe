# SPDX-License-Identifier: GPL-3.0-only
import logging
from gi.repository import Adw, GLib, Gio
from gsecrets.provider.file_provider import FileProvider

KEY_PROVIDERS = [
    FileProvider,
]


def create_key_providers(window: Adw.ApplicationWindow) -> list:
    providers = []

    for key_provider in KEY_PROVIDERS:
        providers.append(key_provider(window))

    return providers


def generate_composite_key(providers: list) -> tuple[bytes | None, str, str]:
    raw_key = b""
    keyfile_path = ""
    keyfile_hash = ""

    # Generate composite key
    # It is safe to travel all providers as non configured ones do not
    # have a key.
    for provider in providers:
        logging.debug("Generate key for %s", type(provider).__name__)
        data = provider.key.get_data() if provider.key else None
        if data:
            raw_key += data

    if len(raw_key) == 0:
        return None, "", ""

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

    return raw_key, keyfile_path, keyfile_hash
