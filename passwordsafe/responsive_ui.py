# SPDX-License-Identifier: GPL-3.0-only
import os


class ResponsiveUI():
    #
    # Global Variables
    #

    unlocked_database = NotImplemented

    #
    # Init
    #

    def __init__(self, u_d):
        self.unlocked_database = u_d

    #
    # Responsive Controls
    #

    def action_bar(self):
        """Move pathbar between top headerbar and bottom actionbar if needed"""

        db = self.unlocked_database  # pylint: disable=C0103
        page = db.get_current_page()
        if page is None:
            # Initial placement of pathbar before content appeared
            if db.window.props.mobile_width and not db.action_bar.get_children():
                # mobile mode
                db.action_bar.add(self.unlocked_database.pathbar)
                db.action_bar.show()
                db.revealer.set_reveal_child(True)
            elif not db.window.props.mobile_width:
                # desktop mode
                db.headerbar.props.show_pathbar = True
            return

        if db.props.search_active:
            # No pathbar in search mode
            db.revealer.set_reveal_child(False)
            return

        if db.window.props.mobile_width and not db.action_bar.get_children():
            # mobile width: hide pathbar in header
            db.headerbar.props.show_pathbar = False
            # and put it in the bottom Action bar instead
            db.action_bar.add(self.unlocked_database.pathbar)
            db.action_bar.show()
        elif not db.window.props.mobile_width and db.action_bar.get_children():
            # Desktop width AND pathbar is in actionbar
            db.revealer.set_reveal_child(False)
            db.action_bar.remove(self.unlocked_database.pathbar)
            db.headerbar.props.show_pathbar = True

        # In mobile mode show the actionbar, unless we aborted in search
        if db.window.mobile_width and not db.revealer.props.reveal_child:
            db.revealer.set_reveal_child(True)

    def headerbar_selection_button(self):
        """Update the visibility of the headerbar buttons."""
        scrolled_page = self.unlocked_database.get_current_page()
        if self.unlocked_database.props.selection_mode:
            return

        if (self.unlocked_database.window.props.mobile_width
                and not scrolled_page.edit_page):
            self.unlocked_database.headerbar.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(True)
            self.unlocked_database.headerbar.builder.get_object("selection_button_revealer").set_reveal_child(False)
        else:
            self.unlocked_database.headerbar.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(False)

            if self.unlocked_database.window.props.mobile_width:
                return

            self.unlocked_database.headerbar.builder.get_object("selection_button_revealer").set_reveal_child(True)
