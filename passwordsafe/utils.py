#!/usr/bin/env python3
from __future__ import annotations

import secrets
import typing
from gettext import gettext as _
from typing import Callable

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from gi.repository import Gio, GLib, Gtk, GObject

if typing.TYPE_CHECKING:
    from datetime import datetime


def format_time(time: datetime | None) -> str:
    """Displays a UTC datetime in the local timezone."""
    if not time:
        return ""

    timestamp = GLib.DateTime.new_utc(
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second,
    ).to_local()
    return timestamp.format("%e %b %Y %R")


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
