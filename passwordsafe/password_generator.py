import secrets
import re

def generate(digits, high_letter, low_letter, numbers, special):
    characters = ""
    
    if high_letter is True:
        characters += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if low_letter is True:
        characters += "abcdefghijklmnopqrstuvwxyz"

    if numbers is True:
        characters += "0123456789"

    if special is True:
        characters += "?!@#$%`<|>^&*()-_.:;,#*+~’§/\={}"

    if characters == "":
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789?!@#$%`<|>^&*()-_.:;,#*+~’§/\={}"

    return "".join([secrets.choice(characters) for _ in range(0, digits)])

def strength(password):
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
        
