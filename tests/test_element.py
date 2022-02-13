# SPDX-License-Identifier: GPL-3.0-only
import os

from pykeepass.exceptions import CredentialsError
import pytest


from gsecrets.database_manager import DatabaseManager
from gsecrets.safe_element import EntryColor, SafeGroup, SafeEntry, ICONS


@pytest.fixture(scope="module")
def password():
    return "dYIhZjdqNiVcGLDr"


@pytest.fixture(scope="module")
def path():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(*[current_dir, "data", "Test2Groups.kdbx"])
    return path


@pytest.fixture(scope="module")
def db_pwd(path, password):
    with pytest.raises(CredentialsError):
        db = DatabaseManager(path, "wrong password")

    db = DatabaseManager(path, password)
    assert db is not None
    assert db.password == password
    assert db.keyfile is None
    assert db.locked is False
    assert db.is_dirty is False

    return db


def test_add_group(db_pwd):
    nr_groups = len(db_pwd.db.groups)

    group_name = "a new group"
    safe_group = db_pwd.add_group_to_database(
        group_name, None, None, db_pwd.db.root_group)
    assert len(db_pwd.db.groups) == nr_groups + 1
    assert db_pwd.is_dirty is True
    assert isinstance(safe_group, SafeGroup)

    assert safe_group.is_group is True
    assert safe_group.is_entry is False
    assert safe_group.props.notes == ""
    assert safe_group.props.name == group_name
    assert safe_group.path == [group_name]

    new_group_name = "group renamed"
    safe_group.props.name = new_group_name
    assert safe_group.props.name == new_group_name
    assert safe_group.path == [new_group_name]

    new_parent = db_pwd.db.groups[1]
    assert safe_group.parentgroup.element != new_parent
    safe_group.move_to(SafeGroup(db_pwd, new_parent))
    assert safe_group.parentgroup.element == new_parent
    assert safe_group.path == [new_parent.name, new_group_name]


def test_delete_group(db_pwd):
    nr_groups = len(db_pwd.db.groups)
    assert nr_groups > 0

    db_pwd.delete_from_database(db_pwd.db.groups[-1])
    assert len(db_pwd.db.groups) == nr_groups - 1

    tmp_group = db_pwd.add_group_to_database(
        "tmp", None, None, db_pwd.db.root_group)
    assert len(db_pwd.db.groups) == nr_groups

    db_pwd.delete_from_database(tmp_group.element)
    assert len(db_pwd.db.groups) == nr_groups - 1


def test_add_entry(db_pwd):
    root_group = db_pwd.db.groups[0]
    nr_entries = len(root_group.entries)

    entry_name = "a new group"
    username = "username"
    password = "password"
    safe_entry = db_pwd.add_entry_to_database(
        root_group, entry_name, username, password)
    assert len(root_group.entries) == nr_entries + 1
    assert isinstance(safe_entry, SafeEntry)

    assert safe_entry.is_group is False
    assert safe_entry.is_entry is True
    assert safe_entry.props.notes == ""
    assert safe_entry.props.username == username
    assert safe_entry.props.password == password
    assert safe_entry.props.name == entry_name
    assert safe_entry.path == [entry_name]

    new_entry_name = "entry renamed"
    safe_entry.props.name = new_entry_name
    assert safe_entry.props.name == new_entry_name
    assert safe_entry.path == [new_entry_name]

    assert safe_entry.props.icon == ICONS["0"]
    new_icon_nr = "42"
    safe_entry.props.icon = new_icon_nr
    assert safe_entry.props.icon == ICONS[new_icon_nr]
    assert safe_entry.props.icon_name == ICONS[new_icon_nr].name

    assert safe_entry.props.color == EntryColor.NONE.value
    safe_entry.props.color = EntryColor.BLUE.value
    assert safe_entry.props.color == EntryColor.BLUE.value

    db_pwd.duplicate_entry(safe_entry.element)
    assert len(root_group.entries) == nr_entries + 2

    new_parent = db_pwd.db.groups[1]
    assert safe_entry.parentgroup.element != new_parent
    safe_entry.move_to(SafeGroup(db_pwd, new_parent))
    assert safe_entry.parentgroup.element == new_parent
    assert safe_entry.path == [new_parent.name, new_entry_name]


def test_delete_entry(db_pwd):
    root_group = db_pwd.db.groups[0]
    nr_entries = len(root_group.entries)
    assert nr_entries > 0

    db_pwd.delete_from_database(root_group.entries[0])
    assert len(root_group.entries) == nr_entries - 1

    tmp_entry = db_pwd.add_entry_to_database(root_group, "tmp")
    assert len(root_group.entries) == nr_entries

    db_pwd.delete_from_database(tmp_entry.element)
    assert len(root_group.entries) == nr_entries - 1
