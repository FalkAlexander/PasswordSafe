#!/usr/bin/env python3

from gi.repository import Gio, GLib, GObject, Gtk

from gsecrets.safe_element import SafeElement


class Selection(GObject.Object, Gio.ListModel, Gtk.SelectionModel):

    selected_item = GObject.Property(type=SafeElement)

    def __init__(self, model, unlocked_db):
        super().__init__()

        self.inner = Gtk.SingleSelection(
            autoselect=False, can_unselect=True, model=model,
        )
        self.model = model
        self.unlocked_db = unlocked_db

        model.connect("items-changed", self.on_items_changed)
        self.inner.connect("selection-changed", self.on_selection_changed)

    def do_get_item(self, pos):
        return self.model.get_item(pos)

    def do_get_n_items(self):
        return self.model.get_n_items()

    def do_get_item_type(self):
        return self.model.get_item_type()

    def do_is_selected(self, pos):
        return self.inner.is_selected(pos)

    def do_select_item(self, pos, _unselect_rest):
        elem = self.model.get_item(pos)

        self.inner.set_selected(pos)
        self.props.selected_item = elem
        return True

    def on_items_changed(self, _model, pos, removed, added):
        self.items_changed(pos, removed, added)

        # Item is still selected
        if self.inner.props.selected != Gtk.INVALID_LIST_POSITION:
            return

        # Unchanged
        if self.inner.props.selected < pos:
            return

        up_to = min(pos + added + 1, self.get_n_items())
        for idx in range(pos, up_to):
            if self.selected_item == self.get_item(idx):
                self.inner.props.selected = idx
                break

    def on_selection_changed(self, _model, pos, n_changes):
        self.selection_changed(pos, n_changes)
