from gi.repository import GLib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import secrets

def create_random_data():
    return secrets.token_bytes(500)

def generate_keyfile(filepath, database_creation, instance):
    key = get_random_bytes(32)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(create_random_data())

    file_out = open(filepath, "wb")
    [ file_out.write(x) for x in (cipher.nonce, tag, ciphertext) ]

    if database_creation is True:
        instance.database_manager.set_database_keyfile(filepath)
        instance.database_manager.save_database()
        GLib.idle_add(instance.set_database_keyfile)
