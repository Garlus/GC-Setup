"""Generic category page — renders items from catalog data with checkboxes."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


class CategoryPage(Gtk.ScrolledWindow):
    """A page showing items for one catalog category with checkboxes."""

    def __init__(self, category_data, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        self._category_id = category_data.get('id', '')
        self._check_rows = []  # List of (row, checkbox, item_data)

        self._pref_page = Adw.PreferencesPage()
        self._pref_page.set_margin_bottom(60)
        page = self._pref_page

        group = Adw.PreferencesGroup()
        group.set_title(category_data.get('name', ''))

        for item in category_data.get('items', []):
            row = Adw.ActionRow()
            row.set_title(item['name'])
            row.set_subtitle(item.get('description', ''))
            row.set_activatable(True)

            checkbox = Gtk.CheckButton()
            checkbox.set_valign(Gtk.Align.CENTER)
            row.add_prefix(checkbox)
            row.set_activatable_widget(checkbox)

            row._gc_item_data = item
            row._gc_checkbox = checkbox
            row._gc_is_installed = False

            self._check_rows.append((row, checkbox, item))
            group.add(row)

        page.add(group)
        self.set_child(page)

    @property
    def category_id(self):
        return self._category_id

    def get_check_rows(self):
        """Return list of (row, checkbox, item_data)."""
        return self._check_rows

    def get_selected_items(self):
        """Return list of item_data dicts for checked, non-installed items."""
        selected = []
        for row, checkbox, item_data in self._check_rows:
            if checkbox.get_active() and not row._gc_is_installed:
                selected.append(item_data)
        return selected

    def mark_installed(self, item_data):
        """Mark an item as already installed — check it and grey it out."""
        for row, checkbox, data in self._check_rows:
            if data is item_data:
                checkbox.set_active(True)
                checkbox.set_sensitive(False)
                row.set_sensitive(False)
                row._gc_is_installed = True
                row.set_subtitle(f"{data.get('description', '')} (installed)")
                break
