# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gio, GObject, Gtk

from gsecrets.safe_element import SafeElement


class SingleSelection(GObject.Object, Gio.ListModel, Gtk.SelectionModel):
    selected_item = GObject.Property(type=SafeElement)

    def __init__(self, model):
        super().__init__()

        self._inner = Gtk.SingleSelection.new()
        self._inner.props.autoselect = False
        self._inner.props.can_unselect = True
        self._inner.props.model = model

        self._inner.connect("items-changed", self._on_items_changed)
        self._inner.connect("selection-changed", self._on_selection_changed)

    def do_get_item(self, pos):
        return self._inner.get_item(pos)

    def do_get_n_items(self):
        return self._inner.get_n_items()

    def do_get_item_type(self):
        return self._inner.get_item_type()

    def do_is_selected(self, pos):
        return self._inner.is_selected(pos)

    def do_select_item(self, pos, _unselect_rest):
        elem = self._inner.get_item(pos)
        self._inner.props.selected = pos
        self.props.selected_item = elem

        return True

    def unselect(self):
        self._inner.props.selected = Gtk.INVALID_LIST_POSITION
        self.selected_item = None

    def _on_items_changed(self, _model, pos, removed, added):
        self.items_changed(pos, removed, added)

        # Item is still selected
        if self._inner.props.selected != Gtk.INVALID_LIST_POSITION:
            return

        # Unchanged
        if self._inner.props.selected < pos:
            return

        up_to = min(pos + added + 1, self.get_n_items())
        for idx in range(pos, up_to):
            if self.selected_item == self.get_item(idx):
                self._inner.props.selected = idx
                break

    def _on_selection_changed(self, _model, pos, n_changes):
        self.selection_changed(pos, n_changes)
