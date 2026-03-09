"""Helium browser AppImage installer — downloads from GitHub Releases."""

import json
import os
import platform
import stat
import subprocess
import tempfile
import urllib.request
import urllib.error


HELIUM_REPO = 'imputnet/helium-linux'
HELIUM_API = f'https://api.github.com/repos/{HELIUM_REPO}/releases/latest'

# Where to install
HELIUM_DIR = os.path.expanduser('~/.local/share/helium')
HELIUM_APPIMAGE = os.path.join(HELIUM_DIR, 'helium.AppImage')
HELIUM_DESKTOP = os.path.expanduser(
    '~/.local/share/applications/helium-browser.desktop'
)
HELIUM_ICON_DIR = os.path.expanduser('~/.local/share/icons/hicolor/256x256/apps')
HELIUM_ICON = os.path.join(HELIUM_ICON_DIR, 'helium-browser.png')


def is_helium_installed():
    """Check if Helium AppImage is already installed."""
    return os.path.isfile(HELIUM_APPIMAGE) and os.access(HELIUM_APPIMAGE, os.X_OK)


def uninstall_helium():
    """Remove the Helium browser AppImage, desktop entry, and icon.

    Returns:
        (success: bool, message: str)
    """
    errors = []
    for path, label in [
        (HELIUM_APPIMAGE, 'AppImage'),
        (HELIUM_DESKTOP, 'desktop entry'),
        (HELIUM_ICON, 'icon'),
    ]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                errors.append(f'{label}: {e}')

    # Remove empty install dir
    if os.path.isdir(HELIUM_DIR):
        try:
            os.rmdir(HELIUM_DIR)
        except OSError:
            pass  # not empty, leave it

    # Update desktop database
    try:
        subprocess.run(
            ['update-desktop-database',
             os.path.expanduser('~/.local/share/applications')],
            capture_output=True, timeout=10,
        )
    except (FileNotFoundError, OSError):
        pass

    if errors:
        return False, f'Partial removal: {"; ".join(errors)}'
    return True, 'Removed Helium browser'


def install_helium(callback=None):
    """Download and install the Helium browser AppImage.

    Args:
        callback: Optional callable(success: bool, message: str).

    Returns:
        (success: bool, message: str)
    """
    try:
        # Get latest release info
        req = urllib.request.Request(HELIUM_API)
        req.add_header('User-Agent', 'GC-Setup/1.0')
        req.add_header('Accept', 'application/vnd.github+json')

        with urllib.request.urlopen(req, timeout=15) as resp:
            release = json.loads(resp.read().decode('utf-8'))

        # Find the correct AppImage asset
        arch = platform.machine()
        # Map Python arch names to GitHub release naming
        arch_map = {
            'x86_64': 'x86_64',
            'aarch64': 'arm64',
            'amd64': 'x86_64',
        }
        target_arch = arch_map.get(arch, arch)

        appimage_url = None
        for asset in release.get('assets', []):
            name = asset.get('name', '')
            if name.endswith('.AppImage') and target_arch in name.lower():
                appimage_url = asset.get('browser_download_url')
                break

        # Fallback: try any AppImage
        if not appimage_url:
            for asset in release.get('assets', []):
                name = asset.get('name', '')
                if name.endswith('.AppImage'):
                    appimage_url = asset.get('browser_download_url')
                    break

        if not appimage_url:
            msg = 'Could not find Helium AppImage in the latest release'
            if callback:
                callback(False, msg)
            return False, msg

        # Create directories
        os.makedirs(HELIUM_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(HELIUM_DESKTOP), exist_ok=True)
        os.makedirs(HELIUM_ICON_DIR, exist_ok=True)

        # Download AppImage
        req = urllib.request.Request(appimage_url)
        req.add_header('User-Agent', 'GC-Setup/1.0')

        with urllib.request.urlopen(req, timeout=300) as resp:
            with open(HELIUM_APPIMAGE, 'wb') as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        # Make executable
        st = os.stat(HELIUM_APPIMAGE)
        os.chmod(HELIUM_APPIMAGE, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Try to download icon from the repo
        _download_icon()

        # Create .desktop file
        _create_desktop_entry()

        # Update desktop database
        try:
            subprocess.run(
                ['update-desktop-database',
                 os.path.expanduser('~/.local/share/applications')],
                capture_output=True,
                timeout=10,
            )
        except (FileNotFoundError, OSError):
            pass

        msg = 'Successfully installed Helium browser'
        if callback:
            callback(True, msg)
        return True, msg

    except urllib.error.URLError as e:
        msg = f'Network error downloading Helium: {e}'
        if callback:
            callback(False, msg)
        return False, msg
    except json.JSONDecodeError:
        msg = 'Invalid response from GitHub API'
        if callback:
            callback(False, msg)
        return False, msg
    except (OSError, IOError) as e:
        msg = f'Error installing Helium: {e}'
        if callback:
            callback(False, msg)
        return False, msg


def _download_icon():
    """Try to download the Helium icon."""
    icon_url = (
        'https://raw.githubusercontent.com/imputnet/helium/main/'
        'resources/branding/app_icon/raw.png'
    )
    try:
        req = urllib.request.Request(icon_url)
        req.add_header('User-Agent', 'GC-Setup/1.0')
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(HELIUM_ICON, 'wb') as f:
                f.write(resp.read())
    except (urllib.error.URLError, OSError):
        pass  # Icon is optional


def _create_desktop_entry():
    """Create a .desktop file for Helium."""
    icon_path = HELIUM_ICON if os.path.isfile(HELIUM_ICON) else 'web-browser'

    desktop_content = f"""[Desktop Entry]
Name=Helium
Comment=Private, fast, and honest web browser
Exec={HELIUM_APPIMAGE} %U
Icon={icon_path}
Terminal=false
Type=Application
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
StartupWMClass=helium
"""
    with open(HELIUM_DESKTOP, 'w') as f:
        f.write(desktop_content)
