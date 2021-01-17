#!/usr/bin/env python3
from __future__ import annotations

import typing
from typing import Optional

from gi.repository import GLib

if typing.TYPE_CHECKING:
    from datetime import datetime


def format_time(time: Optional[datetime]) -> str:
    if not time:
        return ""

    timestamp = GLib.DateTime.new_local(
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second,
    )
    return timestamp.format("%e %b %Y %R")
