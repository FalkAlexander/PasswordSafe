import math
import secrets
import string
import re

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

def entropy(password):
    val = math.log(math.pow(len(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation), len(password)), 2)
    if val < 40:
        return 1
    elif val < 80:
        return 2
    elif val < 120:
        return 3
    elif val < 160:
        return 4
    elif val <= 200:
        return 5
    elif val > 200:
        return 6
    else:
        return 0
        
