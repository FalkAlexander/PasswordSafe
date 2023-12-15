# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=too-many-lines
from __future__ import annotations

import binascii
import logging
import typing

from gettext import gettext as _
from datetime import datetime, timezone
from enum import Enum
from typing import NamedTuple
from uuid import UUID

from gi.repository import GLib, GObject, Gio, Gtk
from pyotp import OTP, TOTP, parse_uri

from gsecrets.attributes_model import AttributesModel

if typing.TYPE_CHECKING:
    from pykeepass.attachment import Attachment
    from pykeepass.entry import Entry
    from pykeepass.group import Group

    from gsecrets.database_manager import DatabaseManager  # pylint: disable=ungrouped-imports # noqa: E501


class EntryColor(Enum):
    NONE = "NoneColorButton"
    BLUE = "BlueColorButton"
    GREEN = "GreenColorButton"
    YELLOW = "YellowColorButton"
    ORANGE = "OrangeColorButton"
    RED = "RedColorButton"
    PURPLE = "PurpleColorButton"
    BROWN = "BrownColorButton"

    def to_translatable(self):  # pylint: disable=too-many-return-statements
        match self:
            case EntryColor.NONE:
                return _("White")
            case EntryColor.BLUE:
                return _("Blue")
            case EntryColor.GREEN:
                return _("Green")
            case EntryColor.YELLOW:
                return _("Yellow")
            case EntryColor.ORANGE:
                return _("Orange")
            case EntryColor.RED:
                return _("Red")
            case EntryColor.PURPLE:
                return _("Purple")
            case EntryColor.BROWN:
                return _("Brown")


class SafeElement(GObject.Object):
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

    @GObject.Signal(flags=GObject.SignalFlags.ACTION)
    def updated(self):
        """Signal used to tell whenever there have been any changed that should
        be reflected on the main list box or edit page."""
        self._db_manager.is_dirty = True
        self.touch(modify=True)
        self.emit(self.updated)
        logging.debug("Safe element updated")

    def touch(self, modify: bool = False) -> None:
        """Updates the last accessed time. If modify is true
        it also updates the last modified time."""
        self._element.touch(modify)

    def delete(self) -> None:
        """Delete an Element from the database."""
        element = self._element
        parentgroup = self.parentgroup

        self.delete_inner()

        if self.is_entry:
            self._db_manager.db.delete_entry(element)
        else:
            self._db_manager.db.delete_group(element)

        parentgroup.updated()

    def delete_inner(self) -> None:
        """Recursively removes items from our wrapper of the database."""
        if self.is_entry:
            found, pos = self._db_manager.entries.find(self)
            if found:
                self._db_manager.entries.remove(pos)
        else:
            while entry := self.entries.get_item(0):  # pylint: disable=no-member
                entry.delete_inner()

            while group := self.subgroups.get_item(0):  # pylint: disable=no-member
                group.delete_inner()

            found, pos = self._db_manager.groups.find(self)
            if found:
                self._db_manager.groups.remove(pos)

    def trash(self) -> bool:
        """Thrash an Element from the database.

        Returns if the element was deleted instead of being sent to the trash
        bin.
        """
        element = self._element
        parentgroup = self.parentgroup

        if trash_bin := self._db_manager.trash_bin:
            if (
                self._db_manager.parent_checker(self, trash_bin)
                and not self.is_trash_bin
            ):
                self.delete()
                return True

        if self.is_trash_bin:
            self.delete()
            self._db_manager.trash_bin = None
            return True

        trash_bin_missing = self._db_manager.trash_bin is None

        if self.is_entry:
            self._db_manager.db.trash_entry(element)
            parentgroup.filter_changed(True)
        else:
            self._db_manager.db.trash_group(element)
            parentgroup.filter_changed(False)

        # We add the trash bin if it was not present already
        if trash_bin_missing:
            if trash_bin_inner := self._db_manager.db.recyclebin_group:
                trash_bin = SafeGroup(self._db_manager, trash_bin_inner)
                self._db_manager.trash_bin = trash_bin
                self._db_manager.groups.append(trash_bin)
                trash_bin.parentgroup.updated()

        if trash_bin := self._db_manager.trash_bin:
            trash_bin.filter_changed(self.is_entry)

        parentgroup.updated()

        return False

    def move_to(self, dest: SafeGroup) -> None:
        old_location = self.parentgroup

        if old_location == dest:
            return

        # We signal items changed on the main list store so that the changes are
        # propagated to the filter models used by each group.
        if self.is_entry:
            self._db_manager.db.move_entry(self._element, dest.group)
            dest.filter_changed(True)
            old_location.filter_changed(True)
        else:
            self._db_manager.db.move_group(self._element, dest.group)
            dest.filter_changed(False)
            old_location.filter_changed(False)

        old_location.updated()
        dest.updated()

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
                self._db_manager.emit("sorting_changed", False)
            else:
                self._element.title = new_name
                self._db_manager.emit("sorting_changed", True)

            if self.is_entry:
                found, pos = self._db_manager.entries.find(self)
                if found:
                    self._db_manager.entries.items_changed(pos, 1, 1)
            else:
                found, pos = self._db_manager.groups.find(self)
                if found:
                    self._db_manager.groups.items_changed(pos, 1, 1)

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

        for group in self._db_manager.groups:
            if group.uuid == self._element.parentgroup.uuid:
                return group

        logging.error("This should be unreachable: parentgroup")
        return SafeGroup(self._db_manager, self._element.parentgroup)

    @property
    def parentgroup_uuid(self) -> UUID:
        """UUID of the parent Group of the element

        This method should be preferred than parentgroup since it does not go
        through the entire list of elements.

        :returns: parent group
        :rtype: SafeGroup
        """
        if self.is_root_group:
            return self.uuid

        return self._element.parentgroup.uuid

    @property
    def is_root_group(self) -> bool:
        if self.is_entry:
            return False

        return self._element.is_root_group

    @property
    def is_trash_bin(self) -> bool:
        if trash_bin_inner := self._db_manager.db.recyclebin_group:
            return self.uuid == trash_bin_inner.uuid

        return False

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
    def atime(self) -> GLib.DateTime | None:
        """The UTC accessed time of the element."""
        try:
            time = self._element.atime
        except OverflowError:
            logging.error("Accessed time for %s is invalid", self.name)
            return None

        if not time:
            return None

        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime

    @property
    def ctime(self) -> GLib.DateTime | None:
        """The UTC creation time of the element."""
        try:
            time = self._element.ctime
        except OverflowError:
            logging.error("Creation time for %s is invalid", self.name)
            return None

        if not time:
            return None

        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime

    @property
    def mtime(self) -> GLib.DateTime | None:
        """The UTC modified time of the element."""
        try:
            time = self._element.mtime
        except OverflowError:
            logging.error("Modified time for %s is invalid", self.name)
            return None

        if not time:
            return None

        gtime = GLib.DateTime.new_utc(
            time.year, time.month, time.day, time.hour, time.minute, time.second
        )
        return gtime


