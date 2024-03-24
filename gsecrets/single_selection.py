# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Gio, GObject, Gtk

from gsecrets.safe_element import SafeElement


class SingleSelection(GObject.Object, Gio.ListModel, Gtk.SelectionModel):
    def __init__(self, model):
        super().__init__()

        self._inner = Gtk.SingleSelection.new()
        self._inner.props.autoselect = False
        self._inner.props.can_unselect = True
        self._inner.props.model = model

        self._item_pos = Gtk.INVALID_LIST_POSITION
        self._hide_selected = False
        self._selected_item = None

        self._inner.connect("items-changed", self._on_items_changed)

    def do_get_item(self, pos):
        return self._inner.get_item(pos)

    def do_get_n_items(self):
        return self._inner.get_n_items()

    def do_get_item_type(self):
        return self._inner.get_item_type()

    def do_is_selected(self, pos):
        item_pos = self._item_pos
        if self._hide_selected or item_pos == Gtk.INVALID_LIST_POSITION:
            return False

        return pos == item_pos

    @GObject.Property(
        type=bool,
        default=False,
        flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.EXPLICIT_NOTIFY,
    )
    def hide_selected(self):
        return self._hide_selected

    @hide_selected.setter  # type: ignore
    def hide_selected(self, hide_selected):
        if self._hide_selected == hide_selected:
            return

        self._hide_selected = hide_selected

        if self._item_pos != Gtk.INVALID_LIST_POSITION:
            self.selection_changed(self._item_pos, 1)

        self.notify("hide_selected")

    @GObject.Property(
        type=SafeElement,
        flags=GObject.ParamFlags.READWRITE | GObject.ParamFlags.EXPLICIT_NOTIFY,
    )
    def selected_item(self):
        return self._selected_item

    @selected_item.setter  # type: ignore
    def selected_item(self, selected_item):
        if self._selected_item == selected_item:
            return

        pos = self._find_item_position(selected_item, 0, self.get_n_items())
        self._set_selected_item_inner(selected_item, pos)

    def _set_selected_item_inner(self, selected_item, pos):
        self._selected_item = selected_item

        old_pos = self._item_pos
        self._item_pos = pos

        if not self._hide_selected:
            if old_pos == Gtk.INVALID_LIST_POSITION:
                self.selection_changed(pos, 1)
            elif pos == Gtk.INVALID_LIST_POSITION:
                self.selection_changed(old_pos, 1)
            elif pos < old_pos:
                self.selection_changed(pos, old_pos - pos + 1)
            else:
                self.selection_changed(old_pos, pos - old_pos + 1)

        self.notify("selected-item")

    def _find_item_position(self, item, start_pos, end_pos):
        model = self._inner.props.model
        for pos in range(start_pos, end_pos):
            if model.get_item(pos) == item:
                return pos

        return Gtk.INVALID_LIST_POSITION

    def _on_items_changed(self, _model, position, removed, added):
        item_position = self._item_pos

        if selected_item := self._selected_item:
            if item_position == Gtk.INVALID_LIST_POSITION:
                # Maybe the item got newly added
                self._item_pos = self._find_item_position(
                    selected_item,
                    position,
                    position + added,
                )
            elif item_position < position:
                # Nothing to do, position stays the same
                pass
            elif item_position < position + removed:
                self._item_pos = self._find_item_position(
                    selected_item,
                    position,
                    position + added,
                )
            elif item_position + added >= removed:
                self._item_pos = item_position + added - removed
            else:
                # This should never happen.
                self._item_pos = 0

        self.items_changed(position, removed, added)
