# SPDX-License-Identifier: GPL-3.0-only
"""Generate a passphrase from a list of predefined words."""

from __future__ import annotations

import logging
from secrets import randbelow

from gi.repository import Gio, GLib, GObject


class Passphrase(GObject.Object):
    """Generate a passphrase from a list of predefined words."""

    _word_file_data = None

    def generate(self, num_words: int, separator: str = "-") -> None:
        """Generate a passphrase.

        :param int num_words: number of words requested
        :param str separator: separator
        """
        if data := self._word_file_data:
            self._parse_data(data)
            return

        word_file: Gio.File = Gio.File.new_for_uri(
            "resource:///org/gnome/World/Secrets/crypto/eff_large_wordlist.txt",
        )

        def callback(gfile: Gio.File, result: Gio.AsyncResult) -> None:
            try:
                gbytes, _ = gfile.load_bytes_finish(result)
            except GLib.Error:
                logging.exception("Could not read word file")
            else:
                self._word_file_data = gbytes
                self._parse_data(gbytes, num_words, separator)

        word_file.load_bytes_async(None, callback)

    @GObject.Signal(arg_types=(str,))
    def generated(self, _passphrase):
        return

    def _parse_data(
        self,
        gbytes: GLib.Bytes,
        num_words: int,
        separator: str = "-",
    ) -> None:
        word_str: str = gbytes.get_data().decode("utf-8")
        word_list: list[str] = word_str.split("\n")
        len_words: int = len(word_list)

        words = [word_list[randbelow(len_words)] for _ in range(num_words)]
        passphrase: str = separator.join(words) or ""
        self.emit("generated", passphrase)
