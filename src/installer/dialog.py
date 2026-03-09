"""Progress dialog — AdwDialog with spinner for install / remove operations."""

import threading

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gdk

from src.installer.flatpak import install_flatpak_on_host, uninstall_flatpak_on_host
from src.installer.extensions import install_extension, uninstall_extension
from src.installer.appimage import install_helium, uninstall_helium
from src.installer.native import (
    install_native, uninstall_native, resolve_system_command,
)


class ProgressDialog(Adw.Dialog):
    """Modal dialog that shows a spinner while installing / removing items.

    System-method items are collected and shown as a single copyable command
    after all other work is done.
    """

    def __init__(self, items, mode='install', on_complete_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.set_title('Applying\u2026' if mode == 'install' else 'Removing\u2026')
        self.set_content_width(380)
        self.set_content_height(260)
        self.set_can_close(False)

        self._items = items
        self._mode = mode          # 'install' | 'remove'
        self._on_complete_cb = on_complete_cb
        self._system_items = []
        self._work_items = []
        self._errors = []

        # Separate system items (copy-paste only) from actionable items
        for item in self._items:
            method = item.get('install', {}).get('method', '')
            if method == 'system':
                self._system_items.append(item)
            else:
                self._work_items.append(item)

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)
        toolbar.add_top_bar(header)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # ── Spinner page ──
        spinner_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
        )
        spinner_box.set_vexpand(True)
        spinner = Adw.Spinner()
        spinner.set_size_request(48, 48)
        spinner_box.append(spinner)
        self._stack.add_named(spinner_box, 'working')

        # ── Done page ──
        done_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            valign=Gtk.Align.CENTER,
            halign=Gtk.Align.CENTER,
        )
        done_box.set_vexpand(True)
        done_box.set_margin_start(24)
        done_box.set_margin_end(24)

        self._done_icon = Gtk.Image()
        self._done_icon.set_pixel_size(48)
        done_box.append(self._done_icon)

        self._done_label = Gtk.Label()
        self._done_label.set_wrap(True)
        self._done_label.set_justify(Gtk.Justification.CENTER)
        done_box.append(self._done_label)

        # System-items section (hidden unless needed)
        self._system_group = Adw.PreferencesGroup()
        self._system_group.set_visible(False)
        done_box.append(self._system_group)

        close_btn = Gtk.Button(label='Close')
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.set_css_classes(['pill'])
        close_btn.connect('clicked', lambda *_: self.close())
        done_box.append(close_btn)

        self._stack.add_named(done_box, 'done')

        toolbar.set_content(self._stack)
        self.set_child(toolbar)
        self._stack.set_visible_child_name('working')

    # ── Execution ─────────────────────────────────────────────────

    def start(self):
        """Kick off work in a background thread."""
        if not self._work_items and not self._system_items:
            self._finish()
            return
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        for item in self._work_items:
            if self._mode == 'install':
                ok, msg = self._do_install(item)
            else:
                ok, msg = self._do_uninstall(item)
            if not ok:
                self._errors.append((item.get('name', '?'), msg))

        GLib.idle_add(self._finish)

    # ── Install dispatch ──────────────────────────────────────────

    def _do_install(self, item):
        info = item.get('install', {})
        method = info.get('method', '')

        if method == 'native':
            return install_native(item)
        elif method == 'flatpak':
            fid = info.get('flatpak_id', '')
            return (False, 'No flatpak_id') if not fid else install_flatpak_on_host(fid)
        elif method == 'extension':
            eid, uuid = info.get('ext_id', 0), info.get('uuid', '')
            return (False, 'Missing ext_id/uuid') if not eid or not uuid else install_extension(eid, uuid)
        elif method == 'appimage':
            return install_helium()
        return False, f'Unknown method: {method}'

    # ── Uninstall dispatch ────────────────────────────────────────

    def _do_uninstall(self, item):
        info = item.get('install', {})
        method = info.get('method', '')
        detect = item.get('detect', {})

        if method == 'native':
            return uninstall_native(item)
        elif method == 'flatpak':
            fid = info.get('flatpak_id', '')
            return (False, 'No flatpak_id') if not fid else uninstall_flatpak_on_host(fid)
        elif method == 'extension':
            uuid = info.get('uuid', '') or detect.get('extension_uuid', '')
            return (False, 'No uuid') if not uuid else uninstall_extension(uuid)
        elif method == 'appimage':
            return uninstall_helium()
        return False, f'Unknown method: {method}'

    # ── Completion ────────────────────────────────────────────────

    def _finish(self):
        self.set_can_close(True)

        if self._errors:
            self._done_icon.set_from_icon_name('dialog-warning-symbolic')
            self._done_icon.add_css_class('warning')
            names = ', '.join(n for n, _ in self._errors)
            self._done_label.set_label(f'Failed: {names}')
        else:
            self._done_icon.set_from_icon_name('object-select-symbolic')
            self._done_icon.add_css_class('success')
            self._done_label.set_label('Done')

        # Show system-items copy section when applicable
        if self._system_items:
            self._build_system_section()

        self._stack.set_visible_child_name('done')
        self.set_title('Done')

        if self._on_complete_cb:
            self._on_complete_cb()

    def _build_system_section(self):
        """Build the copy-paste row for system-method items."""
        self._system_group.set_title('System Packages')
        self._system_group.set_description(
            'Copy and paste this into a terminal.'
        )

        names, commands = [], []
        for item in self._system_items:
            names.append(item.get('name', '?'))
            cmd = resolve_system_command(item)
            if cmd:
                commands.append(cmd)

        if not commands:
            return

        combined = ' && '.join(commands)
        row = Adw.ActionRow()
        row.set_title(', '.join(names))
        row.set_subtitle(GLib.markup_escape_text(combined))
        row.set_subtitle_lines(3)

        copy_btn = Gtk.Button(icon_name='edit-copy-symbolic')
        copy_btn.set_valign(Gtk.Align.CENTER)
        copy_btn.set_css_classes(['flat'])
        copy_btn.set_tooltip_text('Copy command')
        copy_btn.connect('clicked', self._on_copy, combined, copy_btn)
        row.add_suffix(copy_btn)

        self._system_group.add(row)
        self._system_group.set_visible(True)

    @staticmethod
    def _on_copy(_btn, command, btn_ref):
        display = Gdk.Display.get_default()
        if display:
            display.get_clipboard().set(command)
        btn_ref.set_icon_name('object-select-symbolic')
        btn_ref.set_sensitive(False)
