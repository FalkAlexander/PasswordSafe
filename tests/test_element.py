# SPDX-License-Identifier: GPL-3.0-only
import os

import pytest
from pykeepass import PyKeePass


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
    db = DatabaseManager(path)

    # Hack around async methods
    # TODO Provide a sync method which tests unlock_async
    with pytest.raises(Exception):
        py_db = PyKeePass(path, "wrong password")

    py_db = PyKeePass(path, password)
    db.db = py_db
    db.password == password

    assert db.locked is False
    assert db.is_dirty is False

    return db


def test_add_group(db_pwd):
    group_name = "a new group"
    root_group = SafeGroup.get_root(db_pwd)
    nr_groups = len(root_group.subgroups)

    safe_group = root_group.new_subgroup(group_name, None, "")
    assert len(root_group.subgroups) == nr_groups + 1
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

    new_parent = root_group.subgroups[0]
    assert safe_group.parentgroup != new_parent
    safe_group.move_to(new_parent)
    assert safe_group.parentgroup == new_parent
    assert safe_group.path == [new_parent.name, new_group_name]


def test_delete_group(db_pwd):
    root_group = SafeGroup.get_root(db_pwd)

    nr_groups = len(root_group.subgroups)
    assert nr_groups > 0

    safe_group = root_group.subgroups[-1]
    safe_group.delete()
    assert len(root_group.subgroups) == nr_groups - 1

    tmp_group = root_group.new_subgroup("tmp", None, "")
    assert len(root_group.subgroups) == nr_groups

    tmp_group.delete()
    assert len(root_group.subgroups) == nr_groups - 1


def test_add_entry(db_pwd):
    root_group = SafeGroup.get_root(db_pwd)
    nr_entries = len(root_group.entries)

    entry_name = "a new group"
    username = "username"
    password = "password"
    safe_entry = root_group.new_entry(entry_name, username, password)
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

    safe_entry.duplicate()
    assert len(root_group.entries) == nr_entries + 2

    new_parent = root_group.subgroups[0]
    assert safe_entry.parentgroup != new_parent
    safe_entry.move_to(new_parent)
    assert safe_entry.parentgroup == new_parent
    assert safe_entry.path == [new_parent.name, new_entry_name]


def test_delete_entry(db_pwd):
    root_group = SafeGroup.get_root(db_pwd)
    nr_entries = len(root_group.entries)
    assert nr_entries > 0

    first_entry = root_group.entries[0]
    first_entry.delete()
    assert len(root_group.entries) == nr_entries - 1

    tmp_entry = root_group.new_entry("tmp")
    assert len(root_group.entries) == nr_entries

    tmp_entry.delete()
    assert len(root_group.entries) == nr_entries - 1