class SafeGroup(SafeElement):
    _entries = None
    _entries_filter = None
    _subgroups = None
    _subgroups_filter = None

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
        if root := db_manager.root:
            return root

        for group in db_manager.groups:
            if group.is_root_group:
                return group

        logging.error("This should be unreachable: get_root")
        return SafeGroup(db_manager, db_manager.db.root_group)

    def new_entry(
        self, title: str = "", username: str = "", password: str = ""
    ) -> SafeEntry:
        """Adds new entry to self."""
        group = self.group
        force: bool = self._db_manager.check_entry_in_group_exists("", group)

        new_entry = self._db_manager.db.add_entry(
            group,
            title,
            username,
            password,
            url=None,
            notes=None,
            expiry_time=None,
            tags=None,
            icon="0",
            force_creation=force,
        )
        safe_entry = SafeEntry(self._db_manager, new_entry)
        self.updated()
        self._db_manager.entries.append(safe_entry)

        return safe_entry

    def new_subgroup(
        self, name: str = "", icon: str | None = None, notes: str = ""
    ) -> SafeGroup:
        """Adds new subgroup to self."""
        new_group = self._db_manager.db.add_group(
            self.group, name, icon=icon, notes=notes
        )
        safe_group = SafeGroup(self._db_manager, new_group)
        self.updated()
        self._db_manager.groups.append(safe_group)

        return safe_group

    def filter_changed(self, is_entry: bool) -> None:
        if is_entry:
            if self._entries_filter is None:
                self.init_entries()

            self._entries_filter.changed(Gtk.FilterChange.DIFFERENT)  # type: ignore
        else:
            if self._subgroups_filter is None:
                self.init_subgroups()

            self._subgroups_filter.changed(Gtk.FilterChange.DIFFERENT)  # type: ignore

    def init_subgroups(self):
        self._subgroups_filter = Gtk.CustomFilter.new(self._group_filter_func)
        self._subgroups = Gtk.FilterListModel.new(
            self._db_manager.groups, self._subgroups_filter
        )

        # We need to find the trash bin.
        if self.is_root_group:
            self._db_manager.root = self

            if not self._db_manager.trash_bin:
                for group in self._db_manager.groups:
                    if group.is_trash_bin:
                        self._db_manager.trash_bin = group

    def init_entries(self):
        self._entries_filter = Gtk.CustomFilter.new(self._group_filter_func)
        self._entries = Gtk.FilterListModel.new(
            self._db_manager.entries, self._entries_filter
        )

    @property
    def subgroups(self) -> Gio.ListModel:
        if self._subgroups is None:
            self.init_subgroups()

        return self._subgroups

    @property
    def entries(self) -> Gio.ListModel:
        if self._entries is None:
            self.init_entries()

        return self._entries

    @property
    def group(self) -> Group:
        """Returns the private pykeepass group."""
        return self._group

    def _entry_filter_func(self, entry: SafeEntry) -> bool:
        return entry.parentgroup_uuid == self.uuid

    def _group_filter_func(self, group: SafeGroup) -> bool:
        if group.is_root_group:
            return False

        return group.parentgroup_uuid == self.uuid


