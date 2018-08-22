import secrets

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
