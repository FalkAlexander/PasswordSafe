# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

from gi.repository import GObject, Gtk


class AddListBox(Gtk.ListBox):
    """ListBox with a Add button at the end."""

    __gtype_name__ = "AddListBox"

    _n_items: int = 0

    def __init__(self):
        super().__init__()

        self.props.selection_mode = Gtk.SelectionMode.NONE
        self.add_css_class("boxed-list")

        icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        icon.props.accessible_role = Gtk.AccessibleRole.PRESENTATION
        label = Gtk.Label.new("")
        label.props.use_underline = True

        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        hbox.props.halign = Gtk.Align.CENTER
        hbox.props.margin_start = 12
        hbox.props.margin_end = 12
        hbox.props.margin_top = 16
        hbox.props.margin_bottom = 16
        hbox.append(icon)
        hbox.append(label)

        add_more_row = Gtk.ListBoxRow.new()
        add_more_row.props.child = hbox
        add_more_row.props.activatable = True

        super().append(add_more_row)

        self._row = add_more_row
        self._label = label
        self._model = None

    @GObject.Property(type=str, default="")
    def action_name(self):
        return self._row.props.action_name

    @action_name.setter  # type: ignore
    def action_name(self, action_name):
        self._row.props.action_name = action_name

    @GObject.Property(type=str, default="")
    def label(self):
        return self._label.props.label

    @label.setter  # type: ignore
    def label(self, string):
        self._label.props.label = string

    def append(self, child):  # pylint: disable=arguments-differ
        super().insert(child, self._n_items)
        self._n_items += 1

    def remove(self, child):  # pylint: disable=arguments-differ
        if child.props.parent != self:
            return

        super().remove(child)
        self._n_items -= 1

    def _insert(self, pos, child):  # pylint: disable=arguments-differ
        super().insert(child, pos)
        self._n_items += 1

    def set_model(self, model, factory):
        self._model = model

        def on_items_changed(model, pos, removed, added):
            for idx in range(pos, pos + removed):
                if child := self.get_row_at_index(idx):
                    self.remove(child)

            for idx in range(pos, pos + added):
                item = model.get_item(idx)
                self._insert(idx, factory(item))

        on_items_changed(model, 0, 0, model.get_n_items())
        model.connect("items-changed", on_items_changed)
