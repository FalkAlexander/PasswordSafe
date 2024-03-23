# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from gsecrets.password_generator import strength_async


class PasswordLevelBar(Adw.Bin):
    __gtype_name__ = "PasswordLevelBar"

    _password: str = ""

    def __init__(self) -> None:
        super().__init__()

        self.level_bar = Gtk.LevelBar()
        self.level_bar.update_property(
            [Gtk.AccessibleProperty.LABEL],
            [_("Password Strength")],
        )

        self.level_bar.props.max_value = 4.0
        self.level_bar.props.mode = Gtk.LevelBarMode.DISCRETE

        # Values in a discrete mode are rounded
        # instead of using a floor function.
        self.level_bar.add_offset_value("insecure", 0.49)
        self.level_bar.add_offset_value("weak", 1.49)
        self.level_bar.add_offset_value("medium", 2.49)
        self.level_bar.add_offset_value("strong", 3.49)
        self.level_bar.add_offset_value("secure", 4.0)

        self.set_child(self.level_bar)

    @GObject.Property(type=str, default="")
    def password(self) -> str:
        return self._password

    @password.setter  # type: ignore
    def password(self, password: str) -> None:
        self._password = password

        def on_password(strength):
            self.level_bar.props.value = strength

        strength_async(password, on_password)
