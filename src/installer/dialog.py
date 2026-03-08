"""Progress sheet — builds the bottom-sheet content for installation progress."""

import threading

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk

from src.installer.flatpak import install_flatpak_on_host
from src.installer.extensions import install_extension
from src.installer.appimage import install_helium
from src.installer.native import install_native, resolve_system_command


class ProgressSheet:
    """Manages the sheet content and install logic for the bottom sheet.

    This is not a widget itself — it builds and populates a scrollable
    widget that is set as the AdwBottomSheet's sheet, and drives the
    sequential install process.
    """

    def __init__(self, items, on_complete_cb=None):
        self._items = items
        self._on_complete_cb = on_complete_cb
        self._rows = {}
        self._completed = 0
        self._total = 0
        self._system_items = []
        self._installable_items = []
        self._installing = False

        # Separate system (copyable commands) from installable items
        for item in self._items:
            method = item.get('install', {}).get('method', '')
            if method == 'system':
                self._system_items.append(item)
            else:
                self._installable_items.append(item)

        self._total = len(self._installable_items)

        # Build the widget tree
        self._widget = self._build_ui()

    @property
    def widget(self):
        """The top-level widget to set as the sheet content."""
        return self._widget

    @property
    def installing(self):
        """Whether installs are currently in progress."""
        return self._installing

    def _build_ui(self):
        """Build the sheet content: a toolbar view with header + scrollable list."""
        toolbar_view = Adw.ToolbarView()

        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)

        self._title_label = Gtk.Label(label='Applying Changes')
        self._title_label.set_css_classes(['title'])
        header.set_title_widget(self._title_label)

        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_propagate_natural_height(True)

        self._content_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=0
        )
        self._content_box.set_margin_top(12)
        self._content_box.set_margin_bottom(12)
        self._content_box.set_margin_start(12)
        self._content_box.set_margin_end(12)

        # Installable items group (rows added dynamically as installs start)
        if self._installable_items:
            self._install_group = Adw.PreferencesGroup()
            self._content_box.append(self._install_group)

        # System items section — single combined command
        if self._system_items:
            misc_group = Adw.PreferencesGroup()
            misc_group.set_title('System Packages')
            misc_group.set_description(
                'Copy the command below and paste it into a terminal.'
            )

            # Resolve the correct command for each system item
            names = []
            commands = []
            for item in self._system_items:
                names.append(item.get('name', 'Unknown'))
                cmd = resolve_system_command(item)
                if cmd:
                    commands.append(cmd)

            combined = ' && '.join(commands)

            row = Adw.ActionRow()
            row.set_title(', '.join(names))
            safe_cmd = GLib.markup_escape_text(combined)
            row.set_subtitle(safe_cmd)
            row.set_subtitle_lines(3)

            copy_btn = Gtk.Button(icon_name='edit-copy-symbolic')
            copy_btn.set_valign(Gtk.Align.CENTER)
            copy_btn.set_tooltip_text('Copy command')
            copy_btn.set_css_classes(['flat'])
            copy_btn.connect('clicked', self._on_copy_command, combined, row)
            row.add_suffix(copy_btn)

            misc_group.add(row)
            self._content_box.append(misc_group)

        # Empty state
        if not self._installable_items and not self._system_items:
            label = Gtk.Label(label='Nothing to do.')
            label.set_margin_top(24)
            self._content_box.append(label)

        scroll.set_child(self._content_box)
        toolbar_view.set_content(scroll)
        return toolbar_view

    def start(self):
        """Start installing all installable items sequentially in a thread."""
        if not self._installable_items:
            # Only system items — already shown, mark complete immediately
            self._on_all_complete()
            return

        self._installing = True
        thread = threading.Thread(target=self._install_all, daemon=True)
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
        """Install a single item. Returns (success, message).

        Dispatches based on item['install']['method'].
        """
        install_info = item.get('install', {})
        method = install_info.get('method', '')

        if method == 'native':
            return install_native(item)

        elif method == 'flatpak':
            flatpak_id = install_info.get('flatpak_id', '')
            if not flatpak_id:
                return False, 'No flatpak_id specified'
            return install_flatpak_on_host(flatpak_id)

        elif method == 'extension':
            ext_id = install_info.get('ext_id', 0)
            uuid = install_info.get('uuid', '')
            if not ext_id or not uuid:
                return False, 'Missing ext_id or uuid'
            return install_extension(ext_id, uuid)

        elif method == 'appimage':
            return install_helium()

        else:
            return False, f'Unknown install method: {method}'

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
        self._installing = False
        self._title_label.set_label('Changes Applied')

        if self._on_complete_cb:
            self._on_complete_cb()

    def _on_copy_command(self, button, command, row):
        """Copy a command to clipboard."""
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.set(command)

        button.set_icon_name('emblem-ok-symbolic')
        button.set_sensitive(False)
