# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing
from enum import IntEnum
from gettext import gettext as _
from gettext import ngettext

from gi.repository import Adw, Gio, GLib, GObject, Gtk

import gsecrets.config_manager
from gsecrets import const
from gsecrets.entry_page import EntryPage
from gsecrets.entry_row import EntryRow
from gsecrets.group_page import GroupPage
from gsecrets.group_row import GroupRow
from gsecrets.pathbar import Pathbar
from gsecrets.safe_element import SafeElement, SafeEntry, SafeGroup
from gsecrets.unlocked_headerbar import UnlockedHeaderBar
from gsecrets.widgets.database_settings_dialog import DatabaseSettingsDialog
from gsecrets.widgets.properties_dialog import PropertiesDialog
from gsecrets.widgets.references_dialog import ReferencesDialog
from gsecrets.widgets.saving_conflict_dialog import SavingConflictDialog
from gsecrets.widgets.search import Search
from gsecrets.widgets.selection_mode_headerbar import SelectionModeHeaderbar
from gsecrets.widgets.unlocked_database_page import UnlockedDatabasePage

if typing.TYPE_CHECKING:
    from gsecrets.database_manager import DatabaseManager
    from gsecrets.widgets.window import Window


class UndoData:
    def __init__(self, elements, toast):
        self.elements = elements
        self.toast = toast


