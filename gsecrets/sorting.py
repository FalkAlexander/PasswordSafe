# SPDX-License-Identifier: GPL-3.0-only
# Functions to sort a List Model with groups and entries.

from __future__ import annotations

import typing
from enum import IntEnum

from gi.repository import Gtk

from gsecrets.safe_element import SafeElement


class SortingHat:
    """Provides a variety of sorting algorithms."""

    class SortOrder(IntEnum):
        ASC = 0
        DEC = 1
        CTIME_ASC = 2
        CTIME_DEC = 3

    @staticmethod
    def get_sorter(order: SortOrder) -> typing.Callable:
        match order:
            case SortingHat.SortOrder.ASC:
                expr = Gtk.PropertyExpression.new(SafeElement.__gtype__, None, "name")
                return Gtk.StringSorter.new(expr)
            case SortingHat.SortOrder.DEC:
                expr = Gtk.PropertyExpression.new(SafeElement.__gtype__, None, "name")
                return Gtk.StringSorter.new(expr)
            case SortingHat.SortOrder.CTIME_ASC:
                expr = Gtk.PropertyExpression.new(
                    SafeElement.__gtype__, None, "ctime_int"
                )
                return Gtk.NumericSorter.new(expr)
            case SortingHat.SortOrder.CTIME_DEC:
                expr = Gtk.PropertyExpression.new(
                    SafeElement.__gtype__, None, "ctime_int"
                )
                sorter = Gtk.NumericSorter.new(expr)
                sorter.props.sort_order = Gtk.SortType.DESCENDING
                return sorter
