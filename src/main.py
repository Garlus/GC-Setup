"""GC-Setup main application."""

import os
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
        self._first_run_shown = False

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = GCSetupWindow(application=self)
        win.present()
        
        # Show first-run dialog if needed
        if not self._first_run_shown and self._is_first_run():
            self._first_run_shown = True
            GLib.timeout_add(100, self._show_first_run_dialog, win)

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

    def _is_first_run(self):
        """Check if this is the first run by looking for a config flag."""
        config_dir = GLib.get_user_config_dir()
        flag_file = os.path.join(config_dir, 'gc-setup', 'first-run-done')
        return not os.path.exists(flag_file)

    def _mark_first_run_done(self):
        """Mark that the first run dialog has been shown."""
        config_dir = GLib.get_user_config_dir()
        gc_config_dir = os.path.join(config_dir, 'gc-setup')
        flag_file = os.path.join(gc_config_dir, 'first-run-done')
        
        try:
            os.makedirs(gc_config_dir, exist_ok=True)
            with open(flag_file, 'w') as f:
                f.write('1')
        except OSError:
            pass

    def _show_first_run_dialog(self, parent_window):
        """Show the first-run warning dialog."""
        dialog = Adw.AlertDialog(
            heading='Welcome to GC-Setup',
            body='This application is primarily designed for **Fedora Linux**.\n\n'
                 'While other distributions (Debian/Ubuntu, Arch, openSUSE) are supported, '
                 'they may have limited functionality or require additional manual steps.\n\n'
                 'For the best experience, use GC-Setup on Fedora with the dnf package manager.',
        )
        dialog.set_body_use_markup(True)
        
        dialog.add_response('cancel', 'Exit')
        dialog.add_response('continue', 'Continue')
        dialog.set_response_appearance('continue', Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response('continue')
        dialog.set_close_response('cancel')
        
        dialog.connect('response', self._on_first_run_response, parent_window)
        dialog.present(parent_window)
        
        return False  # Don't repeat the timeout

    def _on_first_run_response(self, dialog, response, parent_window):
        """Handle first-run dialog response."""
        if response == 'continue':
            self._mark_first_run_done()
        else:
            # User chose to exit
            parent_window.close()
            self.quit()


def main():
    app = GCSetupApplication()
    return app.run(sys.argv)
