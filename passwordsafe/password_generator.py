import string
from random import *

def generate(digits, high_letter, low_letter, numbers, special):
    characters = ""
    
    if high_letter is True:
        characters = characters + string.ascii_uppercase

    if low_letter is True:
        characters = characters + string.ascii_lowercase

    if numbers is True:
        characters = characters + string.digits

    if special is True:
        characters = characters + string.punctuation

    if characters == "":
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation

    password = "".join(choice(characters) for i in range(digits))
    return password
