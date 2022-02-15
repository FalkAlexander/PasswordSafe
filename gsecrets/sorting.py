# SPDX-License-Identifier: GPL-3.0-only
# Functions to sort a List Model with groups and entries.

from __future__ import annotations

import typing
from enum import IntEnum

from gi.repository import GLib, Gtk

from gsecrets.safe_element import SafeElement


class SortingHat:
    """Provides a variety of sorting algorithms"""

    class SortOrder(IntEnum):
        ASC = 0
        DEC = 1
        CTIME_ASC = 2
        CTIME_DEC = 3

    # will be set from just below the class
    sort_funcs: typing.Dict[SortOrder, typing.Callable] = {}
    sorters: typing.Dict[SortOrder, Gtk.Sorter] = {}

    builder = Gtk.Builder.new_from_resource(
        "/org/gnome/World/Secrets/gtk/sorting.ui"
    )
    asc_sort = builder.get_object("asc_sort")
    ctime_sort = builder.get_object("ctime_sort")

    @staticmethod
    def get_sort_func(order: SortOrder) -> typing.Callable:
        return SortingHat.sort_funcs[order]

    @staticmethod
    def get_sorter(order: SortOrder) -> Gtk.Sorter:
        return SortingHat.sorters[order]

    @staticmethod
    def sort_by_name_asc(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1

        return GLib.ascii_strcasecmp(ele1.name, ele2.name)

    @staticmethod
    def sort_by_name_dec(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1

        return GLib.ascii_strcasecmp(ele2.name, ele1.name)

    @staticmethod
    def sort_by_ctime_asc(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.ctime is None or ele2.ctime is None:
            return 0
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1

        return ele1.ctime.compare(ele2.ctime)

    @staticmethod
    def sort_by_ctime_dec(ele1: SafeElement, ele2: SafeElement) -> int:
        # <0 if ele1<ele2, 0 if ele1=ele2, >0 ele1>ele2
        if ele1.ctime is None or ele2.ctime is None:
            return 0
        if ele1.is_group and ele2.is_entry:
            return -1
        if ele1.is_entry and ele2.is_group:
            return 1

        return ele2.ctime.compare(ele1.ctime)


SortingHat.sort_funcs = {
    SortingHat.SortOrder.ASC: SortingHat.sort_by_name_asc,
    SortingHat.SortOrder.DEC: SortingHat.sort_by_name_dec,
    SortingHat.SortOrder.CTIME_ASC: SortingHat.sort_by_ctime_asc,
    SortingHat.SortOrder.CTIME_DEC: SortingHat.sort_by_ctime_dec,
}

SortingHat.sorters = {
    SortingHat.SortOrder.ASC: SortingHat.asc_sort,
    SortingHat.SortOrder.DEC: SortingHat.asc_sort,
    SortingHat.SortOrder.CTIME_ASC: SortingHat.ctime_sort,
    SortingHat.SortOrder.CTIME_DEC: SortingHat.ctime_sort,
}
