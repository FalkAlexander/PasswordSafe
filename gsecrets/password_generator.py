# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import secrets
import string

import pwquality


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

    return "".join([secrets.choice(characters) for _ in range(0, length)])


def strength(password: str) -> float:
    """Get strength of a password between 0 and 5.

    The higher the score is, the more secure the password is.

    :param str password: password to test
    :returns: strength of password or None on pwquality error
    :rtype: float
    """
    # TODO The settings should be set so the strength of the
    # password is still being computed on certain errors.
    # For the list of error codes see:
    # https://github.com/libpwquality/libpwquality/blob/master/src/pwquality.h
    try:
        if password:
            score = pwquality.PWQSettings().check(password)
        else:
            score = 0
    except pwquality.PWQError:
        score = 0

    return score / 20
