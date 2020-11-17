# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import typing
from typing import Dict, List, Optional
from uuid import UUID

from gi.repository import GObject
from pykeepass.attachment import Attachment
from pykeepass.entry import Entry
from pykeepass.group import Group

from passwordsafe.color_widget import Color
if typing.TYPE_CHECKING:
    from passwordsafe.database_manager import DatabaseManager


class SafeEntry(GObject.GObject):
    # pylint: disable=too-many-instance-attributes

    _color_key = "color_prop_LcljUMJZ9X"
    _note_key = "Notes"

    def __init__(self, db_manager: DatabaseManager, entry: Entry) -> None:
        """GObject to handle a safe entry.

        :param DatabaseManager db_manager:  database of the entry
        :param Entry entry: entry to handle
        """
        super().__init__()

        self._db_manager: DatabaseManager = db_manager
        self._entry: Entry = entry

        self._attachments: List[Attachment] = entry.attachments or []

        self._attributes: Dict[str, str] = {
            key: value for key, value in entry.custom_properties.items()
            if key not in (self._color_key, self._note_key)}

        color_value: Color = entry.get_custom_property(self._color_key)
        self._color: str = color_value or Color.NONE.value

        self._icon: int = int(entry.icon)
        self._name: str = entry.title or ""
        self._notes: str = entry.notes or ""
        self._password: str = entry.password or ""
        self._url: str = entry.url or ""
        self._username: str = entry.username or ""

    @property
    def entry(self) -> Entry:
        """Get entry

        :returns: entry
        :rtype: Entry
        """
        return self._entry

    @property
    def uuid(self) -> UUID:
        """UUID of the entry

        :returns: uuid of the entry
        :rtype: Group
        """
        return self._entry.uuid

    @property
    def parentgroup(self) -> Group:
        """Parent Group of the entry

        :returns: parent group
        :rtype: Group
        """
        return self._entry.parentgroup

    @GObject.Property(
        type=object, flags=GObject.ParamFlags.READABLE)
    def attachments(self) -> List[Attachment]:
        return self._attachments

    def add_attachment(self, byte_buffer: bytes, filename: str) -> Attachment:
        """Add an attachment to the entry

        :param bytes byte_buffer: attachment content
        :param str filename: attachment name
        :returns: attachment
        :rtype: Attachment
        """
        attachment_id = self._db_manager.db.add_binary(byte_buffer)
        attachment = self._entry.add_attachment(attachment_id, filename)
        self._attachments.append(attachment)
        self._db_manager.is_dirty = True

        return attachment

    def delete_attachment(self, attachment: Attachment) -> None:
        """Remove an attachment from the entry

        :param Attachmennt attachment: attachment to delete
        """
        self._db_manager.db.delete_binary(attachment.id)
        self._attachments.remove(attachment)
        self._db_manager.is_dirty = True

    def get_attachment(self, id_: str) -> Optional[Attachment]:
        """Get an attachment from its id.

        :param str id_: attachment id
        :returns: attachment
        :rtype: Attachment
        """
        for attachment in self._attachments:
            if str(attachment.id) == id_:
                return attachment

        return None

    def get_attachment_content(self, attachment: Attachment) -> bytes:
        """Get an attachment content

        :param Attachmennt attachment: attachment
        """
        return self._db_manager.db.binaries[attachment.id]

    @GObject.Property(
        type=object, flags=GObject.ParamFlags.READABLE)
    def attributes(self) -> Dict[str, str]:
        return self._attributes

    def has_attribute(self, key: str) -> bool:
        """Check if an attribute exists.

        :param str key: attribute key to check
        """
        return key in self._attributes

    def set_attribute(self, key: str, value: str) -> None:
        """Add or replace an entry attribute

        :param str key: attribute key
        :param str value: attribute value
        """
        self._entry.set_custom_property(key, value)
        self._attributes[key] = value
        self._db_manager.is_dirty = True
        self._db_manager.set_element_mtime(self._entry)

    def delete_attribute(self, key: str) -> None:
        """Delete an attribute

        :param key: attribute key to delete
        """
        if not self.has_attribute(key):
            return

        self._entry.delete_custom_property(key)
        self._attributes.pop(key)
        self._db_manager.is_dirty = True
        self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, flags=GObject.ParamFlags.READWRITE)
    def color(self) -> str:
        """Get entry color

        :returns: color as string
        :rtype: str
        """
        return self._color

    @color.setter  # type: ignore
    def color(self, new_color: str) -> None:
        """Set an entry color

        :param str new_color: new color as string
        """
        if new_color != self._color:
            self._color = new_color
            self._entry.set_custom_property(self._color_key, new_color)
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    def icon(self) -> int:
        """Get icon number

        :returns: icon number or 0 if no icon
        :rtype: int
        """
        return self._icon

    @icon.setter  # type: ignore
    def icon(self, new_icon: int) -> None:
        """Set icon number

        :param str new_icon: new icon number
        """
        if new_icon != self._icon:
            self._icon = new_icon
            self._entry.icon = str(new_icon)
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)
    def name(self) -> str:
        """Get entry title

        :returns: title or an empty string if there is none
        :rtype: str
        """
        return self._name

    @name.setter  # type: ignore
    def name(self, new_name: str) -> None:
        """Set entry title

        :param str new_name: new title
        """
        if new_name != self._name:
            self._name = new_name
            self._entry.title = new_name
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)
    def notes(self) -> str:
        """Get entry notes

        :returns: notes or an empty string if there is none
        :rtype: str
        """
        return self._notes

    @notes.setter  # type: ignore
    def notes(self, new_notes: str) -> None:
        """Set entry notes

        :param str new_notes: new notes
        """
        if new_notes != self._notes:
            self._notes = new_notes
            self._entry.notes = new_notes
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)
    def password(self) -> str:
        """Get entry password

        :returns: password or an empty string if there is none
        :rtype: str
        """
        return self._password

    @password.setter  # type: ignore
    def password(self, new_password: str) -> None:
        """Set entry password

        :param str new_password: new password
        """
        if new_password != self._password:
            self._password = new_password
            self._entry.password = new_password
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)
    def url(self) -> str:
        """Get entry url

        :returns: url or an empty string if there is none
        :rtype: str
        """
        return self._url

    @url.setter  # type: ignore
    def url(self, new_url: str) -> None:
        """Set entry url

        :param str new_url: new url
        """
        if new_url != self._url:
            self._url = new_url
            self._entry.url = new_url
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)

    @GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE)
    def username(self) -> str:
        """Get entry username

        :returns: username or an empty string if there is none
        :rtype: str
        """
        return self._username

    @username.setter  # type: ignore
    def username(self, new_username: str) -> None:
        """Set entry username

        :param str new_username: new username
        """
        if new_username != self._username:
            self._username = new_username
            self._entry.username = new_username
            self._db_manager.is_dirty = True
            self._db_manager.set_element_mtime(self._entry)
