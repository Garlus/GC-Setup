"""Apps page — Flatpak apps grouped by category with checkboxes."""

import json
import os

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


def _get_data_path(filename):
    """Resolve path to bundled data file."""
    # When installed via meson, data lives next to the src package
    pkg = os.environ.get('GC_SETUP_PKGDATADIR', '')
    if pkg:
        path = os.path.join(pkg, 'data', filename)
        if os.path.exists(path):
            return path
    # Fallback for development
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, '..', 'data', filename)


class AppsPage(Gtk.ScrolledWindow):
    """Page showing Flatpak apps grouped by category."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        self._check_rows = []  # List of (row, checkbox, app_data) tuples

        page = Adw.PreferencesPage()
        page.set_title('Apps')
        page.set_icon_name('applications-symbolic')

        # Load data
        data = self._load_data()

        for category in data.get('categories', []):
            group = Adw.PreferencesGroup()
            group.set_title(category['name'])
            if 'icon' in category:
                group.set_description(f"Select {category['name'].lower()} to install")

            for app in category.get('apps', []):
                row = Adw.ActionRow()
                row.set_title(app['name'])
                row.set_subtitle(app.get('description', ''))
                row.set_activatable(True)

                checkbox = Gtk.CheckButton()
                checkbox.set_valign(Gtk.Align.CENTER)
                row.add_prefix(checkbox)
                row.set_activatable_widget(checkbox)

                row._gc_app_data = app
                row._gc_checkbox = checkbox
                row._gc_is_installed = False

                self._check_rows.append((row, checkbox, app))
                group.add(row)

            page.add(group)

        self.set_child(page)

    def _load_data(self):
        path = _get_data_path('apps.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f'Warning: Could not load apps.json: {e}')
            return {'categories': []}

    def get_check_rows(self):
        """Return list of (row, checkbox, app_data) for detection/install."""
        return self._check_rows

    def get_selected_items(self):
        """Return list of app_data dicts for all checked, non-installed items."""
        selected = []
        for row, checkbox, app_data in self._check_rows:
            if checkbox.get_active() and not row._gc_is_installed:
                selected.append(app_data)
        return selected

    def mark_installed(self, app_data):
        """Mark an app as already installed — check it and make insensitive."""
        for row, checkbox, data in self._check_rows:
            if data is app_data or data.get('flatpak_id') == app_data.get('flatpak_id'):
                checkbox.set_active(True)
                checkbox.set_sensitive(False)
                row.set_sensitive(False)
                row._gc_is_installed = True
                row.set_subtitle(f"{data.get('description', '')} (installed)")
                break
