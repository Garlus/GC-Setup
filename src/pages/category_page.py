"""Generic category page — renders items from catalog data with checkboxes."""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk


# One-time CSS provider for dimming installed rows
_css_loaded = False


def _ensure_css():
    global _css_loaded
    if _css_loaded:
        return
    _css_loaded = True
    provider = Gtk.CssProvider()
    provider.load_from_string(
        'row.installed .title, row.installed .subtitle { opacity: 0.55; }'
    )
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class CategoryPage(Gtk.ScrolledWindow):
    """A page showing items for one catalog category with checkboxes."""

    def __init__(self, category_data, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        _ensure_css()

        self._category_id = category_data.get('id', '')
        self._check_rows = []   # (row, checkbox, item_data) — selectable items

        self._pref_page = Adw.PreferencesPage()
        self._pref_page.set_margin_bottom(60)

        group = Adw.PreferencesGroup()
        group.set_title(category_data.get('name', ''))

        for item in category_data.get('items', []):
            if item.get('runnable', False):
                self._add_runnable_row(group, item)
            else:
                self._add_checkbox_row(group, item)

        self._pref_page.add(group)
        self.set_child(self._pref_page)

    # ── Row builders ──────────────────────────────────────────────

    def _add_checkbox_row(self, group, item):
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

    def _add_runnable_row(self, group, item):
        """Add a row with a run-arrow button instead of a checkbox."""
        row = Adw.ActionRow()
        row.set_title(item['name'])
        row.set_subtitle(item.get('description', ''))

        btn = Gtk.Button.new_from_icon_name('media-playback-start-symbolic')
        btn.set_valign(Gtk.Align.CENTER)
        btn.set_css_classes(['flat', 'circular'])
        btn.set_tooltip_text('Copy command to clipboard')
        btn.connect('clicked', self._on_run_clicked, item, btn)
        row.add_suffix(btn)
        row.set_activatable_widget(btn)

        group.add(row)

    # ── Runnable item handler ─────────────────────────────────────

    def _on_run_clicked(self, _button, item, btn_ref):
        """Resolve the system command, copy to clipboard, show toast."""
        from src.installer.native import resolve_system_command

        cmd = resolve_system_command(item)
        if not cmd:
            cmd = '# No command available for your package manager'

        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.set(cmd)

        # Visual feedback — swap icon briefly
        btn_ref.set_icon_name('object-select-symbolic')
        btn_ref.set_sensitive(False)
        GLib.timeout_add(2000, self._reset_run_button, btn_ref)

        # Toast via window overlay
        window = self.get_root()
        if hasattr(window, '_toast_overlay'):
            toast = Adw.Toast.new('Command copied \u2014 paste in your terminal')
            toast.set_timeout(3)
            window._toast_overlay.add_toast(toast)

    @staticmethod
    def _reset_run_button(btn):
        btn.set_icon_name('media-playback-start-symbolic')
        btn.set_sensitive(True)
        return False

    # ── Public API ────────────────────────────────────────────────

    @property
    def category_id(self):
        return self._category_id

    def get_check_rows(self):
        """Return list of (row, checkbox, item_data)."""
        return self._check_rows

    def get_selected_items(self):
        """Return item dicts for checked, non-installed items (for Apply)."""
        return [
            item for row, cb, item in self._check_rows
            if cb.get_active() and not row._gc_is_installed
        ]

    def get_selected_installed_items(self):
        """Return item dicts for checked, already-installed items (for Remove)."""
        return [
            item for row, cb, item in self._check_rows
            if cb.get_active() and row._gc_is_installed
        ]

    def mark_installed(self, item_data):
        """Mark an item as installed — dim the row text, keep checkbox normal."""
        for row, checkbox, data in self._check_rows:
            if data is item_data:
                row._gc_is_installed = True
                row.add_css_class('installed')
                desc = data.get('description', '')
                row.set_subtitle(f'{desc} (installed)')
                break

    def unmark_installed(self, item_data):
        """Revert an item to non-installed state."""
        for row, checkbox, data in self._check_rows:
            if data is item_data:
                row._gc_is_installed = False
                row.remove_css_class('installed')
                checkbox.set_active(False)
                row.set_subtitle(data.get('description', ''))
                break

    def clear_selection(self):
        """Uncheck all checkboxes."""
        for _row, checkbox, _item in self._check_rows:
            checkbox.set_active(False)
