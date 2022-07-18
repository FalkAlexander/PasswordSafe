# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import GObject, Gtk

from gsecrets.password_generator import strength_async


class PasswordLevelBar(Gtk.LevelBar):

    __gtype_name__ = "PasswordLevelBar"

    _password: str = ""

    def __init__(self) -> None:
        super().__init__()

        self.props.max_value = 4.0
        self.props.mode = Gtk.LevelBarMode.DISCRETE

        # Values in a discrete mode are rounded
        # instead of using a floor function.
        self.add_offset_value("insecure", 0.49)
        self.add_offset_value("weak", 1.49)
        self.add_offset_value("medium", 2.49)
        self.add_offset_value("strong", 3.49)
        self.add_offset_value("secure", 4.0)

    @GObject.Property(type=str, default="")
    def password(self) -> str:
        return self._password

    @password.setter  # type: ignore
    def password(self, password: str) -> None:
        self._password = password

        def on_password(strength):
            self.props.value = strength

        strength_async(password, on_password)
