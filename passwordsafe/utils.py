#!/usr/bin/env python3
from __future__ import annotations

import logging
import secrets
import typing
from typing import Callable, Optional

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from gi.repository import Gio, GLib

if typing.TYPE_CHECKING:
    from datetime import datetime


def format_time(time: Optional[datetime]) -> str:
    if not time:
        return ""

    timestamp = GLib.DateTime.new_local(
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second,
    )
    return timestamp.format("%e %b %Y %R")


def create_random_data(bytes_buffer):
    return secrets.token_bytes(bytes_buffer)


def generate_keyfile(gfile: Gio.File, callback: Callable[[], None]) -> None:
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(create_random_data(96))  # type: ignore
    contents = cipher.nonce + tag + ciphertext  # type: ignore

    success, _ = gfile.replace_contents(
        contents, None, False, Gio.FileCreateFlags.REPLACE_DESTINATION, None
    )

    if not success:
        logging.debug("Could not create keyfile")

    callback()
