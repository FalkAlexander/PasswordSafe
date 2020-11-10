# SPDX-License-Identifier: GPL-3.0-only
from typing import Optional

icon_list = [
    "dialog-password-symbolic",  # 00
    "network-wired-symbolic",  # 01
    "dialog-warning-symbolic",  # 02
    "network-server-symbolic",
    "document-edit-symbolic",
    "media-view-subtitles-symbolic",
    "application-x-addon-symbolic",
    "accessories-text-editor-symbolic",
    "network-wired-symbolic",
    "mail-send-symbolic",
    "text-x-generic-symbolic",  # 10
    "camera-photo-symbolic",
    "network-wireless-signal-excellent-symbolic",
    "dialog-password-symbolic",
    "colorimeter-colorhug-symbolic",
    "scanner-symbolic",
    "network-wired-symbolic",
    "media-optical-cd-audio-symbolic",
    "video-display-symbolic",
    "mail-unread-symbolic",
    "emblem-system-symbolic",  # 20
    "edit-paste-symbolic",
    "edit-paste-symbolic",
    "preferences-desktop-remote-desktop-symbolic",
    "uninterruptible-power-supply-symbolic",
    "mail-unread-symbolic",
    "media-floppy-symbolic",
    "drive-harddisk-symbolic",
    "dialog-password-symbolic",
    "dialog-password-symbolic",
    "utilities-terminal-symbolic",  # 30
    "printer-symbolic",
    "image-x-generic-symbolic",
    "edit-select-all-symbolic",
    "preferences-system-symbolic",
    "network-workgroup-symbolic",
    "dialog-password-symbolic",
    "dialog-password-symbolic",
    "drive-harddisk-symbolic",
    "document-open-recent-symbolic",
    "system-search-symbolic",  # 40
    "dialog-password-symbolic",
    "media-flash-symbolic",
    "user-trash-symbolic",
    "accessories-text-editor-symbolic",
    "edit-delete-symbolic",
    "dialog-question-symbolic",
    "package-x-generic-symbolic",
    "folder-symbolic",
    "folder-open-symbolic",
    "document-open-symbolic",  # 50
    "system-lock-screen-symbolic",
    "rotation-locked-symbolic",
    "object-select-symbolic",
    "document-edit-symbolic",
    "image-x-generic-symbolic",
    "accessories-dictionary-symbolic",
    "view-list-symbolic",
    "avatar-default-symbolic",
    "applications-engineering-symbolic",
    "go-home-symbolic",  # 60
    "starred-symbolic",  # 61
    "start-here-symbolic",  # 62
    "dialog-password-symbolic",  # 63
    "start-here-symbolic",  # 64
    "accessories-dictionary-symbolic",  # 65
    "dialog-password-symbolic",  # 66
    "application-certificate-symbolic",  # 67
    "phone-apple-iphone-symbolic",  # 68
]


def get_icon_name(number: Optional[int]) -> str:
    """Return icons symbolic name

    or the default icon in case of an invalid index"""
    # use default icon if number is None or out of range
    if number is None:
        number = 0
    if number < 0 or number > 68:
        number = 0
    return icon_list[number]
