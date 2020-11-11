# SPDX-License-Identifier: GPL-3.0-only
import secrets
import string
from typing import Optional
import pwquality

import passwordsafe.config_manager as config


def generate() -> str:
    """Generate a password based on some criteria.

    :returns: a password
    :rtype: str
    """
    length = config.get_generator_length()
    characters: str = ""

    if config.get_generator_use_uppercase():
        characters += string.ascii_uppercase

    if config.get_generator_use_lowercase():
        characters += string.ascii_lowercase

    if config.get_generator_use_numbers():
        characters += string.digits

    if config.get_generator_use_symbols():
        characters += string.punctuation

    # If all options are disabled, generate a password using
    # arbitrary ASCII characters.
    # TODO Revisit this. It might be a sane default, but
    # it is highly un-intuitive.
    if characters == "":
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation

    return "".join([secrets.choice(characters) for _ in range(0, length)])


def strength(password: str) -> Optional[float]:
    """Get strength of a password between 0 and 5.

    The higher the score is, the more secure the password is.

    :param str password: password to test
    :returns: strength of password or None on pwquality error
    :rtype: float
    """
    try:
        if password:
            score = pwquality.PWQSettings().check(password)
        else:
            score = 0
    except pwquality.PWQError:
        return None

    return score / 20
