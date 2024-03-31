# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import GObject


class BaseProvider(GObject.Object):
    __gtype_name__ = "BaseProvider"

    show_message = GObject.Signal(arg_types=(str,))
    hide_message = GObject.Signal(arg_types=())

    def __init__(self):
        super().__init__()

        self.raw_key = None

    @property
    def available(self) -> bool:
        return False

    @property
    def key(self) -> bytes:
        return self.raw_key

    def config(self) -> dict:
        return {}

    def clear_input_fields(self) -> None:
        pass
