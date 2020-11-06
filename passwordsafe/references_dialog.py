from gi.repository import Gtk


class ReferencesDialog():
    dialog = NotImplemented

    unlocked_database = NotImplemented
    database_manager = NotImplemented
    builder = NotImplemented

    reference_entry = NotImplemented
    property = "P"

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/references_dialog.ui")

        self.assemble_dialog()

    def assemble_dialog(self):
        self.dialog = self.builder.get_object("references_dialog")

        # Dialog
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(self.unlocked_database.window)
        self.dialog.present()

        self.unlocked_database.references_dialog = self.dialog
        self.dialog.connect("delete-event", self.on_dialog_quit)

        self.reference_entry = self.builder.get_object("reference_entry")
        self.reference_entry.connect("icon-press", self.on_copy_secondary_button_clicked)

        self.connect_model_buttons_signals()

    def connect_model_buttons_signals(self):
        self.builder.get_object("property_label").connect("button-press-event", self.open_codes_popover)
        self.builder.get_object("identifier_label").connect("button-press-event", self.open_codes_popover)
        self.builder.get_object("uuid_label").connect("button-press-event", self.open_uuid_popover)

        self.builder.get_object("title_button").connect("clicked", self.on_property_model_button_clicked)
        self.builder.get_object("username_button").connect("clicked", self.on_property_model_button_clicked)
        self.builder.get_object("password_button").connect("clicked", self.on_property_model_button_clicked)
        self.builder.get_object("url_button").connect("clicked", self.on_property_model_button_clicked)
        self.builder.get_object("notes_button").connect("clicked", self.on_property_model_button_clicked)

        self.update_reference_entry()

    def update_reference_entry(self):
        """Update the reference entry and selected label text."""
        uuid = self.database_manager.get_entry_uuid_from_entry_object(
            self.unlocked_database.current_element)
        encoded_uuid = uuid.hex.upper()

        self.builder.get_object("selected_property_label").set_text(self.property)

        self.reference_entry.set_text("{REF:" + self.property + "@I:" + encoded_uuid + "}")

    #
    # Events
    #

    def on_copy_secondary_button_clicked(self, widget, _position, _eventbutton):
        self.unlocked_database.clipboard.set_text(widget.get_text(), -1)

    def on_property_model_button_clicked(self, widget):
        self.property = widget.get_name()
        self.update_reference_entry()

    def open_codes_popover(self, widget, _label):
        codes_popover = self.builder.get_object("codes_popover")
        codes_popover.set_relative_to(widget)
        codes_popover.popup()

    def open_uuid_popover(self, widget, _label):
        uuid_popover = self.builder.get_object("uuid_popover")
        uuid_popover.set_relative_to(widget)
        uuid_popover.popup()

    #
    # Tools
    #

    def on_dialog_quit(self, _window, _event):
        self.unlocked_database.references_dialog = NotImplemented
