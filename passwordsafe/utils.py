#!/usr/bin/env python3
from __future__ import annotations

import secrets
from gettext import gettext as _
from typing import Callable

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from gi.repository import Gio, GLib, Gtk, GObject


def format_time(time: GLib.DateTime | None, hours: bool = True) -> str:
    """Displays a UTC DateTime in the local timezone."""
    if not time:
        return ""

    time_format = "%e %b %Y"
    if hours:
        time_format += " %R"  # NOTE This is a U+2002 En Space.

    return time.to_local().format(time_format)


def create_random_data(bytes_buffer):
    return secrets.token_bytes(bytes_buffer)


def generate_keyfile(
    gfile: Gio.File, callback: Callable[[GObject.Object, Gio.Task], None]
) -> None:
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(create_random_data(96))  # type: ignore
    contents = cipher.nonce + tag + ciphertext  # type: ignore

    gfile.replace_contents_async(
        contents,
        None,
        False,
        Gio.FileCreateFlags.REPLACE_DESTINATION,
        None,
        callback,
    )


class KeyFileFilter:
    """Filter out Keyfiles in the file chooser dialog"""

    def __init__(self):
        self.file_filter = Gtk.FileFilter()

        self.file_filter.set_name(_("Keyfile"))
        self.file_filter.add_mime_type("application/octet-stream")
        self.file_filter.add_mime_type("application/x-keepass2")
        self.file_filter.add_mime_type("text/plain")
        self.file_filter.add_mime_type("application/x-iwork-keynote-sffkey")
