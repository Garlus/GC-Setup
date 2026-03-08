"""Detection module — checks what is already installed on startup."""

import os
import subprocess

from src.installer.flatpak import is_flatpak_installed_on_host
from src.installer.extensions import is_extension_installed
from src.installer.appimage import is_helium_installed


def detect_installed_apps(apps_page):
    """Check all apps on the apps page and mark installed ones.

    Should be called from a background thread, with UI updates
    posted via GLib.idle_add.
    """
    from gi.repository import GLib

    for row, checkbox, app_data in apps_page.get_check_rows():
        install_type = app_data.get('install_type', '')

        installed = False
        if install_type == 'flatpak':
            flatpak_id = app_data.get('flatpak_id', '')
            if flatpak_id:
                installed = is_flatpak_installed_on_host(flatpak_id)
        elif install_type == 'appimage':
            # Helium special case
            if 'helium' in app_data.get('name', '').lower():
                installed = is_helium_installed()

        if installed:
            GLib.idle_add(apps_page.mark_installed, app_data)


def detect_installed_extensions(extensions_page):
    """Check all extensions on the extensions page and mark installed ones."""
    from gi.repository import GLib

    for row, checkbox, ext_data in extensions_page.get_check_rows():
        uuid = ext_data.get('uuid', '')
        if uuid and is_extension_installed(uuid):
            GLib.idle_add(extensions_page.mark_installed, ext_data)


def detect_installed_misc(misc_page):
    """Check which misc tools are already installed.

    For system packages, we check if the binary exists on the host.
    """
    from gi.repository import GLib

    binary_checks = {
        'btop++': 'btop',
        'fastfetch': 'fastfetch',
        'Steam': 'steam',
    }

    for row, checkbox, item_data in misc_page._items:
        name = item_data.get('name', '')
        binary = binary_checks.get(name)
        if binary:
            installed = _check_binary_on_host(binary)
            if installed:
                GLib.idle_add(_mark_misc_installed, row, checkbox, item_data)


def _check_binary_on_host(binary_name):
    """Check if a binary exists on the host system."""
    try:
        if os.path.exists('/.flatpak-info'):
            result = subprocess.run(
                ['flatpak-spawn', '--host', 'which', binary_name],
                capture_output=True,
                timeout=5,
            )
        else:
            import shutil
            return shutil.which(binary_name) is not None
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _mark_misc_installed(row, checkbox, item_data):
    """Mark a misc item as installed in the UI."""
    checkbox.set_active(True)
    checkbox.set_sensitive(False)
    row.set_sensitive(False)
    row.set_subtitle(f"{item_data.get('description', '')} (installed)")
