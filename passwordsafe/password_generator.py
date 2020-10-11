import secrets
import string
import pwquality


def generate(digits, high_letter, low_letter, numbers, special):
    characters = ""

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


def strength(password):
    score = NotImplemented

    try:
        score = pwquality.PWQSettings().check(password)
    except Exception:
        score = 0

    return score / 20
