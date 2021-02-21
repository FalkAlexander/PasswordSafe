# SPDX-License-Identifier: GPL-3.0-only
"""Generate a passphrase from a list of predefined words."""
from __future__ import annotations

import logging
from secrets import randbelow

from gi.repository import Gio, GLib


class Passphrase:
    """Generate a passphrase from a list of predefined words."""

    def __init__(self, password: str = None):
        """password is the (optional) password to be stored"""
        self.password = password

    @classmethod
    def generate(cls, num_words: int, separator: str = "-") -> "Passphrase":
        """Generate a passphrase.

        :param int num_words: number of words requested
        :param str separator: separator
        :returns: a Passphrase() object
        :rtype: `Passphrase`
        """
        word_file: Gio.File = Gio.File.new_for_uri(
            "resource:///org/gnome/PasswordSafe/crypto/eff_large_wordlist.txt"
        )
        f_buffer: GLib.Bytes = Gio.InputStream.read_bytes(word_file.read(),
                                                          108800)
        word_str: str = f_buffer.get_data().decode("utf-8")
        word_list: list[str] = word_str.split("\n")
        len_words: int = len(word_list)

        words = [word_list[randbelow(len_words)] for _ in range(0, num_words)]
        passphrase: str = separator.join(words)
        logging.debug("Created passphrase with %d words and separator '%s'",
                      num_words, separator)
        return cls(passphrase)

    def __str__(self):
        """String representation of the passphrase"""
        return self.password or ""
