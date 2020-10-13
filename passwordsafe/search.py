from gi.repository import Gdk, GLib, Gtk, Handy
from passwordsafe.entry_row import EntryRow
from passwordsafe.group_row import GroupRow
from passwordsafe.scrolled_page import ScrolledPage
import threading


class Search:
    #
    # Global Variables
    #

    unlocked_database = NotImplemented
    search_active = False
    search_list_box = NotImplemented
    cached_rows = []
    skipped_rows = []

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    def initialize(self):
        # Search Headerbar
        headerbar_search_box_close_button = self.unlocked_database.builder.get_object("headerbar_search_box_close_button")
        headerbar_search_box_close_button.connect("clicked", self.on_headerbar_search_close_button_clicked)

        search_local_switch = self.unlocked_database.builder.get_object("search_local_switch")
        search_local_switch.connect("notify::active", self.on_search_filter_switch_toggled)

        search_fulltext_switch = self.unlocked_database.builder.get_object("search_fulltext_switch")
        search_fulltext_switch.connect("notify::active", self.on_search_filter_switch_toggled)

        headerbar_search_entry = self.unlocked_database.builder.get_object("headerbar_search_entry")
        headerbar_search_entry.connect("search-changed", self.on_headerbar_search_entry_changed, search_local_switch, search_fulltext_switch)
        headerbar_search_entry.connect("activate", self.on_headerbar_search_entry_enter_pressed)
        headerbar_search_entry.connect("stop-search", self.on_headerbar_search_entry_focused)

        self.unlocked_database.bind_accelerator(self.unlocked_database.accelerators, headerbar_search_entry, "<Control>f", signal="stop-search")
    #
    # Search
    #

    # Search headerbar
    def set_search_headerbar(self, _widget):
        self.unlocked_database.headerbar_search = self.unlocked_database.builder.get_object("headerbar_search")
        self.unlocked_database.parent_widget.set_headerbar(self.unlocked_database.headerbar_search)
        self.unlocked_database.window.set_titlebar(self.unlocked_database.headerbar_search)
        self.unlocked_database.builder.get_object("headerbar_search_entry").grab_focus()
        self.search_active = True
        if self.search_list_box is not NotImplemented:
            self.search_list_box.select_row(self.search_list_box.get_row_at_index(0))
            self.search_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        else:
            self.unlocked_database.builder.get_object("headerbar_search_entry").connect("key-release-event", self.on_search_entry_navigation)

        self.prepare_search_page()
        self.unlocked_database.responsive_ui.action_bar()

    def remove_search_headerbar(self, _widget):
        self.unlocked_database.parent_widget.set_headerbar(self.unlocked_database.headerbar)
        self.unlocked_database.window.set_titlebar(self.unlocked_database.headerbar)
        self.search_active = False

    #
    # Stack
    #

    # Set Search stack page
    def prepare_search_page(self):
        if self.unlocked_database.stack.get_child_by_name("search") is None:
            scrolled_page = ScrolledPage(False)
            viewport = Gtk.Viewport()
            viewport.set_name("BGPlatform")
            self.unlocked_database.search_overlay = Gtk.Overlay()
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")
            self.search_list_box = builder.get_object("list_box")

            # Responsive Container
            self.search_list_box.set_name("BrowserListBox")
            self.search_list_box.set_margin_top(18)
            self.search_list_box.set_margin_bottom(18)
            self.search_list_box.set_valign(Gtk.Align.START)

            hdy_search = Handy.Clamp()
            hdy_search.set_maximum_size(700)
            hdy_search.add(self.search_list_box)
            self.unlocked_database.search_overlay.add(hdy_search)

            self.search_list_box.connect("row-activated", self.unlocked_database.on_list_box_row_activated)
            viewport.add(self.unlocked_database.search_overlay)

            scrolled_page.add(viewport)
            scrolled_page.show_all()
            self.unlocked_database.stack.add_named(scrolled_page, "search")
            if self.search_list_box.get_children():
                self.search_list_box.show()
            else:
                info_search_overlay = self.unlocked_database.builder.get_object("info_search_overlay")
                self.unlocked_database.search_overlay.add_overlay(info_search_overlay)
                self.search_list_box.hide()

        self.unlocked_database.stack.set_visible_child(self.unlocked_database.stack.get_child_by_name("search"))

    #
    # Utils
    #

    def search_thread_creation(self, search_local_switch, widget, fulltext, result_list, empty_search_overlay, info_search_overlay):
        if search_local_switch.get_active() is True:
            result_list = self.unlocked_database.database_manager.search(widget.get_text(),
                                                                         fulltext,
                                                                         global_search=False,
                                                                         path=self.unlocked_database.current_group.path + "/")
        else:
            result_list = self.unlocked_database.database_manager.search(widget.get_text(),
                                                                         fulltext,
                                                                         global_search=True,
                                                                         path="/")

        GLib.idle_add(self.search_overlay_creation, widget, result_list, empty_search_overlay, info_search_overlay)

    def search_overlay_creation(self, widget, result_list, empty_search_overlay, info_search_overlay):
        if widget.get_text():
            if empty_search_overlay in self.unlocked_database.search_overlay:
                self.unlocked_database.search_overlay.remove(empty_search_overlay)

            self.search_list_box.show()
            self.search_instance_creation(result_list, empty_search_overlay)
        else:
            self.unlocked_database.search_overlay.add_overlay(info_search_overlay)
            self.search_list_box.hide()

    def search_instance_creation(self, result_list, empty_search_overlay, load_all=False):
        window_height = self.unlocked_database.parent_widget.get_allocation().height - 120
        group_row_height = 40
        entry_row_height = 60
        search_height = 0

        last_row = NotImplemented
        self.skipped_rows = []

        # result_list = list(set(result_list))

        for uuid in result_list:
            skip = False
            row = NotImplemented

            for cached in self.cached_rows:
                if cached.get_uuid() == uuid:
                    skip = True
                    row = cached

            if search_height < window_height or load_all is True:
                if self.unlocked_database.database_manager.check_is_group(uuid):
                    search_height += group_row_height

                    if skip is False:
                        row = GroupRow(self.unlocked_database, self.unlocked_database.database_manager, self.unlocked_database.database_manager.get_group_object_from_uuid(uuid))
                        self.search_list_box.add(row)
                        self.cached_rows.append(row)
                    else:
                        self.search_list_box.add(row)

                    last_row = row
                else:
                    search_height += entry_row_height

                    if skip is False:
                        row = EntryRow(self.unlocked_database, self.unlocked_database.database_manager, self.unlocked_database.database_manager.get_entry_object_from_uuid(uuid))
                        self.search_list_box.add(row)
                        self.cached_rows.append(row)
                    else:
                        self.search_list_box.add(row)

                    last_row = row
            else:
                self.skipped_rows.append(uuid)

        if last_row is not NotImplemented and len(self.skipped_rows) != 0:
            builder = Gtk.Builder()
            builder.add_from_resource("/org/gnome/PasswordSafe/unlocked_database.ui")
            load_more_row = builder.get_object("load_more_row")
            self.search_list_box.add(load_more_row)

        self.search_list_box.show()

        if self.search_list_box.get_children():
            self.search_list_box.show()
        else:
            self.unlocked_database.search_overlay.add_overlay(empty_search_overlay)
            self.search_list_box.hide()

    #
    # Events
    #

    def on_headerbar_search_close_button_clicked(self, _widget):
        self.unlocked_database.start_database_lock_timer()
        self.remove_search_headerbar(None)
        self.unlocked_database.show_page_of_new_directory(False, False)

    def on_search_entry_navigation(self, _widget, event, _data=None):
        self.unlocked_database.start_database_lock_timer()
        if event.keyval == Gdk.KEY_Escape:
            self.remove_search_headerbar(None)
            self.unlocked_database.show_page_of_new_directory(False, False)
        elif event.keyval == Gdk.KEY_Up:
            self.search_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            selected_row = self.search_list_box.get_selected_row()
            if selected_row is not None:
                row = self.search_list_box.get_row_at_index(selected_row.get_index() - 1)
                if row is not None:
                    self.search_list_box.select_row(row)
        elif event.keyval == Gdk.KEY_Down:
            self.search_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            selected_row = self.search_list_box.get_selected_row()
            if selected_row is None:
                row = self.search_list_box.get_row_at_index(0)
                if row is not None:
                    self.search_list_box.select_row(row)
            else:
                row = self.search_list_box.get_row_at_index(selected_row.get_index() + 1)
                if row is not None:
                    self.search_list_box.select_row(row)

    def on_headerbar_search_entry_changed(self, widget, search_local_switch, search_fulltext_switch):
        self.search_list_box.hide()
        fulltext = False
        result_list = []

        empty_search_overlay = self.unlocked_database.builder.get_object("empty_search_overlay")
        info_search_overlay = self.unlocked_database.builder.get_object("info_search_overlay")
        if info_search_overlay in self.unlocked_database.search_overlay:
            self.unlocked_database.search_overlay.remove(info_search_overlay)

        if empty_search_overlay in self.unlocked_database.search_overlay:
            self.unlocked_database.search_overlay.remove(empty_search_overlay)

        for row in self.search_list_box.get_children():
            self.search_list_box.remove(row)

        if search_fulltext_switch.get_active() is True:
            fulltext = True

        search_thread = threading.Thread(target=self.search_thread_creation, args=(search_local_switch, widget, fulltext, result_list, empty_search_overlay, info_search_overlay))
        search_thread.daemon = True
        search_thread.start()

    def on_headerbar_search_entry_enter_pressed(self, widget):
        self.unlocked_database.start_database_lock_timer()

        # Do nothing on empty search terms or no search results
        if not widget.get_text():
            return
        if len(self.search_list_box.get_children()) == 0:
            return

        uuid = NotImplemented
        first_row = NotImplemented
        selected_row = self.search_list_box.get_selected_row()

        if selected_row is None:
            selected_row = self.search_list_box.get_children()[0]
        uuid = selected_row.get_uuid()
        if selected_row.type == "GroupRow":
            first_row = self.unlocked_database.database_manager.get_group_object_from_uuid(uuid)
        else:
            first_row = self.unlocked_database.database_manager.get_entry_object_from_uuid(uuid)

        self.unlocked_database.current_group = first_row
        self.unlocked_database.pathbar.add_pathbar_button_to_pathbar(uuid)
        self.unlocked_database.show_page_of_new_directory(False, False)

    def on_search_filter_switch_toggled(self, _switch_button, _gparam):
        self.on_headerbar_search_entry_changed(
            self.unlocked_database.builder.get_object("headerbar_search_entry"),
            self.unlocked_database.builder.get_object("search_local_switch"),
            self.unlocked_database.builder.get_object("search_fulltext_switch"))

    def on_load_more_row_clicked(self, row):
        self.search_list_box.remove(row)
        self.search_instance_creation(self.skipped_rows, None, True)

    def on_headerbar_search_entry_focused(self, entry):
        if entry.has_focus() is True:
            return

        entry.grab_focus()
