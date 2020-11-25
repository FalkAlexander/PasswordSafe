# SPDX-License-Identifier: GPL-3.0-only
from typing import Optional

icon_list = {
    "0": "dialog-password-symbolic",
    "1": "network-wired-symbolic",
    "9": "mail-send-symbolic",
    "12": "network-wireless-signal-excellent-symbolic",
    "19": "mail-unread-symbolic",
    "23": "preferences-desktop-remote-desktop-symbolic",
    "27": "drive-harddisk-symbolic",
    "30": "utilities-terminal-symbolic",
    "34": "preferences-system-symbolic",
    "48": "folder-symbolic"
}


def get_icon_name(number: Optional[int]) -> str:
    """Return icons symbolic name

    or the default icon in case of an invalid index"""
    # use default icon if number is None or out of range
    if number is None:
        number = 0
    try:
        return icon_list[str(number)]
    except KeyError:
        return icon_list["0"]
