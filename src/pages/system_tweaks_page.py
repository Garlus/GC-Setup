"""System tweaks page — extends CategoryPage with font rendering controls."""

import os
import subprocess

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw

from src.pages.category_page import CategoryPage


class SystemTweaksPage(CategoryPage):
    """System Tweaks page with additional font rendering section."""

    def __init__(self, category_data, **kwargs):
        super().__init__(category_data, **kwargs)

        # Append font rendering group to the existing page
        page = self._pref_page  # Set by CategoryPage.__init__

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

        self._font_revert_btn = Gtk.Button.new_from_icon_name('edit-undo-symbolic')
        self._font_revert_btn.set_valign(Gtk.Align.CENTER)
        self._font_revert_btn.set_tooltip_text('Revert to default')
        self._font_revert_btn.set_css_classes(['flat', 'circular'])
        self._font_revert_btn.set_visible(False)
        self._font_revert_btn.connect('clicked', self._on_revert_font_sharpness)
        font_row.add_suffix(self._font_revert_btn)

        self._font_status_icon = Gtk.Image()
        self._font_status_icon.set_valign(Gtk.Align.CENTER)
        self._font_status_icon.set_visible(False)
        font_row.add_suffix(self._font_status_icon)

        font_group.add(font_row)
        page.add(font_group)

    def _run_gsettings(self, schema, key, value):
        """Run a gsettings command, using flatpak-spawn if in sandbox."""
        try:
            cmd = ['gsettings', 'set', schema, key, value]
            if os.path.exists('/.flatpak-info'):
                cmd = ['flatpak-spawn', '--host'] + cmd
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _on_apply_font_sharpness(self, _button):
        """Apply macOS-like font rendering settings."""
        schema = 'org.gnome.desktop.interface'
        ok1 = self._run_gsettings(schema, 'font-antialiasing', 'rgba')
        ok2 = self._run_gsettings(schema, 'font-hinting', 'slight')

        if ok1 and ok2:
            self._font_status_icon.set_from_icon_name('object-select-symbolic')
            self._font_status_icon.remove_css_class('error')
            self._font_status_icon.add_css_class('success')
            self._font_apply_btn.set_visible(False)
            self._font_revert_btn.set_visible(True)
        else:
            self._font_status_icon.set_from_icon_name('dialog-error-symbolic')
            self._font_status_icon.remove_css_class('success')
            self._font_status_icon.add_css_class('error')

        self._font_status_icon.set_visible(True)

    def _on_revert_font_sharpness(self, _button):
        """Revert font rendering to GNOME defaults."""
        schema = 'org.gnome.desktop.interface'
        ok1 = self._run_gsettings(schema, 'font-antialiasing', 'grayscale')
        ok2 = self._run_gsettings(schema, 'font-hinting', 'medium')

        if ok1 and ok2:
            self._font_revert_btn.set_visible(False)
            self._font_status_icon.set_visible(False)
            self._font_apply_btn.set_visible(True)
        else:
            self._font_status_icon.set_from_icon_name('dialog-error-symbolic')
            self._font_status_icon.remove_css_class('success')
            self._font_status_icon.add_css_class('error')
            self._font_status_icon.set_visible(True)
