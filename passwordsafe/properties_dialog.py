from gi.repository import Gtk


class PropertiesDialog:
    dialog = NotImplemented

    unlocked_database = NotImplemented
    database_manager = NotImplemented
    builder = NotImplemented

    def __init__(self, unlocked_database):
        self.unlocked_database = unlocked_database
        self.database_manager = unlocked_database.database_manager
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/properties_dialog.ui")

        self.assemble_dialog()

    def assemble_dialog(self):
        self.dialog = self.builder.get_object("properties_dialog")

        # Dialog
        self.dialog.set_modal(True)
        self.dialog.set_transient_for(self.unlocked_database.window)
        self.dialog.present()

        self.unlocked_database.references_dialog = self.dialog
        self.dialog.connect("delete-event", self.on_dialog_quit)

        self.update_properties()

    def update_properties(self):
        element = self.unlocked_database.current_group

        if self.database_manager.check_is_group_object(self.unlocked_database.current_group) is True:
            encoded_uuid = self.unlocked_database.base64_to_hex(self.database_manager.get_group_uuid_from_group_object(element))
        else:
            encoded_uuid = self.unlocked_database.base64_to_hex(self.database_manager.get_entry_uuid_from_entry_object(element))

        self.builder.get_object("label_uuid").set_text(encoded_uuid)
        self.builder.get_object("label_accessed").set_text(self.database_manager.get_element_acessed_date(element))
        self.builder.get_object("label_modified").set_text(self.database_manager.get_element_modified_date(element))
        self.builder.get_object("label_created").set_text(self.database_manager.get_element_creation_date(element))
    #
    # Tools
    #

    def on_dialog_quit(self, window, event):
        self.unlocked_database.references_dialog = NotImplemented