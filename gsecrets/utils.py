# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import os
import secrets
import stat
import typing
from gettext import gettext as _

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes

from gi.repository import Gio, GLib, Gtk

if typing.TYPE_CHECKING:
    from typing import Tuple


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


def generate_keyfile_sync(gfile: Gio.File) -> str:
    """The callback returns a GFile as its source object and the keyfile hash as
    its user_data. Returns the hash of the keyfile."""
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(create_random_data(96))  # type: ignore
    contents = cipher.nonce + tag + ciphertext  # type: ignore
    keyfile_hash = GLib.compute_checksum_for_data(GLib.ChecksumType.SHA1, contents)

    flags = Gio.FileCreateFlags.REPLACE_DESTINATION | Gio.FileCreateFlags.PRIVATE
    gfile.replace_contents(contents, None, False, flags, None)
    # Sets the file as read-only
    os.chmod(gfile.get_path(), stat.S_IREAD)

    return keyfile_hash


def generate_keyfile_async(gfile: Gio.File, callback: Gio.AsyncReadyCallback) -> None:
    def generate_keyfile_task(task, obj, _data, _cancellable):
        try:
            keyfile_hash = generate_keyfile_sync(obj)
        except GLib.Error as err:  # pylint: disable=broad-except
            task.return_error(err)
        else:
            task.return_value(keyfile_hash)

    task = Gio.Task.new(gfile, None, callback)
    task.run_in_thread(generate_keyfile_task)


def generate_keyfile_finish(result: Gio.AsyncResult) -> Tuple[bool, str]:
    return result.propagate_value()


def compare_passwords(pass1: str | None, pass2: str | None) -> bool:
    if pass1 is not None and pass2 is not None:
        return secrets.compare_digest(
            bytes(pass1, 'utf-8'), bytes(pass2, 'utf-8')
        )

    if pass1 is None and pass2 is None:
        return True

    return False


class KeyFileFilter:
    """Filter out Keyfiles in the file chooser dialog"""

    def __init__(self):
        self.file_filter = Gtk.FileFilter()

        self.file_filter.set_name(_("Keyfile"))
        self.file_filter.add_mime_type("application/octet-stream")
        self.file_filter.add_mime_type("application/x-keepass2")
        self.file_filter.add_mime_type("text/plain")
        self.file_filter.add_mime_type("application/x-iwork-keynote-sffkey")
