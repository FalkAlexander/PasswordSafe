# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import secrets
import string
import threading
import typing

from gi.repository import GLib
from zxcvbn_rs_py import zxcvbn

if typing.TYPE_CHECKING:
    from collections.abc import Callable


def _satisfies_requirements(
    password: str,
    use_uppercase: bool,
    use_lowercase: bool,
    use_numbers: bool,
    use_symbols: bool,
) -> bool:
    if use_uppercase and not any(c.isupper() for c in password):
        return False

    if use_lowercase and not any(c.islower() for c in password):
        return False

    if use_numbers and not any(c.isdigit() for c in password):
        return False

    if use_symbols and not any(not c.isalnum() for c in password):  # noqa: SIM103
        return False

    return True


def generate(
    length: int,
    use_uppercase: bool,
    use_lowercase: bool,
    use_numbers: bool,
    use_symbols: bool,
) -> str:
    """Generate a password based on some criteria.

    :param int digits: password number of characters
    :param bool high_letter: password must contain uppercase letters
    :param bool low_letter: password must contain low letters
    :param bool numbers: password must contain digits
    :param bool special: password must contain special characters
    :returns: a password
    :rtype: str
    """
    characters: str = ""

    if use_uppercase:
        characters += string.ascii_uppercase

    if use_lowercase:
        characters += string.ascii_lowercase

    if use_numbers:
        characters += string.digits

    if use_symbols:
        characters += string.punctuation

    # If all options are disabled, generate a password using
    # arbitrary ASCII characters.
    # TODO Revisit this. It might be a sane default, but
    # it is highly un-intuitive.
    if characters == "":
        characters = (
            string.ascii_uppercase
            + string.ascii_lowercase
            + string.digits
            + string.punctuation
        )

    while True:
        password = "".join([secrets.choice(characters) for _ in range(length)])
        if _satisfies_requirements(
            password,
            use_uppercase,
            use_lowercase,
            use_numbers,
            use_symbols,
        ):
            return password


def strength(password: str) -> int:
    """Get strength of a password between 0 and 4.

    The higher the score is, the more secure the password is.

    :param str password: password to test
    :returns: strength of password
    :rtype: int
    """
    if password:
        return int(zxcvbn(password).score)

    return 0


def _threaded_compute_strength(password: str, callback: Callable[[int], None]) -> None:
    score = strength(password)
    GLib.idle_add(callback, score)


def strength_async(password: str, callback: Callable[[int], None]) -> None:
    if password:
        thread = threading.Thread(
            target=_threaded_compute_strength,
            args=[password, callback],
        )
        thread.daemon = True
        thread.start()
    else:
        callback(0)
