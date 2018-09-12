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

def strength(password):
    di = diversity(password)
    en = entropy(password)

    strength = int(round((di + en) / 2, 0))
    if strength <= 6:
        return strength
    elif strenth > 6:
        return 6
    else:
        return 0

def diversity(password):
    if len(password) <= 3:
        return 0

    if len(password) <= 6:
        if any(i.isdigit() for i in password) and any(i.isupper() for i in password) and any(i.islower() for i in password):
            return 2
        else:
            return 1

    if len(password) >= 7:
        count = 1
        if any(i.isdigit() for i in password):
            if sum(i.isdigit() for i in password) >= 2:
                count += 2
            else:
                count += 1
        if any(i.isupper() for i in password):
            if sum(i.isupper() for i in password) >= 2:
                count += 2
            else:
                count += 1
        if(re.compile('[@_!#$%^&*()<>?/\|}{~:]').search(password) != None):
            count += 1

        return count


def entropy(password):
    passwd_length = len(password)
    if passwd_length > 156:
        passwd_length = 156

    val = math.log(math.pow(len(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation), passwd_length), 2)
    if val < 40:
        return 1
    elif val < 80:
        return 2
    elif val < 120:
        return 3
    elif val < 160:
        return 4
    elif val < 200:
        return 5
    elif val < 250:
        return 6
    else:
        return 6
