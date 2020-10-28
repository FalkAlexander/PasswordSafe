import secrets
import string
import pwquality


def generate(
        digits: int, high_letter: bool, low_letter: bool, numbers: bool,
        special: bool) -> str:
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

    if high_letter is True:
        characters += string.ascii_uppercase

    if low_letter is True:
        characters += string.ascii_lowercase

    if numbers is True:
        characters += string.digits

    if special is True:
        characters += string.punctuation

    if characters == "":
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation

    return "".join([secrets.choice(characters) for _ in range(0, digits)])


def strength(password: str) -> float:
    """Get strength of a password between 0 and 5.

    The higher the score is, the more secure the password is.

    :param str password: password to test
    :returns: strength of password
    :rtype: float
    """
    try:
        score: int = pwquality.PWQSettings().check(password)
    except Exception:
        score = 0

    return score / 20
