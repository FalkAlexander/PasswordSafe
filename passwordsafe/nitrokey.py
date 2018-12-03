from gi.repository import Gio
import cffi
import os
import passwordsafe.password_generator
import pyotp
import sys


class NitroKey():
    logging_manager = NotImplemented

    ffi = NotImplemented
    native_lib = NotImplemented

    device_connected = False
    temporary_password = NotImplemented

    def __init__(self, logging_manager):
        self.logging_manager = logging_manager

        self.ffi = cffi.FFI()
        self.libnitrokey_native()
        self.prepare_device()

    def libnitrokey_native(self):
        header_file = Gio.File.new_for_uri("resource:///org/gnome/PasswordSafe/native/NK_C_API.h")
        file_buffer = Gio.InputStream.read_bytes(header_file.read(), 16333)
        unicode_str = file_buffer.get_data().decode("utf-8", "ignore")

        interfaces = unicode_str.split("\n")

        i = iter(interfaces)
        for interface in i:
            if interface.strip().startswith("NK_C_API"):
                interface = interface.replace("NK_C_API", "").strip()
                while ";" not in interface:
                    interface += (next(i)).strip()

                self.ffi.cdef(interface, override=True)

        library_path = "/" + sys.path[1].split(os.sep)[1] + "/" + sys.path[1].split(os.sep)[2] + "/libnitrokey.so"

        if os.path.exists(library_path):
            self.native_lib = self.ffi.dlopen(library_path)
        else:
            self.logging_manager.info("libnitrokey.so not found in system library path")

    def prepare_device(self):
        if self.native_lib is NotImplemented:
            return

        if self.native_lib.NK_login_auto():
            self.device_connected = True
            self.temporary_password = passwordsafe.password_generator.generate(10, True, True, True, True)
            pin_correct = self.native_lib.NK_first_authenticate("passwd".encode("ascii"), self.temporary_password.encode("ascii"))
            if pin_correct:
                print("corrent pin")
            else:
                print("wrong pin")
                print("Tries left: " + str(self.native_lib.NK_get_admin_retry_count()))
            self.logging_manager.debug("NitroKey connected")
        else:
            self.logging_manager.debug("No NitroKey connected")

    def logout_device(self):
        self.native_lib.NK_logout()

    def get_hardware_token_identifier(self):
        return self.native_lib.NK_device_serial_number()

    def get_hotp_code(self):
        for i in range(0, 3):
            slot_bytes = self.ffi.string(self.native_lib.NK_get_hotp_slot_name(i))
            print(slot_bytes.decode("utf-8"))

            code = self.native_lib.NK_get_hotp_code(i)
            bytes = self.ffi.string(code)
            string = bytes.decode("utf-8")
            print(string)

            if self.native_lib.NK_get_hotp_slot_name(i) == "PasswordSafe":
                code = self.native_lib.NK_get_hotp_code(i)
                bytes = self.ffi.string(code)
                string = bytes.decode("utf-8")
                return string

        return None

    def create_hotp_slot(self):
        for i in range(0, 3):
            if self.ffi.string(self.native_lib.NK_get_hotp_code(i)).decode("utf-8") == "":
                self.native_lib.NK_write_hotp_slot(
                    i,
                    bytes("PasswordSafe", encoding="utf8"),
                    bytes(pyotp.random_base32(), encoding="utf8"),
                    8,
                    True,
                    False,
                    False,
                    bytes("", encoding="utf8"),
                    bytes(self.temporary_password, encoding="utf8"))
                return True

        return False

