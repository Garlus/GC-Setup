"""Misc page — system-level items with copyable install commands."""

import json
import os
import subprocess

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk


def _get_data_path(filename):
    """Resolve path to bundled data file."""
    pkg = os.environ.get('GC_SETUP_PKGDATADIR', '')
    if pkg:
        path = os.path.join(pkg, 'data', filename)
        if os.path.exists(path):
            return path
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, '..', 'data', filename)


def _detect_package_manager():
    """Detect the system package manager."""
    checks = [
        ('apt', '/usr/bin/apt'),
        ('dnf', '/usr/bin/dnf'),
        ('pacman', '/usr/bin/pacman'),
        ('zypper', '/usr/bin/zypper'),
    ]
    for name, path in checks:
        if os.path.exists(path):
            return name
    return None


class MiscPage(Gtk.ScrolledWindow):
    """Page showing system-level tweaks with copyable commands."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)

        self._items = []
        self._pkg_manager = _detect_package_manager()

        page = Adw.PreferencesPage()
        page.set_title('Misc')
        page.set_icon_name('preferences-other-symbolic')

        # Info banner
        info_group = Adw.PreferencesGroup()
        info_group.set_description(
            'These items require system package manager access and cannot be '
            'installed from within the Flatpak sandbox. Check the items you '
            'want, then click "Apply" to copy the combined command '
            'to your clipboard. Paste it into a terminal to install.'
        )
        if self._pkg_manager:
            info_group.set_title(f'System Tweaks (detected: {self._pkg_manager})')
        else:
            info_group.set_title('System Tweaks')
        page.add(info_group)

        # Items
        group = Adw.PreferencesGroup()
        data = self._load_data()

        for item in data.get('items', []):
            row = Adw.ActionRow()
            row.set_title(item['name'])
            row.set_subtitle(item.get('description', ''))
            row.set_activatable(True)

            checkbox = Gtk.CheckButton()
            checkbox.set_valign(Gtk.Align.CENTER)
            row.add_prefix(checkbox)
            row.set_activatable_widget(checkbox)

            row._gc_misc_data = item
            row._gc_checkbox = checkbox
            self._items.append((row, checkbox, item))
            group.add(row)

        page.add(group)

        # === Font Sharpness Section ===
        font_group = Adw.PreferencesGroup()
        font_group.set_title('Font Rendering')
        font_group.set_description(
            'Apply macOS-like font rendering: subpixel antialiasing (RGBA) '
            'with slight hinting for crisp, sharp text.'
        )

        font_row = Adw.ActionRow()
        font_row.set_title('Sharp Font Rendering')
        font_row.set_subtitle('Sets antialiasing to RGBA and hinting to slight')

        self._font_apply_btn = Gtk.Button(label='Apply')
        self._font_apply_btn.set_valign(Gtk.Align.CENTER)
        self._font_apply_btn.set_css_classes(['suggested-action', 'pill'])
        self._font_apply_btn.connect('clicked', self._on_apply_font_sharpness)
        font_row.add_suffix(self._font_apply_btn)

        self._font_status_icon = Gtk.Image()
        self._font_status_icon.set_valign(Gtk.Align.CENTER)
        self._font_status_icon.set_visible(False)
        font_row.add_suffix(self._font_status_icon)

        font_group.add(font_row)

        font_revert_row = Adw.ActionRow()
        font_revert_row.set_title('Revert to Default')
        font_revert_row.set_subtitle('Reset antialiasing to grayscale and hinting to medium')

        self._font_revert_btn = Gtk.Button(label='Revert')
        self._font_revert_btn.set_valign(Gtk.Align.CENTER)
        self._font_revert_btn.set_css_classes(['flat', 'pill'])
        self._font_revert_btn.connect('clicked', self._on_revert_font_sharpness)
        font_revert_row.add_suffix(self._font_revert_btn)

        self._font_revert_icon = Gtk.Image()
        self._font_revert_icon.set_valign(Gtk.Align.CENTER)
        self._font_revert_icon.set_visible(False)
        font_revert_row.add_suffix(self._font_revert_icon)

        font_group.add(font_revert_row)

        page.add(font_group)

        self.set_child(page)

    def _load_data(self):
        path = _get_data_path('misc.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f'Warning: Could not load misc.json: {e}')
            return {'items': []}

    def get_selected_items(self):
        """Return list of misc item dicts for checked items.

        Each item gets 'install_type': 'misc' and 'resolved_command' set
        to the command for the detected package manager.
        """
        selected = []
        for row, checkbox, item_data in self._items:
            if checkbox.get_active():
                entry = dict(item_data)
                entry['install_type'] = 'misc'
                # Resolve command for detected package manager
                commands = entry.get('commands', {})
                if 'all' in commands:
                    entry['resolved_command'] = commands['all']
                elif self._pkg_manager and self._pkg_manager in commands:
                    entry['resolved_command'] = commands[self._pkg_manager]
                else:
                    # Fallback: pick first available
                    entry['resolved_command'] = next(iter(commands.values()), '')
                selected.append(entry)
        return selected

    def get_package_manager(self):
        return self._pkg_manager

    def _run_gsettings(self, schema, key, value):
        """Run a gsettings command, using flatpak-spawn if in sandbox."""
        try:
            cmd = ['gsettings', 'set', schema, key, value]
            if os.path.exists('/.flatpak-info'):
                cmd = ['flatpak-spawn', '--host'] + cmd
            result = subprocess.run(
                cmd, capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _on_apply_font_sharpness(self, _button):
        """Apply macOS-like font rendering settings."""
        schema = 'org.gnome.desktop.interface'
        ok1 = self._run_gsettings(schema, 'font-antialiasing', 'rgba')
        ok2 = self._run_gsettings(schema, 'font-hinting', 'slight')

        if ok1 and ok2:
            self._font_status_icon.set_from_icon_name('emblem-ok-symbolic')
            self._font_status_icon.set_css_classes(['success'])
            self._font_apply_btn.set_label('Applied')
            self._font_apply_btn.set_sensitive(False)
            self._font_apply_btn.set_css_classes(['flat', 'pill'])
            # Reset revert button in case it was used before
            self._font_revert_btn.set_label('Revert')
            self._font_revert_btn.set_sensitive(True)
            self._font_revert_btn.set_css_classes(['flat', 'pill'])
            self._font_revert_icon.set_visible(False)
        else:
            self._font_status_icon.set_from_icon_name('dialog-error-symbolic')
            self._font_status_icon.set_css_classes(['error'])

        self._font_status_icon.set_visible(True)

    def _on_revert_font_sharpness(self, _button):
        """Revert font rendering to GNOME defaults."""
        schema = 'org.gnome.desktop.interface'
        ok1 = self._run_gsettings(schema, 'font-antialiasing', 'grayscale')
        ok2 = self._run_gsettings(schema, 'font-hinting', 'medium')

        if ok1 and ok2:
            self._font_revert_icon.set_from_icon_name('emblem-ok-symbolic')
            self._font_revert_icon.set_css_classes(['success'])
            self._font_revert_btn.set_label('Reverted')
            self._font_revert_btn.set_sensitive(False)
            # Reset apply button
            self._font_apply_btn.set_label('Apply')
            self._font_apply_btn.set_sensitive(True)
            self._font_apply_btn.set_css_classes(['suggested-action', 'pill'])
            self._font_status_icon.set_visible(False)
        else:
            self._font_revert_icon.set_from_icon_name('dialog-error-symbolic')
            self._font_revert_icon.set_css_classes(['error'])

        self._font_revert_icon.set_visible(True)
