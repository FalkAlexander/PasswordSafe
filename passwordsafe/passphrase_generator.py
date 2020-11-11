# SPDX-License-Identifier: GPL-3.0-only
import re
import secrets

from typing import List
from gi.repository import Gio, GLib

import passwordsafe.config_manager as config

word_dict = {}


def generate() -> str:
    """Generate a passphrase.

    :returns: a passphrase
    :rtype: str

    """
    words = config.get_generator_words()
    separator = config.get_generator_separator()

    words_file: Gio.File = Gio.File.new_for_uri(
        "resource:///org/gnome/PasswordSafe/crypto/eff_large_wordlist.txt")
    file_buffer: GLib.Bytes = Gio.InputStream.read_bytes(
        words_file.read(), 108800)
    unicode_str: str = file_buffer.get_data().decode("utf-8", "ignore")

    word_list: List[str] = unicode_str.split("\n")
    for line in word_list:
        split: List[str] = re.split(r'\t+', line)

        if split != ['']:
            word_dict[split[0]] = split[1]

    passphrase: str = ""

    for i in range(words):
        passphrase += get_word(dice())
        if i + 1 < words:
            passphrase += separator

    return passphrase


def dice():
    return "".join([secrets.choice("123456") for _ in range(0, 5)])


def get_word(number):
    return word_dict[number]
