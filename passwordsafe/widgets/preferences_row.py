# SPDX-License-Identifier: GPL-3.0-only
from gi.repository import Adw, GObject, Gtk


@Gtk.Template(resource_path="/org/gnome/World/Secrets/gtk/preferences_row.ui")
class PreferencesRow(Adw.ActionRow):

    __gtype_name__ = "PreferencesRow"

    subtitle = GObject.Property(
        type=str, default="", flags=GObject.ParamFlags.READWRITE
    )
