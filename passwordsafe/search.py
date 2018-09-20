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

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    def initialize(self):
        # Search Headerbar
        headerbar_search_box_close_button = self.unlocked_database.builder.get_object("headerbar_search_box_close_button")
        headerbar_search_box_close_button.connect("clicked", self.on_headerbar_search_close_button_clicked)

        search_settings_popover_local_button = self.unlocked_database.builder.get_object("search_settings_popover_local_button")
        search_settings_popover_fulltext_button = self.unlocked_database.builder.get_object("search_settings_popover_fulltext_button")

        search_local_button = self.unlocked_database.builder.get_object("search_local_button")
        search_local_button.connect("toggled", self.on_search_filter_button_toggled)

        search_fulltext_button = self.unlocked_database.builder.get_object("search_fulltext_button")
        search_fulltext_button.connect("toggled", self.on_search_filter_button_toggled)

        headerbar_search_entry = self.unlocked_database.builder.get_object("headerbar_search_entry")
        headerbar_search_entry.connect("search-changed", self.on_headerbar_search_entry_changed, search_local_button, search_fulltext_button)
        headerbar_search_entry.connect("activate", self.on_headerbar_search_entry_enter_pressed)

    #
    # Search
    #

    # Search headerbar
    def set_search_headerbar(self, widget):
        hscb = self.unlocked_database.builder.get_object("headerbar_search_box_close_button")
        if hscb.get_active() is False:
            hscb.set_active(True)

        if self.unlocked_database.window.mobile_width is True:
            self.unlocked_database.builder.get_object("headerbar_search_box").set_margin_left(0)
            self.unlocked_database.builder.get_object("headerbar_search_box").set_margin_right(0)
        else:
            self.unlocked_database.builder.get_object("headerbar_search_box").set_margin_left(90)
            self.unlocked_database.builder.get_object("headerbar_search_box").set_margin_right(47)

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

    def remove_search_headerbar(self, widget):
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

            hdy_search = Handy.Column()
            hdy_search.set_maximum_width(700)
            hdy_search.add(self.search_list_box)
            self.unlocked_database.search_overlay.add(hdy_search)

            self.search_list_box.connect("row-activated", self.unlocked_database.on_list_box_row_activated)
            viewport.add(self.unlocked_database.search_overlay)

            scrolled_page.add(viewport)
            scrolled_page.show_all()
            self.unlocked_database.stack.add_named(scrolled_page, "search")
            if len(self.search_list_box.get_children()) is 0:
                info_search_overlay = self.unlocked_database.builder.get_object("info_search_overlay")
                self.unlocked_database.search_overlay.add_overlay(info_search_overlay)
                self.search_list_box.hide()
            else:
                self.search_list_box.show()

        self.unlocked_database.stack.set_visible_child(self.unlocked_database.stack.get_child_by_name("search"))

    #
    # Utils
    #

    def search_thread_creation(self, search_local_button, widget, fulltext, result_list, empty_search_overlay, info_search_overlay):
        if search_local_button.get_active() is True:
            result_list = self.unlocked_database.database_manager.local_search(self.unlocked_database.current_group, widget.get_text(), fulltext)
        else:
            result_list = self.unlocked_database.database_manager.global_search(widget.get_text(), fulltext)

        GLib.idle_add(self.search_overlay_creation, widget, result_list, empty_search_overlay, info_search_overlay)

    def search_overlay_creation(self, widget, result_list, empty_search_overlay, info_search_overlay):
        if widget.get_text() is not "":
            if empty_search_overlay in self.unlocked_database.search_overlay:
                self.unlocked_database.search_overlay.remove(empty_search_overlay)

            self.search_list_box.show()
            self.search_instance_creation(result_list, empty_search_overlay)
        else:
            self.unlocked_database.search_overlay.add_overlay(info_search_overlay)
            self.search_list_box.hide()

    def search_instance_creation(self, result_list, empty_search_overlay):
        for uuid in result_list:
            if self.unlocked_database.database_manager.check_is_group(uuid):
                group_row = GroupRow(self.unlocked_database, self.unlocked_database.database_manager, self.unlocked_database.database_manager.get_group_object_from_uuid(uuid))
                self.search_list_box.add(group_row)
            else:
                entry_row = EntryRow(self.unlocked_database, self.unlocked_database.database_manager, self.unlocked_database.database_manager.get_entry_object_from_uuid(uuid))
                self.search_list_box.add(entry_row)

        if len(self.search_list_box.get_children()) is 0:
            self.unlocked_database.search_overlay.add_overlay(empty_search_overlay)
            self.search_list_box.hide()
        else:
            self.search_list_box.show()

    #
    # Events
    #

    def on_headerbar_search_close_button_clicked(self, widget):
        self.unlocked_database.start_database_lock_timer()
        self.remove_search_headerbar(None)
        self.unlocked_database.show_page_of_new_directory(False, False)

    def on_search_entry_navigation(self, widget, event, data=None):
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

    def on_headerbar_search_entry_changed(self, widget, search_local_button, search_fulltext_button):
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

        if search_fulltext_button.get_active() is True:
            fulltext = True

        search_thread = threading.Thread(target=self.search_thread_creation, args=(search_local_button, widget, fulltext, result_list, empty_search_overlay, info_search_overlay))
        search_thread.daemon = True
        search_thread.start()

    def on_headerbar_search_entry_enter_pressed(self, widget):
        self.unlocked_database.start_database_lock_timer()
        if widget.get_text() is not "":
            uuid = NotImplemented
            first_row = NotImplemented

            if len(self.search_list_box.get_children()) != 0:
                selected_row = self.search_list_box.get_selected_row()
                if selected_row is None:
                    if self.search_list_box.get_children()[0].type is "GroupRow":
                        uuid = self.search_list_box.get_children()[0].get_group_uuid()
                        first_row = self.unlocked_database.database_manager.get_group_object_from_uuid(uuid)
                    else:
                        uuid = self.search_list_box.get_children()[0].get_entry_uuid()
                        first_row = self.unlocked_database.database_manager.get_entry_object_from_uuid(uuid)
                else:
                    if selected_row.type is "GroupRow":
                        uuid = selected_row.get_group_uuid()
                        first_row = self.unlocked_database.database_manager.get_group_object_from_uuid(uuid)
                    else:
                        uuid = selected_row.get_entry_uuid()
                        first_row = self.unlocked_database.database_manager.get_entry_object_from_uuid(uuid)

                self.unlocked_database.current_group = first_row
                self.unlocked_database.pathbar.add_pathbar_button_to_pathbar(uuid)
                self.unlocked_database.show_page_of_new_directory(False, False)


    def on_search_filter_button_toggled(self, widget):
        headerbar_search_entry = self.unlocked_database.builder.get_object("headerbar_search_entry")
        search_local_button = self.unlocked_database.builder.get_object("search_local_button")
        search_fulltext_button = self.unlocked_database.builder.get_object("search_fulltext_button")

        self.on_headerbar_search_entry_changed(headerbar_search_entry, search_local_button, search_fulltext_button)

