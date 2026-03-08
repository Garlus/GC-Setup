"""Progress window — shows installation progress as items are processed."""

import threading

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk

from src.installer.flatpak import install_flatpak_on_host
from src.installer.extensions import install_extension
from src.installer.appimage import install_helium


class ProgressWindow(Adw.Window):
    """Window that shows installation progress for all selected items."""

    def __init__(self, items, parent_window, **kwargs):
        super().__init__(**kwargs)

        self._items = items
        self._parent_window = parent_window
        self._rows = {}
        self._completed = 0
        self._total = 0
        self._misc_items = []
        self._installable_items = []

        self.set_title('Applying Changes')
        self.set_default_size(460, 400)
        self.set_transient_for(parent_window)
        self.set_modal(True)

        self._build_ui()
        self._start_processing()

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Scrolled content area
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=0
        )
        self._content_box.set_margin_top(12)
        self._content_box.set_margin_bottom(12)
        self._content_box.set_margin_start(12)
        self._content_box.set_margin_end(12)

        # Separate misc from installable items
        for item in self._items:
            if item.get('install_type') == 'misc':
                self._misc_items.append(item)
            else:
                self._installable_items.append(item)

        self._total = len(self._installable_items)

        # Installable items group (rows added dynamically as installs start)
        if self._installable_items:
            self._install_group = Adw.PreferencesGroup()
            self._content_box.append(self._install_group)

        # Misc items section — show copy buttons with escaped text
        if self._misc_items:
            misc_group = Adw.PreferencesGroup()
            misc_group.set_title('System Packages')
            misc_group.set_description(
                'Copy the command and paste it into a terminal.'
            )

            for item in self._misc_items:
                name = item.get('name', 'Unknown')
                cmd = item.get('resolved_command', '')

                row = Adw.ActionRow()
                row.set_title(name)
                # Escape markup-sensitive characters in the command
                safe_cmd = GLib.markup_escape_text(cmd)
                if len(safe_cmd) > 80:
                    safe_cmd = GLib.markup_escape_text(cmd[:77]) + '...'
                row.set_subtitle(safe_cmd)
                row.set_subtitle_lines(1)

                copy_btn = Gtk.Button(icon_name='edit-copy-symbolic')
                copy_btn.set_valign(Gtk.Align.CENTER)
                copy_btn.set_tooltip_text('Copy command')
                copy_btn.set_css_classes(['flat'])
                copy_btn.connect('clicked', self._on_copy_command, cmd, row)
                row.add_suffix(copy_btn)

                misc_group.add(row)

            # Copy All button
            if len(self._misc_items) > 1:
                combined = ' && '.join(
                    item.get('resolved_command', '')
                    for item in self._misc_items
                    if item.get('resolved_command')
                )
                copy_all_row = Adw.ActionRow()
                copy_all_row.set_title('Copy All Commands')
                copy_all_row.set_subtitle('Combined command for all selected packages')

                copy_all_btn = Gtk.Button(icon_name='edit-copy-symbolic')
                copy_all_btn.set_valign(Gtk.Align.CENTER)
                copy_all_btn.set_css_classes(['flat'])
                copy_all_btn.set_tooltip_text('Copy combined command')
                copy_all_btn.connect(
                    'clicked', self._on_copy_command, combined, copy_all_row
                )
                copy_all_row.add_suffix(copy_all_btn)
                misc_group.add(copy_all_row)

            self._content_box.append(misc_group)

        # Empty state if nothing to do
        if not self._installable_items and not self._misc_items:
            label = Gtk.Label(label='Nothing to do.')
            label.set_margin_top(24)
            self._content_box.append(label)

        scroll.set_child(self._content_box)
        toolbar_view.set_content(scroll)
        self.set_content(toolbar_view)

    def _start_processing(self):
        """Start installing all installable items sequentially in a thread."""
        if not self._installable_items:
            return

        thread = threading.Thread(
            target=self._install_all, daemon=True
        )
        thread.start()

    def _install_all(self):
        """Install items one at a time (runs in background thread)."""
        for item in self._installable_items:
            name = item.get('name', 'Unknown')

            # Show this item with a spinner
            GLib.idle_add(self._show_item_installing, name)

            # Do the actual install
            success, message = self._do_install(item)

            # Update the row to show result
            GLib.idle_add(self._show_item_done, name, success, message)

        GLib.idle_add(self._on_all_complete)

    def _do_install(self, item):
        """Install a single item. Returns (success, message)."""
        install_type = item.get('install_type', '')

        if install_type == 'flatpak':
            flatpak_id = item.get('flatpak_id', '')
            return install_flatpak_on_host(flatpak_id)
        elif install_type == 'extension':
            ext_id = item.get('ext_id', 0)
            uuid = item.get('uuid', '')
            return install_extension(ext_id, uuid)
        elif install_type == 'appimage':
            return install_helium()
        else:
            return False, f'Unknown install type: {install_type}'

    def _show_item_installing(self, name):
        """Add a row with a spinner for this item."""
        row = Adw.ActionRow()
        row.set_title(name)

        spinner = Gtk.Spinner()
        spinner.set_valign(Gtk.Align.CENTER)
        spinner.set_spinning(True)
        row.add_suffix(spinner)

        self._rows[name] = (row, spinner)
        self._install_group.add(row)

    def _show_item_done(self, name, success, message):
        """Update the row to show success or failure, replacing the spinner."""
        if name not in self._rows:
            return

        row, spinner = self._rows[name]
        spinner.set_spinning(False)
        spinner.set_visible(False)

        icon = Gtk.Image()
        icon.set_valign(Gtk.Align.CENTER)

        if success:
            icon.set_from_icon_name('emblem-ok-symbolic')
            icon.set_css_classes(['success'])
        else:
            icon.set_from_icon_name('dialog-error-symbolic')
            icon.set_css_classes(['error'])
            short_msg = message[:80] if len(message) > 80 else message
            safe_msg = GLib.markup_escape_text(short_msg)
            row.set_subtitle(safe_msg)

        row.add_suffix(icon)

        self._completed += 1

    def _on_all_complete(self):
        """Called when all installs are done."""
        self.set_title('Changes Applied')

    def _on_copy_command(self, button, command, row):
        """Copy a command to clipboard."""
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.set(command)

        button.set_icon_name('emblem-ok-symbolic')
        button.set_sensitive(False)
