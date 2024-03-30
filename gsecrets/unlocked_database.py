# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import logging
import os
import typing
from gettext import gettext as _
from gettext import ngettext
from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk

import gsecrets.config_manager
from gsecrets import const
from gsecrets.entry_page import EntryPage
from gsecrets.entry_row import EntryRow
from gsecrets.group_page import GroupPage
from gsecrets.group_row import GroupRow
from gsecrets.safe_element import SafeElement, SafeEntry, SafeGroup
from gsecrets.selection_manager import SelectionManager
from gsecrets.unlocked_headerbar import UnlockedHeaderBar
from gsecrets.widgets.browsing_panel import BrowsingPanel
from gsecrets.widgets.database_settings_dialog import DatabaseSettingsDialog
from gsecrets.widgets.properties_dialog import PropertiesDialog
from gsecrets.widgets.references_dialog import ReferencesDialog
from gsecrets.widgets.saving_conflict_dialog import SavingConflictDialog

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
class UnlockedDatabase(Adw.BreakpointBin):
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

    headerbar_stack = Gtk.Template.Child()
    _split_view = Gtk.Template.Child()
    toolbar_view = Gtk.Template.Child()
    _select_entry_status_page = Gtk.Template.Child()
    _empty_page = Gtk.Template.Child()

    _search_active: bool = False
    _search_bar = Gtk.Template.Child()
    _search_entry = Gtk.Template.Child()

    _selection_mode: bool = False
    _selection_mode_headerbar = Gtk.Template.Child()
    _selection_mode_action_bar = Gtk.Template.Child()
    _delete_selection_button = Gtk.Template.Child()
    _cut_selection_button = Gtk.Template.Child()
    _paste_selection_button = Gtk.Template.Child()
    _selection_mode_title = Gtk.Template.Child()
    _cut_paste_button_stack = Gtk.Template.Child()
    _clear_selection_button = Gtk.Template.Child()

    undo_data: UndoData | None = None
    attribute_undo_data: AttributeUndoData | None = None

    def __init__(self, window: Window, dbm: DatabaseManager):
        super().__init__()
        # Instances
        self.window: Window = window
        self.database_manager: DatabaseManager = dbm

        root_group = SafeGroup.get_root(dbm)
        self.props.current_element = root_group

        # Headerbars
        self.headerbar = UnlockedHeaderBar(self)

        self.headerbar_stack.add_child(self.headerbar)
        self.headerbar_stack.props.visible_child = self.headerbar

        self._select_entry_status_page.props.icon_name = f"{const.APP_ID}-symbolic"

        self.active_element: SafeElement | None = None

        # Browser Mode
        self.browsing_panel = BrowsingPanel(self)
        self.toolbar_view.props.content = self.browsing_panel

        self.setup()

        self.clipboard = self.get_clipboard()

        self.db_locked_handler = self.database_manager.connect(
            "notify::locked",
            self._on_database_lock_changed,
        )

        # Sets the menu's save button sensitive property.
        save_action = window.lookup_action("db.save_dirty")
        dbm.bind_property("is-dirty", save_action, "enabled")

        search_action = Gio.PropertyAction.new("db.search", self, "search-active")
        window.add_action(search_action)

        def on_locked(dbm, _spec):
            if dbm.locked:
                self._search_bar.set_key_capture_widget(None)
            else:
                self._search_bar.set_key_capture_widget(window)

        dbm.connect("notify::locked", on_locked)
        self._search_bar.set_key_capture_widget(window)

        self._search_entry.connect("search-changed", self._on_search_changed)
        self.bind_property(
            "search-active",
            self._search_bar,
            "search-mode-enabled",
            GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL,
        )

        self._split_view.connect("notify::show-content", self._on_show_content_notify)
        self._split_view.connect("notify::collapsed", self._on_collapsed_notify)

        self._selection_manager = SelectionManager(self)

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
            "notify::screensaver-active",
            self.on_session_lock,
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
        self.active_element = element

        # Sets the accessed time.
        element.touch()

        if element.is_group:
            page = GroupPage(self, element)
        else:
            page = EntryPage(self, element, new)

        page = Adw.NavigationPage.new(page, "Edit")
        self._split_view.props.content = page
        self._split_view.props.show_content = True

    def show_browser_page(self, group: SafeGroup) -> None:
        self.start_database_lock_timer()

        self.active_element = group
        self.props.current_element = group
        self._split_view.props.show_content = False
        self.browsing_panel.visit_group(group)

    def _navigate_back(self):
        if element := self.active_element:
            parent_group = element.parentgroup
            self.show_browser_page(parent_group)
            return

        self.show_browser_page(self.current_element)

    #
    # Group and Entry Management
    #

    @GObject.Property(type=SafeElement)
    def current_element(self) -> SafeElement:
        # FIXME Rename to current_group, check all uses
        return self._current_element

    @current_element.setter  # type: ignore
    def current_element(self, element: SafeElement) -> None:
        self._current_element = element

    #
    # Events
    #

    def on_save(
        self,
        database_manager: DatabaseManager,
        result: Gio.AsyncResult,
    ) -> None:
        try:
            is_saved = database_manager.save_finish(result)
        except GLib.Error:
            logging.exception("Could not save Safe")
            self.window.send_notification(_("Could not save Safe"))
        else:
            if is_saved:
                self.window.send_notification(_("Safe saved"))
            else:
                self.window.send_notification(_("No changes made"))

    def on_auto_save(
        self,
        database_manager: DatabaseManager,
        result: Gio.AsyncResult,
    ) -> None:
        # TODO Does it make sense to present this info to the user?
        try:
            database_manager.save_finish(result)
        except GLib.Error:
            logging.exception("Could not automatically save Safe")

    def lock_safe(self):
        self.database_manager.props.locked = True

    def on_add_entry_action(self) -> None:
        """CB when the Add Entry menu was clicked."""
        group = self.props.current_element
        new_entry: SafeEntry = group.new_entry()
        self.show_edit_page(new_entry, new=True)

    def on_add_group_action(self) -> None:
        """CB when menu entry Add Group is clicked."""
        group = self.props.current_element
        safe_group = group.new_subgroup()
        self.show_edit_page(safe_group)

    def on_element_delete_action(self) -> None:
        """Delete the visible entry from the menu."""
        if element := self.active_element:
            parent_group = element.parentgroup
            self.browsing_panel.unselect(element)
            if element.trash():
                elements = []
            else:
                elements = [(element, parent_group)]

            self._split_view.props.content = self._empty_page
            self.deleted_notification(elements)
            self._navigate_back()

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
            if (data := self.undo_data) and data.toast == toast:
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
        if element := self.active_element:
            element.duplicate()
            self._navigate_back()

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
                    "Could not clear the clipboard, it will clear on new focus",
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
                    "notify::is-active",
                    on_is_active,
                )

            return GLib.SOURCE_REMOVE

        GLib.timeout_add_seconds(clear_clipboard_time, callback)

    def show_database_settings(self) -> None:
        DatabaseSettingsDialog(self).present(self)

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
        """Show a Group/Entry reference dialog.

        Invoked by the app.entry.references action
        """
        ReferencesDialog(self).present(self)

    def show_properties_dialog(self) -> None:
        """Show a Group/Entry property dialog.

        Invoked by the app.element.properties action
        """
        PropertiesDialog(self).present(self)

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
        """Stop all ongoing operations.

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
            except GLib.Error:
                logging.exception("Could not delete temporal file")

        cache_dir = Path(GLib.get_user_cache_dir()) / const.SHORT_NAME / "tmp"
        for root, _dirs, files in os.walk(cache_dir):
            for file_name in files:
                file_path = Path(root) / file_name
                gfile = Gio.File.new_for_path(str(file_path))
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
        except GLib.Error:
            logging.exception("Could not monitor file changes")
            self.window.send_notification(_("Could not save Safe"))
        else:
            if conflicts:
                dialog = SavingConflictDialog(self.window, dbm, on_save_callback)
                dialog.present(self.window)
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
                timeout,
                self.lock_timeout_database,
            )

    def start_save_loop(self):
        logging.debug("Starting automatic save loop")
        self.save_loop = GLib.timeout_add_seconds(30, self.threaded_save_loop)

    def threaded_save_loop(self) -> bool:
        """Return True if the safe was saved."""
        if gsecrets.config_manager.get_save_automatically():
            self.auto_save_database()

        return GLib.SOURCE_CONTINUE

    def go_back(self):
        if self._search_active:
            self.props.search_active = False
            return

        if self._selection_mode:
            self.props.selection_mode = False
            return

        self._navigate_back()

    @Gtk.Template.Callback()
    def _on_selection_go_back_button_clicked(self, _button):
        self.headerbar.on_go_back_button_clicked(None)

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
        """Set the search mode.

        :param value: new search_active
        """
        self._search_active = value

        if not value:
            self.browsing_panel.set_search(None)

    # TODO This property does not emit a notify signal when the manager locked
    # property is updated.
    @GObject.Property(type=bool, default=False)
    def database_locked(self):
        """Get database lock status.

        :returns: True if the database is locked
        :rtype: bool
        """
        return self.database_manager.props.locked

    @GObject.Property(type=bool, default=False)
    def selection_mode(self) -> bool:
        return self._selection_mode

    @selection_mode.setter  # type: ignore
    def selection_mode(self, value: bool) -> None:
        self._selection_mode = value
        self._selection_mode_action_bar.set_revealed(value)

        if value:
            self.headerbar_stack.props.visible_child = self._selection_mode_headerbar
        else:
            self.headerbar_stack.props.visible_child = self.headerbar
            self._clear_selection()

    @Gtk.Template.Callback()
    def _on_selection_cancel_clicked(self, _button):
        self.props.selection_mode = False

    @Gtk.Template.Callback()
    def _on_clear_selection_clicked(self, _button):
        self.start_database_lock_timer()
        self._clear_selection()

    @Gtk.Template.Callback()
    def _on_cut_selection_clicked(self, _button):
        self.start_database_lock_timer()
        self._selection_manager.cut_selection()
        self._update_selection()

    @Gtk.Template.Callback()
    def _on_paste_selection_clicked(self, _button):
        self.start_database_lock_timer()
        self._selection_manager.paste_selection()
        self._update_selection()

    @Gtk.Template.Callback()
    def _on_delete_selection_clicked(self, _button):
        self.start_database_lock_timer()
        if (
            element := self.browsing_panel.selection_model.selected_item
        ) and element.selected:
            self._split_view.props.content = self._empty_page
            self._navigate_back()

        self._selection_manager.delete_selection()
        self._update_selection()

    def add_selection(self, element):
        if element.is_group:
            self._selection_manager.add_group(element)
        else:
            self._selection_manager.add_entry(element)

        self._update_selection()

    def remove_selection(self, element):
        if element.is_group:
            self._selection_manager.remove_group(element)
        else:
            self._selection_manager.remove_entry(element)

        self._update_selection()

    def _clear_selection(self):
        self._selection_manager.clear_selection()
        self._update_selection()

    def _update_selection(self):
        n_selected = self._selection_manager.selected_elements
        cut_mode = self._selection_manager.cut_mode
        non_empty_selection = n_selected > 0

        self._cut_selection_button.props.sensitive = non_empty_selection
        self._delete_selection_button.props.sensitive = non_empty_selection
        self._clear_selection_button.props.sensitive = non_empty_selection

        if n_selected == 0:
            title = _("Select Items")
        else:
            title = ngettext("{} Selected", "{} Selected", n_selected).format(
                n_selected,
            )

        self._selection_mode_title.props.title = title

        self._delete_selection_button.props.sensitive = n_selected > 0

        if cut_mode:
            visible_child = self._cut_selection_button
        else:
            visible_child = self._paste_selection_button

        self._cut_paste_button_stack.props.visible_child = visible_child

    def _update_selection_on_collapsed(self):
        nav = self._split_view
        hide_selection = nav.props.collapsed and not nav.props.show_content
        self.browsing_panel.hide_selection(hide_selection)

    def _on_show_content_notify(self, _split_view, _pspec):
        self._update_selection_on_collapsed()

    def _on_collapsed_notify(self, _split_view, _pspec):
        self._update_selection_on_collapsed()

    def _on_search_changed(self, search_entry):
        self.browsing_panel.set_search(search_entry.props.text)
