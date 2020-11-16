# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import GObject, Gtk, Handy


class UnlockedHeaderBar(Handy.HeaderBar):

    __gtype_name__ = "UnlockedHeaderBar"

    def __new__(cls, unlocked_database):
        builder = Gtk.Builder()
        builder.add_from_resource(
            "/org/gnome/PasswordSafe/unlocked_headerbar.ui")

        new_object = builder.get_object("headerbar")
        new_object.finish_initializing(builder, unlocked_database)
        return new_object

    def finish_initializing(self, builder, unlocked_database):
        self.builder = builder
        self._unlocked_database = unlocked_database
        self._db_manager = unlocked_database.database_manager
        self._pathbar = unlocked_database.pathbar

        self._headerbar_box = self.builder.get_object("headerbar_box")
        self._show_pathbar = True

        self._search_button = self.builder.get_object("search_button")
        self._search_button.connect("clicked", self._on_search_button_clicked)
        self._unlocked_database.bind_accelerator(self._search_button, "<Control>f")

        self._selection_button_box = self.builder.get_object(
            "selection_button_box")
        self._unlocked_database.bind_property(
            "selection-mode", self._selection_button_box, "visible",
            GObject.BindingFlags.SYNC_CREATE)

        self._selection_button = self.builder.get_object("selection_button")
        self._selection_button.connect(
            "clicked", self._on_selection_button_clicked)

        self._selection_button_mobile = builder.get_object("selection_button_mobile")
        self._selection_button_mobile.connect(
            "clicked", self._on_selection_button_clicked)

        self._selection_options_button = self.builder.get_object(
            "selection_options_button")
        self._unlocked_database.bind_property(
            "selection-mode", self._selection_options_button, "visible",
            GObject.BindingFlags.SYNC_CREATE)

    def _on_search_button_clicked(self, _btn: Gtk.Button) -> None:
        self._unlocked_database.props.search_active = True

    def _on_selection_button_clicked(self, _button: Gtk.Button) -> None:
        self._unlocked_database.props.selection_mode = True

    @GObject.Property(
        type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    def show_pathbar(self):
        return self._show_pathbar

    @show_pathbar.setter  # type: ignore
    def show_pathbar(self, value):
        self._show_pathbar = value

        if self._show_pathbar:
            self._headerbar_box.add(self._pathbar)
        else:
            self._headerbar_box.remove(self._pathbar)
