# SPDX-License-Identifier: GPL-3.0-only

from collections import OrderedDict

from gi.repository import Gio, GObject


class Attribute(GObject.Object):
    __gtype_name__ = "Attribute"

    def __init__(self, key, value):
        super().__init__()

        self.key = key
        self.value = value


class AttributesModel(GObject.Object, Gio.ListModel):
    __gtype_name__ = "AttributesModel"

    def __init__(self, attributes: dict[str, str]) -> None:
        super().__init__()

        self._inner = OrderedDict()
        for key, value in attributes.items():
            self._inner[key] = Attribute(key, value)

        self.items_changed(0, 0, len(attributes))

    def do_get_item(self, pos):
        if 0 <= pos < self.get_n_items():
            key = list(self._inner)[pos]
            return self._inner[key]

        return None

    def do_get_n_items(self):
        return len(self._inner)

    def do_get_item_type(self):
        return Attribute.__gtype__  # pylint: disable=no-member

    def get(self, key: str) -> str | None:
        return self._inner.get(key)

    def _get_pos(self, key: str) -> int:
        return list(self._inner).index(key)

    def has_attribute(self, key: str) -> bool:
        return key in self._inner

    def insert(self, key: str, value: str) -> None:
        if key in self._inner:
            self._inner[key].value = value
        else:
            n_items = self.get_n_items()
            self._inner[key] = Attribute(key, value)
            self.items_changed(n_items, 0, 1)

    def pop(self, key: str) -> Attribute | None:
        if key not in self._inner:
            return None

        pos = self._get_pos(key)
        attribute = self._inner.pop(key)
        self.items_changed(pos, 1, 0)
        return attribute
