"""Extensions page — GNOME Shell extensions with checkboxes."""

import json
import os

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw


def _get_data_path(filename):
    """Resolve path to bundled data file."""
    pkg = os.environ.get('GC_SETUP_PKGDATADIR', '')
    if pkg:
        path = os.path.join(pkg, 'data', filename)
        if os.path.exists(path):
            return path
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, '..', 'data', filename)


class ExtensionsPage(Gtk.ScrolledWindow):
    """Page showing GNOME Shell extensions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        self._check_rows = []

        page = Adw.PreferencesPage()
        page.set_title('Extensions')
        page.set_icon_name('application-x-addon-symbolic')

        group = Adw.PreferencesGroup()
        group.set_title('GNOME Shell Extensions')
        group.set_description(
            'Extensions are downloaded from extensions.gnome.org and installed '
            'via the gnome-extensions CLI'
        )

        # Load data
        data = self._load_data()

        for ext in data.get('extensions', []):
            row = Adw.ActionRow()
            row.set_title(ext['name'])
            row.set_subtitle(ext.get('description', ''))
            row.set_activatable(True)

            checkbox = Gtk.CheckButton()
            checkbox.set_valign(Gtk.Align.CENTER)
            row.add_prefix(checkbox)
            row.set_activatable_widget(checkbox)

            row._gc_ext_data = ext
            row._gc_checkbox = checkbox
            row._gc_is_installed = False

            self._check_rows.append((row, checkbox, ext))
            group.add(row)

        page.add(group)
        self.set_child(page)

    def _load_data(self):
        path = _get_data_path('extensions.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f'Warning: Could not load extensions.json: {e}')
            return {'extensions': []}

    def get_check_rows(self):
        """Return list of (row, checkbox, ext_data)."""
        return self._check_rows

    def get_selected_items(self):
        """Return list of ext_data dicts for checked, non-installed items."""
        selected = []
        for row, checkbox, ext_data in self._check_rows:
            if checkbox.get_active() and not row._gc_is_installed:
                item = dict(ext_data)
                item['install_type'] = 'extension'
                selected.append(item)
        return selected

    def mark_installed(self, ext_data):
        """Mark an extension as already installed."""
        for row, checkbox, data in self._check_rows:
            if data is ext_data or data.get('uuid') == ext_data.get('uuid'):
                checkbox.set_active(True)
                checkbox.set_sensitive(False)
                row.set_sensitive(False)
                row._gc_is_installed = True
                row.set_subtitle(f"{data.get('description', '')} (installed)")
                break
