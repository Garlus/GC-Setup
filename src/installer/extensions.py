"""GNOME Shell extension installer — downloads from extensions.gnome.org."""

import json
import os
import subprocess
import tempfile
import urllib.request
import urllib.error


GNOME_EXT_API = 'https://extensions.gnome.org'


def get_shell_version():
    """Get the running GNOME Shell version."""
    try:
        cmd = ['gnome-shell', '--version']
        if os.path.exists('/.flatpak-info'):
            cmd = ['flatpak-spawn', '--host'] + cmd
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Output: "GNOME Shell 46.2"
            parts = result.stdout.strip().split()
            if len(parts) >= 3:
                version = parts[-1]
                # Return major version (e.g., "46" from "46.2")
                return version.split('.')[0]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_extension_installed(uuid):
    """Check if a GNOME Shell extension is installed."""
    try:
        cmd = ['gnome-extensions', 'show', uuid]
        if os.path.exists('/.flatpak-info'):
            cmd = ['flatpak-spawn', '--host'] + cmd
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_extension(ext_id, uuid, callback=None):
    """Install a GNOME Shell extension by downloading from extensions.gnome.org.

    Args:
        ext_id: The numeric extension ID on extensions.gnome.org.
        uuid: The extension UUID.
        callback: Optional callable(success: bool, message: str).

    Returns:
        (success: bool, message: str)
    """
    shell_version = get_shell_version()
    if not shell_version:
        msg = 'Could not detect GNOME Shell version'
        if callback:
            callback(False, msg)
        return False, msg

    try:
        # Query the extension info to get the download URL
        info_url = (
            f'{GNOME_EXT_API}/extension-info/'
            f'?uuid={uuid}&shell_version={shell_version}'
        )
        req = urllib.request.Request(info_url)
        req.add_header('User-Agent', 'GC-Setup/1.0')

        with urllib.request.urlopen(req, timeout=15) as resp:
            info = json.loads(resp.read().decode('utf-8'))

        download_url = info.get('download_url')
        if not download_url:
            msg = f'No compatible version of {uuid} for GNOME Shell {shell_version}'
            if callback:
                callback(False, msg)
            return False, msg

        # Download the zip
        full_url = f'{GNOME_EXT_API}{download_url}'
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp_path = tmp.name
            req = urllib.request.Request(full_url)
            req.add_header('User-Agent', 'GC-Setup/1.0')
            with urllib.request.urlopen(req, timeout=60) as resp:
                tmp.write(resp.read())

        # Install via gnome-extensions CLI
        cmd = ['gnome-extensions', 'install', '--force', tmp_path]
        if os.path.exists('/.flatpak-info'):
            cmd = ['flatpak-spawn', '--host'] + cmd

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Clean up
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        if result.returncode == 0:
            # Enable the extension
            enable_cmd = ['gnome-extensions', 'enable', uuid]
            if os.path.exists('/.flatpak-info'):
                enable_cmd = ['flatpak-spawn', '--host'] + enable_cmd
            subprocess.run(enable_cmd, capture_output=True, timeout=10)

            msg = f'Successfully installed {uuid}'
            if callback:
                callback(True, msg)
            return True, msg
        else:
            stderr = result.stderr.strip()
            msg = f'Failed to install {uuid}: {stderr}'
            if callback:
                callback(False, msg)
            return False, msg

    except urllib.error.URLError as e:
        msg = f'Network error installing {uuid}: {e}'
        if callback:
            callback(False, msg)
        return False, msg
    except json.JSONDecodeError:
        msg = f'Invalid response from extensions.gnome.org for {uuid}'
        if callback:
            callback(False, msg)
        return False, msg
    except subprocess.TimeoutExpired:
        msg = f'Installation of {uuid} timed out'
        if callback:
            callback(False, msg)
        return False, msg
    except (FileNotFoundError, OSError) as e:
        msg = f'Error installing {uuid}: {e}'
        if callback:
            callback(False, msg)
        return False, msg
