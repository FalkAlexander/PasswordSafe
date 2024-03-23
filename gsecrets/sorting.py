# SPDX-License-Identifier: GPL-3.0-only
# Functions to sort a List Model with groups and entries.

from __future__ import annotations

import typing
from enum import IntEnum

from gi.repository import GLib, Gtk

if typing.TYPE_CHECKING:
    from gsecrets.safe_element import SafeElement


class SortingHat:
    """Provides a variety of sorting algorithms."""

    class SortOrder(IntEnum):
        ASC = 0
        DEC = 1
        CTIME_ASC = 2
        CTIME_DEC = 3

    # will be set from just below the class
    sort_funcs: dict[SortOrder, typing.Callable] = {}

    @staticmethod
    def get_sorter(order: SortOrder) -> typing.Callable:
        sort_func = SortingHat.sort_funcs[order]
        return Gtk.CustomSorter.new(sort_func)

    @staticmethod
    def sort_by_name_asc(
        ele1: SafeElement,
        ele2: SafeElement,
        _data: object = None,
    ) -> int:
        return GLib.ascii_strcasecmp(ele1.name, ele2.name)

    @staticmethod
    def sort_by_name_dec(
        ele1: SafeElement,
        ele2: SafeElement,
        _data: object = None,
    ) -> int:
        return GLib.ascii_strcasecmp(ele2.name, ele1.name)

    @staticmethod
    def sort_by_ctime_asc(
        ele1: SafeElement,
        ele2: SafeElement,
        _data: object = None,
    ) -> int:
        if ele1.ctime is not None and ele2.ctime is not None:
            return ele1.ctime.compare(ele2.ctime)
        if ele1.ctime is None and ele2.ctime is not None:
            return 1
        if ele1.ctime is not None and ele2.ctime is None:
            return -1

        return 0

    @staticmethod
    def sort_by_ctime_dec(
        ele1: SafeElement,
        ele2: SafeElement,
        _data: object = None,
    ) -> int:
        if ele1.ctime is not None and ele2.ctime is not None:
            return ele2.ctime.compare(ele1.ctime)
        if ele1.ctime is None and ele2.ctime is not None:
            return -1
        if ele1.ctime is not None and ele2.ctime is None:
            return 1

        return 0


SortingHat.sort_funcs = {
    SortingHat.SortOrder.ASC: SortingHat.sort_by_name_asc,
    SortingHat.SortOrder.DEC: SortingHat.sort_by_name_dec,
    SortingHat.SortOrder.CTIME_ASC: SortingHat.sort_by_ctime_asc,
    SortingHat.SortOrder.CTIME_DEC: SortingHat.sort_by_ctime_dec,
}
