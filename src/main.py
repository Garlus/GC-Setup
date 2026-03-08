"""GC-Setup main application."""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

from src.window import GCSetupWindow

APP_ID = 'io.github.gcsetup.GCSetup'


class GCSetupApplication(Adw.Application):
    """The main GC-Setup application."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = GCSetupWindow(application=self)
        win.present()

    def do_startup(self):
        Adw.Application.do_startup(self)

        # Create app actions
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', lambda *_: self.quit())
        self.add_action(action)
        self.set_accels_for_action('app.quit', ['<primary>q'])

        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self._on_about)
        self.add_action(action)

    def _on_about(self, _action, _param):
        about = Adw.AboutDialog(
            application_name='GC-Setup',
            application_icon=APP_ID,
            version='1.0.0',
            developer_name='GC-Setup Team',
            license_type=Gtk.License.GPL_3_0,
            website='https://github.com/gcsetup/gc-setup',
            issue_url='https://github.com/gcsetup/gc-setup/issues',
            developers=['GC-Setup Team'],
            copyright='Copyright 2026 GC-Setup Team',
        )
        about.present(self.props.active_window)


def main():
    app = GCSetupApplication()
    return app.run(sys.argv)
