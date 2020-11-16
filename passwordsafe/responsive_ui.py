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
            if db.window.mobile_width and not db.action_bar.get_children():
                # mobile mode
                db.action_bar.add(self.unlocked_database.pathbar)
                db.action_bar.show()
                db.revealer.set_reveal_child(True)
            elif not db.window.mobile_width and not db.headerbar_box.get_children():
                # desktop mode
                db.headerbar_box.add(self.unlocked_database.pathbar)
                db.headerbar_box.show()
            return

        if db.props.search_active:
            # No pathbar in search mode
            db.revealer.set_reveal_child(False)
            return

        if db.window.mobile_width and not db.action_bar.get_children():
            # mobile width: hide pathbar in header
            db.headerbar_box.remove(self.unlocked_database.pathbar)
            db.headerbar_box.hide()
            # and put it in the bottom Action bar instead
            db.action_bar.add(self.unlocked_database.pathbar)
            db.action_bar.show()
        elif not db.window.mobile_width and db.action_bar.get_children():
            # Desktop width AND pathbar is in actionbar
            db.revealer.set_reveal_child(False)
            db.action_bar.remove(self.unlocked_database.pathbar)
            db.headerbar_box.add(self.unlocked_database.pathbar)
            db.headerbar_box.show()

        # In mobile mode show the actionbar, unless we aborted in search
        if db.window.mobile_width and not db.revealer.props.reveal_child:
            db.revealer.set_reveal_child(True)

    def headerbar_title(self) -> None:
        is_mobile = self.unlocked_database.window.mobile_width
        scrolled_page = self.unlocked_database.get_current_page()
        dbm = self.unlocked_database.database_manager
        cur_ele = self.unlocked_database.current_element
        title_label = self.unlocked_database.headerbar.builder.get_object("title_label")

        if is_mobile and not self.unlocked_database.props.selection_mode:
            if not scrolled_page.edit_page:
                # No edit page, show safe filename
                title = os.path.basename(dbm.database_path)
            elif dbm.check_is_group_object(cur_ele):
                # on group edit page, show entry title
                title = cur_ele.name or ""
            else:
                # on entry edit page, show entry title
                title = cur_ele.title or ""
            title_label.set_text(title)

        show = is_mobile and not self.unlocked_database.props.selection_mode
        title_label.set_visible(show)

    def headerbar_selection_button(self):
        """Update the visibility of the headerbar buttons."""
        scrolled_page = self.unlocked_database.get_current_page()
        if self.unlocked_database.props.selection_mode:
            return

        if (self.unlocked_database.window.mobile_width
                and not scrolled_page.edit_page):
            self.unlocked_database.headerbar.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(True)
            self.unlocked_database.headerbar.builder.get_object("selection_button_revealer").set_reveal_child(False)
        else:
            self.unlocked_database.headerbar.builder.get_object("pathbar_button_selection_revealer").set_reveal_child(False)

            if self.unlocked_database.window.mobile_width:
                return

            self.unlocked_database.headerbar.builder.get_object("selection_button_revealer").set_reveal_child(True)
