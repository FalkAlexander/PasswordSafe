# SPDX-License-Identifier: GPL-3.0-only
# Functions to sort a List Model with groups and entries.

from __future__ import annotations

import typing
from enum import IntEnum

# from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Handy

from passwordsafe.safe_element import SafeElement


class SortingHat:
    """Provides a variety of sorting algorithms"""

    class SortOrder(IntEnum):
        ASC = 0
        DEC = 1
        CTIME_DEC = 2

    # will be set from just below the class
    sort_funcs: typing.Dict[SortOrder, typing.Callable] = {}

    @staticmethod
    def get_sort_func(order: SortOrder) -> typing.Callable:
        return SortingHat.sort_funcs[order]

    @staticmethod
    def sort_by_asc(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1
        if ele1.name.lower() < ele2.name.lower():
            return -1
        if ele1.name.lower() == ele2.name.lower():
            return 0
        return 1

    @staticmethod
    def sort_by_dec(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1
        if ele1.name.lower() < ele2.name.lower():
            return 1
        if ele1.name.lower() == ele2.name.lower():
            return 0
        return -1

    @staticmethod
    def sort_by_ctime_dec(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.ctime is None or ele2.ctime is None:
            return 0
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1
        if ele1.ctime < ele2.ctime:
            return 1
        if ele1.ctime == ele2.ctime:
            return 0
        return -1


SortingHat.sort_funcs = {
    SortingHat.SortOrder.ASC: SortingHat.sort_by_asc,
    SortingHat.SortOrder.DEC: SortingHat.sort_by_dec,
    SortingHat.SortOrder.CTIME_DEC: SortingHat.sort_by_ctime_dec,
}
