# SPDX-License-Identifier: GPL-3.0-only
from enum import IntEnum

from gi.repository import GLib

QUARK = GLib.quark_from_string("secrets")


class ErrorType(IntEnum):
    UNSUPPORTED_FORMAT = 0
    UNKNOWN = 1
    CREDENTIALS_ERROR = 2

    def message(self):
        match self:
            case ErrorType.UNSUPPORTED_FORMAT:
                return "The kdb Format is not Supported"
            case ErrorType.UNKNOWN:
                return "Unknown error"
            case ErrorType.CREDENTIALS_ERROR:
                return "Invalid credentials"
            case _other:
                msg = "Unrecognized error"
                raise ValueError(msg)


def generic_error(msg):
    return GLib.Error.new_literal(QUARK, msg, ErrorType.UNKNOWN)


def error(type_):
    return GLib.Error.new_literal(QUARK, type_.message(), type_)
