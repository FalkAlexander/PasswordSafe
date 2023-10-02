# SPDX-License-Identifier: GPL-3.0-only
class BaseProvider:
    def __init__(self):
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