class AttributeUndoData:
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        toast: Adw.Toast,
        entry: SafeEntry,
        key: str,
        value: str,
        protected: bool = False,
    ):
        self.toast = toast
        self.key = key
        self.value = value
        self.entry = entry
        self.protected = protected


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/unlocked_database.ui")
class UnlockedDatabase(Adw.Bin):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    __gtype_name__ = "UnlockedDatabase"

    # Connection handlers
    db_locked_handler: int | None = None
    # Used only to delete the clipboard if the window is not active.
    on_is_active_handler: int | None = None
    _current_element: SafeElement | None = None
    _lock_timer_handler: int | None = None
    save_loop: int | None = None  # If int, a thread periodically saves the database
    session_handler_id: int | None = None

    action_bar = Gtk.Template.Child()
    _edit_page = Gtk.Template.Child()
    headerbar_stack = Gtk.Template.Child()
    _main_view = Gtk.Template.Child()
    _stack = Gtk.Template.Child()
    _navigation_view = Gtk.Template.Child()
    _unlocked_db_stack = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()

    selection_mode = GObject.Property(type=bool, default=False)
    undo_data: UndoData | None = None
    attribute_undo_data: AttributeUndoData | None = None

    class Mode(IntEnum):
        ENTRY = 0
        GROUP = 1
        GROUP_EDIT = 2
        SEARCH = 3
        SELECTION = 4

    def __init__(self, window: Window, dbm: DatabaseManager):
        super().__init__()
        # Instances
        self.window: Window = window
        self.database_manager: DatabaseManager = dbm

        root_group = SafeGroup.get_root(dbm)
        self.props.current_element = root_group
        self._mode = self.Mode.GROUP

        # Actionbar has to be setup before edit entry & group headerbars.
        mobile_pathbar = Pathbar(self)
        self.pathbar = Pathbar(self)
        self.action_bar.pack_start(mobile_pathbar)

        # Headerbars
        self.selection_mode_headerbar = SelectionModeHeaderbar(self)
        self.headerbar = UnlockedHeaderBar(self)

        self.headerbar_stack.add_child(self.selection_mode_headerbar)
        self.headerbar_stack.add_child(self.headerbar)

        # self.search has to be loaded after the search headerbar.
        self._search_active = False
        self.search: Search = Search(self)
        self._unlocked_db_stack.add_named(self.search, "search")
        self.search.initialize()

        # Browser Mode
        self.show_browser_page(self.current_element)  # type: ignore

        self.setup()

        self.clipboard = self.get_clipboard()

        self.connect("notify::selection-mode", self._on_selection_mode_changed)
        self.db_locked_handler = self.database_manager.connect(
            "notify::locked", self._on_database_lock_changed
        )

        # Sets the menu's save button sensitive property.
        save_action = window.lookup_action("db.save_dirty")
        dbm.bind_property("is-dirty", save_action, "enabled")

        search_action = Gio.PropertyAction.new("db.search", self, "search-active")
        window.add_action(search_action)

        def on_locked(dbm, _spec):
            if dbm.locked:
                self.search_bar.set_key_capture_widget(None)
            else:
                self.search_bar.set_key_capture_widget(window)

        dbm.connect("notify::locked", on_locked)
        self.search_bar.set_key_capture_widget(window)

        self.search_bar.connect_entry(self.search_entry)
        self.bind_property("search-active", self.search_bar, "search-mode-enabled")

    def inner_dispose(self):
        logging.debug("Database disposed")
        self.cleanup()

        if self.db_locked_handler:
            self.database_manager.disconnect(self.db_locked_handler)
            self.db_locked_handler = None

    def setup(self):
        self.start_save_loop()
        self.start_database_lock_timer()

        app = self.window.props.application
        self.session_handler_id = app.connect(
            "notify::screensaver-active", self.on_session_lock
        )

    def listbox_row_factory(self, element: SafeElement) -> Gtk.Widget:
        if element.is_entry:
            row = EntryRow(self)
            row.props.safe_entry = element
            return row

        row = GroupRow(self)
        row.props.safe_group = element
        return row

    def show_edit_page(self, element: SafeElement, new: bool = False) -> None:
        self.start_database_lock_timer()
        self.props.current_element = element

        if self.props.search_active:
            self.props.search_active = False

        # Sets the accessed time.
        element.touch()

        if element.is_group:
            page = GroupPage(self, element)
            self.props.mode = self.Mode.GROUP_EDIT
        else:
            page = EntryPage(self, element, new)
            self.props.mode = self.Mode.ENTRY

        self._edit_page.set_child(page)
        self._navigation_view.push(self._edit_page)

    def show_browser_page(self, group: SafeGroup) -> None:
        self.start_database_lock_timer()
        self._unlocked_db_stack.set_visible_child(self._stack)
        if self._navigation_view.props.visible_page == self._edit_page:
            # pop triggers _on_edit_page_hidden via the hidden signal.
            self._navigation_view.pop()
        else:
            self._set_current_element_after_pop(group)

    def _set_current_element_after_pop(self, group):
        page_name = group.uuid.urn
        if page := self._stack.get_child_by_name(page_name):
            self.props.current_element = page.group
        else:
            self.props.current_element = group
            new_page = UnlockedDatabasePage(self, group)
            self._stack.add_named(new_page, page_name)

        if not self.props.selection_mode:
            self.props.mode = self.Mode.GROUP

        self._stack.set_visible_child_name(page_name)

    @property
    def in_edit_page(self) -> bool:
        """Returns true if the current visible page is either
        the Group edit page or Entry edit page."""

        boolean: bool = (
            self._navigation_view.props.visible_page == self._edit_page
        )
        return boolean

    def _on_selection_mode_changed(
        self, _unlocked_database: UnlockedDatabase, _value: GObject.ParamSpec
    ) -> None:
        if self.props.selection_mode:
            self.props.mode = self.Mode.SELECTION
            self.headerbar_stack.set_visible_child(self.selection_mode_headerbar)
        else:
            self.headerbar_stack.set_visible_child(self.headerbar)

    #
    # Group and Entry Management
    #

    @GObject.Property(type=SafeElement)
    def current_element(self) -> SafeElement:
        return self._current_element

    @current_element.setter  # type: ignore
    def current_element(self, element: SafeElement) -> None:
        self._current_element = element

    def get_current_page(self) -> UnlockedDatabasePage:
        """Returns the page associated with current_element.

        :returns: current page
        :rtype: Gtk.Widget
        """
        element_uuid = self.props.current_element.uuid
        return self._stack.get_child_by_name(element_uuid.urn)

    def delete_page(self, element):
        if page := self._stack.get_child_by_name(element.uuid.urn):
            self._stack.remove(page)

    #
    # Events
    #

    def on_list_box_row_activated(self, _widget, list_box_row):
        self.start_database_lock_timer()

        if self.props.search_active:
            self.props.search_active = False

        if list_box_row.__gtype_name__ == "GroupRow":
            safe_group = list_box_row.safe_group
            self.show_browser_page(safe_group)
        else:
            if self.selection_mode:
                active = list_box_row.selection_checkbox.props.active
                list_box_row.selection_checkbox.props.active = not active
                return

            safe_entry = list_box_row.safe_entry
            self.show_edit_page(safe_entry)

    def on_save(
        self, database_manager: DatabaseManager, result: Gio.AsyncResult
    ) -> None:
        try:
            is_saved = database_manager.save_finish(result)
        except GLib.Error as err:
            logging.error("Could not save Safe: %s", err.message)
            self.window.send_notification(_("Could not save Safe"))
        else:
            if is_saved:
                self.window.send_notification(_("Safe saved"))
            else:
                self.window.send_notification(_("No changes made"))

    def on_auto_save(
        self, database_manager: DatabaseManager, result: Gio.AsyncResult
    ) -> None:
        # TODO Does it make sense to present this info to the user?
        try:
            database_manager.save_finish(result)
        except GLib.Error as err:
            logging.error("Could not automatically save Safe %s", err.message)

    def lock_safe(self):
        self.database_manager.props.locked = True

    def on_add_entry_action(self) -> None:
        """CB when the Add Entry menu was clicked"""
        group = self.props.current_element
        new_entry: SafeEntry = group.new_entry()
        self.show_edit_page(new_entry, new=True)

    def on_add_group_action(self) -> None:
        """CB when menu entry Add Group is clicked"""
        group = self.props.current_element
        safe_group = group.new_subgroup()
        self.show_edit_page(safe_group)

    def on_element_delete_action(self) -> None:
        """Delete the visible entry from the menu."""
        element = self.props.current_element
        parent_group = self.props.current_element.parentgroup
        if element.trash():
            self.delete_page(element)
            elements = []
        else:
            elements = [(element, parent_group)]

        self.deleted_notification(elements)

        self.show_browser_page(parent_group)

    def deleted_notification(self, elements):
        n_del = len(elements)
        if n_del:
            label = ngettext(
                # pylint: disable=consider-using-f-string
                "Element deleted",
                "{} Elements deleted".format(n_del),
                n_del,
            )
        else:
            label = _("Deletion completed")

        toast = Adw.Toast.new(label)

        if n_del:
            toast.props.button_label = _("Undo")
            toast.props.action_name = "win.db.undo_delete"

        if data := self.undo_data:
            data.toast.dismiss()

        def dismissed_db(toast):
            if data := self.undo_data:
                if data.toast == toast:
                    self.undo_data = None

        toast.connect("dismissed", dismissed_db)

        self.undo_data = UndoData(elements, toast)
        self.window.toast_overlay.add_toast(toast)

    def undo_delete(self):
        if data := self.undo_data:
            for element, element_parent in data.elements:
                element.move_to(element_parent)

            self.undo_data = None

    def attribute_deleted(self, entry, key, value, protected):
        toast = Adw.Toast.new(_("Attribute deleted"))
        toast.props.button_label = _("Undo")
        toast.props.action_name = "win.db.undo_attribute_delete"

        if data := self.attribute_undo_data:
            data.toast.dismiss()

        undo_data = AttributeUndoData(toast, entry, key, value, protected)
        self.attribute_undo_data = undo_data
        self.window.toast_overlay.add_toast(toast)

    def undo_attribute_delete(self):
        if data := self.attribute_undo_data:
            data.toast.dismiss()
            data.entry.set_attribute(data.key, data.value, data.protected)

            self.attribute_undo_data = None

    def on_entry_duplicate_action(self):
        self.props.current_element.duplicate()
        parent_group = self.props.current_element.parentgroup

        self.show_browser_page(parent_group)

    def send_to_clipboard(
        self,
        text: str,
        message: str = "",
        toast_overlay: Adw.ToastOverlay | None = None,
    ) -> None:
        if not message:
            message = _("Copied")

        self.start_database_lock_timer()

        if self.on_is_active_handler:
            self.disconnect(self.on_is_active_handler)
            self.on_is_active_handler = None

        self.clipboard.set(text)

        if toast_overlay:
            window = toast_overlay.get_root()
            toast = Adw.Toast.new(message)
            toast_overlay.add_toast(toast)
        else:
            window = self.window
            self.window.send_notification(message)

        clear_clipboard_time = gsecrets.config_manager.get_clear_clipboard()
        clipboard_last_content = self.clipboard.get_content()

        def callback():
            if window.props.is_active:
                if clipboard_last_content == self.clipboard.get_content():
                    logging.debug("Clipboard cleared")
                    self.clipboard.set_content(None)
            else:
                logging.debug(
                    "Could not clear the clipboard, it will clear on new focus"
                )

                def on_is_active(window, _pspec):
                    if self.on_is_active_handler:
                        window.disconnect(self.on_is_active_handler)
                        self.on_is_active_handler = None

                    # Only clear clipboard if we set ourselves the content.
                    if clipboard_last_content == self.clipboard.get_content():
                        logging.debug("Clipboard cleared")
                        self.clipboard.set_content(None)

                self.on_is_active_handler = window.connect(
                    "notify::is-active", on_is_active
                )

            return GLib.SOURCE_REMOVE

        GLib.timeout_add_seconds(clear_clipboard_time, callback)

    def show_database_settings(self) -> None:
        DatabaseSettingsDialog(self).present()

    def on_session_lock(self, app: Gtk.Application, _pspec: GObject.ParamSpec) -> None:
        if (
            app.props.screensaver_active
            and not self.database_manager.props.locked
            and gsecrets.config_manager.get_lock_on_session_lock()
        ):
            self.lock_timeout_database()

    #
    # Dialog Creator
    #

    def show_references_dialog(self) -> None:
        """Show a Group/Entry reference dialog

        Invoked by the app.entry.references action"""
        ReferencesDialog(self).present()

    def show_properties_dialog(self) -> None:
        """Show a Group/Entry property dialog

        Invoked by the app.element.properties action"""
        PropertiesDialog(self).present()

    #
    # Utils
    #

    def _on_database_lock_changed(self, _database_manager, _value):
        locked = self.database_manager.props.locked
        if locked:
            self.cleanup()
            if gsecrets.config_manager.get_save_automatically():
                self.auto_save_database()

            filepath = self.database_manager.path
            self.window.start_database_opening_routine(filepath)
        else:
            self.window.view = self.window.View.UNLOCKED_DATABASE
            self.setup()

    def lock_timeout_database(self):
        self.database_manager.props.locked = True

        # NOTE: Notification that a safe has been locked.
        self.window.send_notification(_("Safe locked due to inactivity"))

    #
    # Helper Methods
    #

    def cleanup(self) -> None:
        """Stop all ongoing operations:

        * stop the save loop
        * cancel all timers
        * stop lisening to screensaver

        This is the opposite of setup().
        """
        logging.debug("Cleaning database %s", self.database_manager.path)

        if self._lock_timer_handler:
            GLib.source_remove(self._lock_timer_handler)
            self._lock_timer_handler = None

        # Do not listen to screensaver kicking in anymore
        if self.session_handler_id:
            app = self.window.props.application
            if app:
                app.disconnect(self.session_handler_id)

            self.session_handler_id = None

        # stop the save loop
        if self.save_loop:
            GLib.source_remove(self.save_loop)
            self.save_loop = None

        # Cleanup temporal files created when opening attachments.
        def callback(gfile, result):
            try:
                gfile.delete_finish(result)
            except GLib.Error as err:
                logging.debug("Could not delete temporal file: %s", err.message)

        cache_dir = os.path.join(GLib.get_user_cache_dir(), const.SHORT_NAME, "tmp")
        for root, _dirs, files in os.walk(cache_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                gfile = Gio.File.new_for_path(file_path)
                gfile.delete_async(GLib.PRIORITY_DEFAULT, None, callback)

    def save_database(self) -> None:
        """Save the database.

        Shows a notification after saving.
        """

        def on_check_file_changes(dbm, result):
            self.on_check_file_changes(dbm, result, self.on_save)

        self.database_manager.check_file_changes_async(on_check_file_changes)

    def auto_save_database(self) -> None:
        """Save the database."""
        logging.debug("Automatically saving database")

        def on_check_file_changes(dbm, result):
            self.on_check_file_changes(dbm, result, self.on_auto_save)

        self.database_manager.check_file_changes_async(on_check_file_changes)

    def on_check_file_changes(self, dbm, result, on_save_callback):
        try:
            conflicts = dbm.check_file_changes_finish(result)
        except GLib.Error as err:
            logging.error("Could not monitor file changes: %s", err.message)
            self.window.send_notification(_("Could not save Safe"))
        else:
            if conflicts:
                dialog = SavingConflictDialog(self.window, dbm, on_save_callback)
                dialog.present()
            else:
                self.database_manager.save_async(on_save_callback)

    def start_database_lock_timer(self):
        if self._lock_timer_handler:
            GLib.source_remove(self._lock_timer_handler)
            self._lock_timer_handler = None

        if self.database_manager.props.locked:
            return

        timeout = gsecrets.config_manager.get_database_lock_timeout() * 60
        if timeout:
            self._lock_timer_handler = GLib.timeout_add_seconds(
                timeout, self.lock_timeout_database
            )

    def start_save_loop(self):
        logging.debug("Starting automatic save loop")
        self.save_loop = GLib.timeout_add_seconds(30, self.threaded_save_loop)

    def threaded_save_loop(self) -> bool:
        """Saves the safe as long as it returns True."""
        if gsecrets.config_manager.get_save_automatically():
            self.auto_save_database()

        return GLib.SOURCE_CONTINUE

    def go_back(self):
        if self.props.selection_mode:
            self.props.selection_mode = False
            self.props.mode = self.Mode.GROUP
            return
        if self.props.search_active:
            self.props.search_active = False
            self.props.mode = self.Mode.GROUP
            return
        if self.props.current_element.is_root_group:
            return

        parent = self.props.current_element.parentgroup
        self.show_browser_page(parent)

    @GObject.Property(type=bool, default=False)
    def search_active(self) -> bool:
        """Property to know if search is active.

        It is used by Search to update the widgets accordingly.

        :returns: True is search is active
        :rtype: bool
        """
        return self._search_active

    @search_active.setter  # type: ignore
    def search_active(self, value: bool) -> None:
        """Set the search mode

        :param value: new search_active
        """
        if (
            self.database_manager.props.locked
            or self.selection_mode
            or self.in_edit_page
        ):
            return

        self._search_active = value
        if self._search_active:
            self.props.mode = self.Mode.SEARCH
            self._unlocked_db_stack.set_visible_child_name("search")
        else:
            self.show_browser_page(self.current_element)

    # TODO This property does not emit a notify signal when the manager locked
    # property is updated.
    @GObject.Property(type=bool, default=False)
    def database_locked(self):
        """Get database lock status

        :returns: True if the database is locked
        :rtype: bool
        """
        return self.database_manager.props.locked

    @GObject.Property(type=int, default=0)
    def mode(self) -> int:
        return self._mode

    @mode.setter  # type: ignore
    def mode(self, new_mode: int) -> None:
        self._mode = new_mode

    @Gtk.Template.Callback()
    def _on_edit_page_hidden(self, _page):
        # Makes sure that current_element is set correctly.
        parent = self.props.current_element.parentgroup
        self._set_current_element_after_pop(parent)
