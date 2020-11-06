# SPDX-License-Identifier: GPL-3.0-only
import logging
from secrets import randbelow
from typing import List
from gi.repository import Gio, GLib


def generate(num_words: int, separator: str) -> str:
    """Generate a passphrase.

    :param int num_words: number of words requested
    :param str separator: separator
    :returns: a passphrase
    :rtype: str

    """
    word_file: Gio.File = Gio.File.new_for_uri(
        "resource:///org/gnome/PasswordSafe/crypto/eff_large_wordlist.txt"
    )
    f_buffer: GLib.Bytes = Gio.InputStream.read_bytes(word_file.read(), 108800)
    word_str: str = f_buffer.get_data().decode("utf-8")

    word_list: List[str] = word_str.split("\n")
    len_words: int = len(word_list)

    rand_words = [word_list[randbelow(len_words)] for _ in range(0, num_words)]
    passphrase: str = separator.join(rand_words)
    logging.debug(
        "Created passphrase with %d words and separator '%s'", num_words, separator
    )
    return passphrase
