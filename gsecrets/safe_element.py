# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import binascii
import logging
import typing

from datetime import datetime, timezone
from typing import NamedTuple
from uuid import UUID

from gi.repository import GLib, GObject
from pyotp import OTP, TOTP, parse_uri

from gsecrets.color_widget import Color

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment
    from pykeepass.entry import Entry
    from pykeepass.group import Group

    from gsecrets.database_manager import DatabaseManager  # pylint: disable=ungrouped-imports # noqa: E501


class SafeElement(GObject.GObject):

    sorted_handler_id: int | None = None

    def __init__(self, db_manager: DatabaseManager, element: Entry | Group):
        """GObject to handle a safe element. The underlying pykeepass element
        can be obtainied via the `element` property, when it is certain the
        element is a Group or Entry, the properties `entry` and `group` should
        be used instead."""
        super().__init__()

        self._element = element
        self._db_manager = db_manager

        self.is_group = isinstance(self, SafeGroup)
        self.is_entry = isinstance(self, SafeEntry)

        self._notes: str = element.notes or ""
        if self.is_group:
            self._name = element.name or ""
        else:
            self._name = element.title or ""

    def __eq__(self, other):  # pylint: disable=arguments-differ
        if isinstance(other, SafeElement):
            return self.uuid == other.uuid

        return False

    @GObject.Signal()
    def updated(self):
        """Signal used to tell whenever there have been any changed that should
        be reflected on the main list box or edit page."""
        self._db_manager.is_dirty = True
        self.touch(modify=True)
        logging.debug("Safe element updated")

    def touch(self, modify: bool = False) -> None:
        """Updates the last accessed time. If modify is true
        it also updates the last modified time."""
        self._element.touch(modify)

    @property
    def element(self) -> Entry | Group:
        return self._element

    @GObject.Property(type=str, default="")
    def name(self) -> str:
        """Get element title or name

        :returns: name or an empty string if there is none
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
            if self.is_group:
                self._element.name = new_name
            else:
                self._element.title = new_name

            self.updated()

    @GObject.Property(type=str, default="")
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
            self._element.notes = new_notes
            self.updated()

    @property
    def parentgroup(self) -> SafeGroup:
        """Parent Group of the element

        :returns: parent group
        :rtype: SafeGroup
        """
        if self.is_root_group:
            return self

        return SafeGroup(self._db_manager, self._element.parentgroup)

    @property
    def is_root_group(self) -> bool:
        if self.is_entry:
            return False

        return self._element.is_root_group

    @property
    def uuid(self) -> UUID:
        """UUID of the element

        :returns: uuid of the element
        :rtype: UUID
        """
        return self._element.uuid

    @property
    def path(self) -> list[str]:
        return self._element.path

    @property
    def atime(self) -> GLib.DateTime:
        """The UTC accessed time of the element."""
        time = self._element.atime
        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime

    @property
    def ctime(self) -> GLib.DateTime:
        """The UTC creation time of the element."""
        time = self._element.ctime
        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime

    @property
    def mtime(self) -> GLib.DateTime:
        """The UTC modified time of the element."""
        time = self._element.mtime
        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime


class SafeGroup(SafeElement):
    def __init__(self, db_manager: DatabaseManager, group: Group) -> None:
        """GObject to handle a safe group.

        :param DatabaseManager db_manager:  database of the group
        :param Group group: group to handle
        """
        super().__init__(db_manager, group)

        self._group: Group = group

    @staticmethod
    def get_root(db_manager: DatabaseManager) -> SafeGroup:
        """Method to obtain the root group."""
        # pylint: disable=no-member
        return SafeGroup(db_manager, db_manager.db.root_group)

    @property
    def subgroups(self) -> list[SafeGroup]:
        return [SafeGroup(self._db_manager, group) for group in self._group.subgroups]

    @property
    def entries(self) -> list[SafeEntry]:
        return [SafeEntry(self._db_manager, entry) for entry in self._group.entries]

    @property
    def group(self) -> Group:
        """Returns the private pykeepass group."""
        return self._group


class SafeEntry(SafeElement):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    _color_key = "color_prop_LcljUMJZ9X"
    _note_key = "Notes"
    _otp: OTP | None = None
    _otp_key = "otp"

    def __init__(self, db_manager: DatabaseManager, entry: Entry) -> None:
        """GObject to handle a safe entry.

        :param DatabaseManager db_manager:  database of the entry
        :param Entry entry: entry to handle
        """
        super().__init__(db_manager, entry)

        self._entry: Entry = entry

        self._attachments: list[Attachment] = entry.attachments or []

        self._attributes: dict[str, str] = {
            key: value
            for key, value in entry.custom_properties.items()
            if key not in (self._color_key, self._note_key, self._otp_key)
        }

        color_value: str = entry.get_custom_property(self._color_key)
        self._color: str = color_value or Color.NONE.value

        self._icon_nr: str = entry.icon or ""
        self._password: str = entry.password or ""
        self._url: str = entry.url or ""
        self._username: str = entry.username or ""

        otp_uri = entry.get_custom_property("otp")
        if otp_uri:
            self._otp = parse_uri(otp_uri)

        # Check if the entry has expired every 10 minutes.
        GLib.timeout_add_seconds(600, self._is_expired)

    @property
    def entry(self) -> Entry:
        """Get entry

        :returns: entry
        :rtype: Entry
        """
        return self._entry

    def _is_expired(self) -> bool:
        self.props.expired = self.element.expired
        return GLib.SOURCE_CONTINUE

    @GObject.Property(type=object, flags=GObject.ParamFlags.READABLE)
    def attachments(self) -> list[Attachment]:
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
        self.updated()

        return attachment

    def delete_attachment(self, attachment: Attachment) -> None:
        """Remove an attachment from the entry

        :param Attachmennt attachment: attachment to delete
        """
        self._db_manager.db.delete_binary(attachment.id)
        self._attachments.remove(attachment)
        self.updated()

    def get_attachment(self, id_: str) -> Attachment | None:
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

    @GObject.Property(type=object, flags=GObject.ParamFlags.READABLE)
    def attributes(self) -> dict[str, str]:
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
        self.updated()

    def delete_attribute(self, key: str) -> None:
        """Delete an attribute

        :param key: attribute key to delete
        """
        if not self.has_attribute(key):
            return

        self._entry.delete_custom_property(key)
        self._attributes.pop(key)
        self.updated()

    @GObject.Property(type=str, default=Color.NONE.value)
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
            self.updated()

    @GObject.Property(type=object)
    def icon(self) -> Icon:
        """Get icon number

        :returns: icon number or "0" if no icon
        :rtype: str
        """
        try:
            return ICONS[self._icon_nr]
        except KeyError:
            return ICONS["0"]

    @icon.setter  # type: ignore
    def icon(self, new_icon_nr: str) -> None:
        """Set icon number

        :param str new_icon_nr: new icon number
        """
        if new_icon_nr != self._icon_nr:
            self._icon_nr = new_icon_nr
            self._entry.icon = new_icon_nr
            self.notify("icon-name")
            self.updated()

    @GObject.Property(type=str, default="", flags=GObject.ParamFlags.READABLE)
    def icon_name(self) -> str:
        """Get the icon name

        :returns: icon name or the default icon if undefined
        :rtype: str
        """
        return self.props.icon.name

    @GObject.Property(type=str, default="")
    def otp(self) -> str:
        if self._otp:
            return self._otp.secret

        return ""

    @otp.setter  # type: ignore
    def otp(self, otp: str) -> None:
        updated = False

        # Some sites give the secret in chunks split by spaces for easy reading
        # lets strip those as they'll produce an invalid secret.
        otp = otp.replace(" ", "")

        if not otp and self._otp:
            # Delete existing
            self._otp = None
            self._element.delete_custom_property("otp")
            self.updated()
        elif self._otp and self._otp.secret != otp:
            # Changing an existing OTP
            self._otp.secret = otp
            updated = True
        elif otp:
            # Creating brand new OTP.
            self._otp = TOTP(otp, issuer=self.name)
            updated = True

        if updated:
            self._element.set_custom_property("otp", self._otp.provisioning_uri())
            self.updated()

    def otp_interval(self) -> int:
        if isinstance(self._otp, TOTP):
            return self._otp.interval

        return 30

    def otp_lifespan(self) -> float | None:
        """Returns seconds until token expires."""
        if isinstance(self._otp, TOTP):
            gnow = GLib.DateTime.new_now_utc()
            now_seconds = gnow.to_unix()
            now_milis = gnow.get_seconds() % 1
            now = now_seconds + now_milis
            return self._otp.interval - now % self._otp.interval

        return None

    def otp_token(self):  # pylint: disable=inconsistent-return-statements
        if self._otp:
            try:  # pylint: disable=inconsistent-return-statements
                return self._otp.now()
            except binascii.Error:
                logging.debug(
                    "Error cought in OTP token generation (likely invalid "
                    "base32 secret)."
                )

    @GObject.Property(type=str, default="")
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
            self.updated()

    @GObject.Property(type=str, default="")
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
            self.updated()

    @GObject.Property(type=str, default="")
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
            self.updated()

    @GObject.Property(type=bool, default=False)
    def expires(self) -> bool:
        return self.entry.expires

    @expires.setter  # type: ignore
    def expires(self, value: bool) -> None:
        if value != self.entry.expires:
            self.entry.expires = value
            self.props.expired = self.entry.expired
            self.updated()

    @GObject.Property(type=bool, default=False)
    def expired(self):
        return self.entry.expired

    @property
    def expiry_time(self) -> GLib.DateTime:
        """Returns the expiration time in the UTC timezone."""
        time = self.entry.expiry_time
        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime

    @expiry_time.setter  # type: ignore
    def expiry_time(self, value: GLib.DateTime) -> None:
        """Sets the expiration time in the UTC timezone."""
        if value != self.entry.expiry_time:
            expired = datetime(
                value.get_year(),
                value.get_month(),
                value.get_day_of_month(),
                value.get_hour(),
                value.get_minute(),
                value.get_second(),
                tzinfo=timezone.utc,
            )
            self.entry.expiry_time = expired
            self.props.expired = self.entry.expired
            self.updated()


class Icon(NamedTuple):
    # pylint: disable=inherit-non-class
    # This is a false positive because pylint does not properly handle
    # Python 3.9 at the moment. It can be safely removed once pylint
    # handles it.
    name: str
    visible: bool = False


# https://github.com/dlech/KeePass2.x/blob/4facf2f1ebc76eeddbe11975eccb0dc2b49dfc37/KeePassLib/PwEnums.cs#L81  # noqa: E501  # pylint: disable=line-too-long
# https://hsto.org/files/b1e/d20/e38/b1ed20e385d642cc870355fdef153fb9.png
# FIXME: Based on the names from the links above, some of the current
# icons should be replaced.
ICONS = {
    "0": Icon("dialog-password-symbolic", True),
    "1": Icon("network-wired-symbolic", True),
    "2": Icon("dialog-warning-symbolic"),
    "3": Icon("network-server-symbolic"),
    "4": Icon("document-edit-symbolic"),
    "5": Icon("media-view-subtitles-symbolic"),
    "6": Icon("application-x-addon-symbolic"),
    "7": Icon("accessories-text-editor-symbolic"),
    "8": Icon("network-wired-symbolic"),
    "9": Icon("mail-send-symbolic", True),
    "10": Icon("text-x-generic-symbolic"),
    "11": Icon("camera-photo-symbolic"),
    "12": Icon("network-wireless-signal-excellent-symbolic", True),
    "13": Icon("dialog-password-symbolic"),
    "14": Icon("colorimeter-colorhug-symbolic"),
    "15": Icon("scanner-symbolic"),
    "16": Icon("user-available-symbolic", True),
    "17": Icon("media-optical-cd-audio-symbolic"),
    "18": Icon("video-display-symbolic"),
    "19": Icon("mail-unread-symbolic", True),
    "20": Icon("emblem-system-symbolic"),
    "21": Icon("edit-paste-symbolic"),
    "22": Icon("edit-paste-symbolic"),
    "23": Icon("preferences-desktop-remote-desktop-symbolic", True),
    "24": Icon("uninterruptible-power-supply-symbolic"),
    "25": Icon("mail-unread-symbolic"),
    "26": Icon("media-floppy-symbolic"),
    "27": Icon("drive-harddisk-symbolic", True),
    "28": Icon("dialog-password-symbolic"),
    "29": Icon("airplane-mode-symbolic", True),
    "30": Icon("utilities-terminal-symbolic", True),
    "31": Icon("printer-symbolic"),
    "32": Icon("image-x-generic-symbolic"),
    "33": Icon("edit-select-all-symbolic"),
    "34": Icon("preferences-system-symbolic", True),
    "35": Icon("network-workgroup-symbolic"),
    "36": Icon("dialog-password-symbolic"),
    "37": Icon("auth-fingerprint-symbolic", True),
    "38": Icon("drive-harddisk-symbolic"),
    "39": Icon("document-open-recent-symbolic"),
    "40": Icon("system-search-symbolic"),
    "41": Icon("applications-games-symbolic", True),
    "42": Icon("media-flash-symbolic"),
    "43": Icon("user-trash-symbolic"),
    "44": Icon("accessories-text-editor-symbolic"),
    "45": Icon("edit-delete-symbolic"),
    "46": Icon("dialog-question-symbolic"),
    "47": Icon("package-x-generic-symbolic"),
    "48": Icon("folder-symbolic", True),
    "49": Icon("folder-open-symbolic"),
    "50": Icon("document-open-symbolic"),
    "51": Icon("system-lock-screen-symbolic", True),
    "52": Icon("rotation-locked-symbolic"),
    "53": Icon("object-select-symbolic"),
    "54": Icon("document-edit-symbolic"),
    "55": Icon("image-x-generic-symbolic"),
    "56": Icon("accessories-dictionary-symbolic", True),
    "57": Icon("view-list-symbolic"),
    "58": Icon("avatar-default-symbolic", True),
    "59": Icon("applications-engineering-symbolic"),
    "60": Icon("go-home-symbolic"),
    "61": Icon("starred-symbolic", True),
    "62": Icon("start-here-symbolic"),
    "63": Icon("dialog-password-symbolic"),
    "64": Icon("start-here-symbolic"),
    "65": Icon("accessories-dictionary-symbolic"),
    "66": Icon("currency-symbolic", True),
    "67": Icon("application-certificate-symbolic"),
    "68": Icon("phone-apple-iphone-symbolic", True),
}
