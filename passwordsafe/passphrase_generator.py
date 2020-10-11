from gi.repository import Gio
import re
import secrets

word_dict = {}


def generate(words, separator):
    words_file = Gio.File.new_for_uri("resource:///org/gnome/PasswordSafe/crypto/eff_large_wordlist.txt")
    file_buffer = Gio.InputStream.read_bytes(words_file.read(), 108800)
    unicode_str = file_buffer.get_data().decode("utf-8", "ignore")

    word_list = unicode_str.split("\n")
    for line in word_list:
        split = re.split(r'\t+', line)

        if split != ['']:
            word_dict[split[0]] = split[1]

    passphrase = ""

    for i in range(words):
        passphrase += get_word(dice())
        if i + 1 < words:
            passphrase += separator

    return passphrase


def dice():
    return "".join([secrets.choice("123456") for _ in range(0, 5)])


def get_word(number):
    return word_dict[number]
