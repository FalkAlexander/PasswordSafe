"""Responsible for displaying the Entry/Group Properties"""
from gi.repository import Gtk


class PropertiesDialog:
    """Displays a modal dialog with Entry/Group Properties"""

    def __init__(self, database):
        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/org/gnome/PasswordSafe/properties_dialog.ui")
        self.dialog = self.builder.get_object("properties_dialog")
        self._database = database
        self._db_manager = database.database_manager
        self.dialog.set_transient_for(self._database.window)
        self.update_properties()

    def present(self):
        """Present the dialog"""
        self.dialog.present()

    def update_properties(self) -> None:
        """Construct dialog content with the attributes of the Entry|Group"""
        element = self._database.current_group
        hex_uuid = element.uuid.hex.upper()
        self.builder.get_object("label_uuid").set_text(hex_uuid)
        self.builder.get_object("label_accessed").set_text(
            self._db_manager.get_element_acessed_date(element)
        )
        self.builder.get_object("label_modified").set_text(
            self._db_manager.get_element_modified_date(element)
        )
        self.builder.get_object("label_created").set_text(
            self._db_manager.get_element_creation_date(element)
        )
