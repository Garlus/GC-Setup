"""Detection module — checks what is already installed on startup.

Uses the unified catalog item format where detection info is nested
under item['detect'] with keys: command, flatpak_id, extension_uuid.
"""

import os
import subprocess

from src.installer.flatpak import is_flatpak_installed_on_host
from src.installer.extensions import is_extension_installed
from src.installer.appimage import is_helium_installed


def detect_installed_items(pages):
    """Check all items across all pages and mark installed ones.

    Should be called from a background thread.  UI updates are posted
    via GLib.idle_add.

    Args:
        pages: List of CategoryPage (or subclass) instances.
    """
    from gi.repository import GLib

    for page in pages:
        for _row, _checkbox, item_data in page.get_check_rows():
            detect = item_data.get('detect', {})
            install = item_data.get('install', {})
            method = install.get('method', '')

            installed = False

            # 1. Check by command existence on host
            cmd_name = detect.get('command')
            if cmd_name and not installed:
                installed = _check_binary_on_host(cmd_name)

            # 2. Check by Flatpak ID
            flatpak_id = detect.get('flatpak_id')
            if flatpak_id and not installed:
                installed = is_flatpak_installed_on_host(flatpak_id)

            # 3. Check by GNOME extension UUID
            ext_uuid = detect.get('extension_uuid')
            if ext_uuid and not installed:
                installed = is_extension_installed(ext_uuid)

            # 4. Special case: AppImage (Helium)
            if method == 'appimage' and not installed:
                installed = is_helium_installed()

            if installed:
                GLib.idle_add(page.mark_installed, item_data)


def _check_binary_on_host(binary_name):
    """Check if a binary exists on the host system."""
    try:
        if os.path.exists('/.flatpak-info'):
            result = subprocess.run(
                ['flatpak-spawn', '--host', 'which', binary_name],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        else:
            import shutil
            return shutil.which(binary_name) is not None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