class SafeEntry(SafeElement):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    _color_key = "color_prop_LcljUMJZ9X"
    _expired_id: int | None = None
    _note_key = "Notes"
    _otp: TOTP | None = None
    _otp_key = "otp"

    history_saved = GObject.Signal()

    def __init__(self, db_manager: DatabaseManager, entry: Entry) -> None:
        """GObject to handle a safe entry.

        :param DatabaseManager db_manager:  database of the entry
        :param Entry entry: entry to handle
        """
        super().__init__(db_manager, entry)

        self._entry: Entry = entry

        self._attachments: list[Attachment] = entry.attachments or []

        # NOTE Can fail at libpykeepass, see
        # https://github.com/libkeepass/pykeepass/issues/254
        # TODO Read as many attributes as possible until we see an error.
        try:
            attributes = {
                key: value
                for key, value in entry.custom_properties.items()
                if key not in (self._color_key, self._note_key, self._otp_key)
            }
        except Exception as err:  # pylint: disable=broad-except
            logging.error("Could not read attributes: %s", err)
            attributes = {}

        self._attributes = AttributesModel(attributes)

        color_value: str = entry.get_custom_property(self._color_key)
        self._color: str = color_value or EntryColor.NONE.value

        self._icon_nr: str = entry.icon or ""
        self._password: str = entry.password or ""
        self._url: str = entry.url or ""
        self._username: str = entry.username or ""

        if otp_uri := entry.otp:
            try:
                if otp_uri.startswith("otpauth://"):
                    self._otp = parse_uri(otp_uri)
                else:
                    self._otp = TOTP(otp_uri)
            except ValueError as err:
                logging.debug(err)

        self._check_expiration()

    @property
    def entry(self) -> Entry:
        """Get entry

        :returns: entry
        :rtype: Entry
        """
        return self._entry

    def duplicate(self):
        """Duplicate an entry"""
        title: str = self.name or ""
        username: str = self.username or ""
        password: str = self.password or ""

        # NOTE: With clone is meant a duplicated object, not the process
        # of cloning/duplication; "the" clone
        entry = self.entry
        clone_entry: Entry = self._db_manager.db.add_entry(
            entry.parentgroup,
            title + " - " + _("Clone"),
            username,
            password,
            url=entry.url,
            notes=entry.notes,
            expiry_time=entry.expiry_time,
            tags=entry.tags,
            icon=entry.icon,
            force_creation=True,
        )
        clone_entry.expires = entry.expires

        # Add custom properties
        for key in entry.custom_properties:
            value: str = entry.custom_properties[key] or ""
            clone_entry.set_custom_property(key, value)

        safe_entry = SafeEntry(self._db_manager, clone_entry)

        self.parentgroup.updated()
        self._db_manager.entries.append(safe_entry)

    def _check_expiration(self) -> None:
        """Check expiration

        If the entry is expired, this ensures that a notification is sent.
        If the entry is not expired yet, a timeout is set to regularly
        check if the entry is expired.
        """
        if self._expired_id:
            GLib.source_remove(self._expired_id)
            self._expired_id = None

        if not self.props.expires:
            return

        if self.props.expired:
            self.notify("expired")
        else:
            self._expired_id = GLib.timeout_add_seconds(600, self._is_expired)

    def _is_expired(self) -> bool:
        if self.props.expired:
            self._expired_id = None
            self.notify("expired")
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def save_history(self) -> None:
        """Save current version of the entry in its history."""
        # NOTE Attachments are references, so duplicating them is ok.
        self._entry.save_history()
        self.updated()
        self.emit(self.history_saved)

    def delete_history(self, entry: SafeEntry) -> None:
        """Delete entry from the history of self."""
        self._entry.delete_history(entry.entry)
        self.updated()
        self.emit(self.history_saved)

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
        self.notify("attachments")

        return attachment

    def delete_attachment(self, attachment: Attachment) -> None:
        """Remove an attachment from the entry

        :param Attachmennt attachment: attachment to delete
        """
        self._db_manager.db.delete_binary(attachment.id)
        self._attachments.remove(attachment)
        self.notify("attachments")
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
    def attributes(self) -> AttributesModel:
        return self._attributes

    def has_attribute(self, key: str) -> bool:
        """Check if an attribute exists.

        :param str key: attribute key to check
        """
        return self._attributes.has_attribute(key)

    def set_attribute(self, key: str, value: str, protected: bool = False) -> None:
        """Add or replace an entry attribute

        :param str key: attribute key
        :param str value: attribute value
        """
        if self.props.attributes.get(key) == value:
            return

        self._entry.set_custom_property(key, value, protect=protected)
        self._attributes.insert(key, value)
        self.updated()
        self.notify("attributes")

    def delete_attribute(self, key: str) -> None:
        """Delete an attribute

        :param key: attribute key to delete
        """
        if not self.has_attribute(key):
            return

        self._entry.delete_custom_property(key)
        self._attributes.pop(key)
        self.updated()
        self.notify("attributes")

    def is_attribute_protected(self, key: str) -> bool:
        """Returns whether the attribute with a specific key is protected

        If there is no such key returns False."""
        return self.entry.is_custom_property_protected(key)

    @GObject.Property(type=str, default=EntryColor.NONE.value)
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

    @property
    def history(self) -> list[SafeEntry]:
        history = self._entry.history
        return [SafeEntry(self._db_manager, entry) for entry in history]

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
            # NOTE the opt property doesn't accept None.
            self._element.otp = ""
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
            self._element.otp = self._otp.provisioning_uri()
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

    def otp_token(self) -> str | None:
        if self._otp:
            try:
                return self._otp.now()
            except binascii.Error:
                logging.debug(
                    "Error caught in OTP token generation (likely invalid "
                    "base32 secret)."
                )

        return None

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
            self._check_expiration()
            self.updated()

    @GObject.Property(
        type=bool,
        default=False,
        flags=GObject.ParamFlags.READABLE | GObject.ParamFlags.EXPLICIT_NOTIFY,
    )
    def expired(self):
        return self.entry.expired

    @property
    def expiry_time(self) -> GLib.DateTime | None:
        """Returns the expiration time in the UTC timezone.

        Returns None when there isn't an expiration date.
        """
        try:
            time = self.entry.expiry_time
        except Exception as err:  # pylint: disable=broad-except
            logging.error(
                "Could not read expiry date from %s: %s", self.name, err
            )
            return None

        if not time:
            return None

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
            self._check_expiration()

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
    "7": Icon("notepad-symbolic"),
    "8": Icon("network-wired-symbolic"),
    "9": Icon("send-symbolic", True),
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
    "23": Icon("display-with-window-symbolic", True),
    "24": Icon("uninterruptible-power-supply-symbolic"),
    "25": Icon("mail-unread-symbolic"),
    "26": Icon("media-floppy-symbolic"),
    "27": Icon("drive-harddisk-symbolic", True),
    "28": Icon("dialog-password-symbolic"),
    "29": Icon("airplane-mode-symbolic", True),
    "30": Icon("terminal-symbolic", True),
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
    "44": Icon("notepad-symbolic"),
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
    "56": Icon("open-book-symbolic", True),
    "57": Icon("view-list-symbolic"),
    "58": Icon("avatar-default-symbolic", True),
    "59": Icon("applications-engineering-symbolic"),
    "60": Icon("go-home-symbolic"),
    "61": Icon("starred-symbolic", True),
    "62": Icon("start-here-symbolic"),
    "63": Icon("dialog-password-symbolic"),
    "64": Icon("start-here-symbolic"),
    "65": Icon("open-book-symbolic"),
    "66": Icon("money-symbolic", True),
    "67": Icon("application-certificate-symbolic"),
    "68": Icon("phone-apple-iphone-symbolic", True),
}
