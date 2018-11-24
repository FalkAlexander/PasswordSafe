from gi.repository import Gio
import cffi
import os
import sys

class NitroKey():
    ffi = cffi.FFI()
    native_lib = NotImplemented

    def __init__(self):
        self.libnitrokey_native()

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
            print("libnitrokey.so not found")

        if self.native_lib is NotImplemented:
            print("Native Library Missing")

    def get_hotp_code(self, slot):
        return self.ffi.string(self.native_lib.NK_get_hotp_code(slot))

