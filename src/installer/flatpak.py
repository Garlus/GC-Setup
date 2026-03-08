"""Flatpak app installer — runs flatpak install via host command."""

import subprocess
import shutil


def is_flatpak_installed(flatpak_id):
    """Check if a Flatpak app is already installed (user or system)."""
    flatpak_bin = _get_flatpak_bin()
    if not flatpak_bin:
        return False
    try:
        result = subprocess.run(
            [flatpak_bin, 'info', flatpak_id],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_flatpak(flatpak_id, callback=None):
    """Install a Flatpak app from Flathub.

    Args:
        flatpak_id: The Flatpak application ID.
        callback: Optional callable(success: bool, message: str).

    Returns:
        (success: bool, message: str)
    """
    flatpak_bin = _get_flatpak_bin()
    if not flatpak_bin:
        msg = 'flatpak is not installed on the host system'
        if callback:
            callback(False, msg)
        return False, msg

    try:
        # First ensure flathub remote is added
        subprocess.run(
            [flatpak_bin, 'remote-add', '--user', '--if-not-exists',
             'flathub', 'https://dl.flathub.org/repo/flathub.flatpakrepo'],
            capture_output=True,
            timeout=30,
        )

        # Install the app
        result = subprocess.run(
            [flatpak_bin, 'install', '--user', '--noninteractive',
             '--assumeyes', 'flathub', flatpak_id],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min timeout for large apps
        )

        if result.returncode == 0:
            msg = f'Successfully installed {flatpak_id}'
            if callback:
                callback(True, msg)
            return True, msg
        else:
            stderr = result.stderr.strip()
            msg = f'Failed to install {flatpak_id}: {stderr}'
            if callback:
                callback(False, msg)
            return False, msg

    except subprocess.TimeoutExpired:
        msg = f'Installation of {flatpak_id} timed out'
        if callback:
            callback(False, msg)
        return False, msg
    except (FileNotFoundError, OSError) as e:
        msg = f'Error running flatpak: {e}'
        if callback:
            callback(False, msg)
        return False, msg


def _get_flatpak_bin():
    """Find the flatpak binary, checking host system paths."""
    # When running inside a Flatpak, we can use flatpak-spawn
    # to execute commands on the host
    if _is_inside_flatpak():
        return 'flatpak-spawn'
    return shutil.which('flatpak')


def _is_inside_flatpak():
    """Check if we're running inside a Flatpak sandbox."""
    import os
    return os.path.exists('/.flatpak-info')


def install_flatpak_on_host(flatpak_id, callback=None):
    """Install a Flatpak app, handling the case where we're inside a Flatpak.

    Uses flatpak-spawn --host to break out of the sandbox when needed.
    """
    if _is_inside_flatpak():
        return _install_via_host_spawn(flatpak_id, callback)
    else:
        return install_flatpak(flatpak_id, callback)


def _install_via_host_spawn(flatpak_id, callback=None):
    """Install a Flatpak from within a Flatpak sandbox using flatpak-spawn."""
    try:
        # Add flathub remote
        subprocess.run(
            ['flatpak-spawn', '--host', 'flatpak', 'remote-add',
             '--user', '--if-not-exists', 'flathub',
             'https://dl.flathub.org/repo/flathub.flatpakrepo'],
            capture_output=True,
            timeout=30,
        )

        result = subprocess.run(
            ['flatpak-spawn', '--host', 'flatpak', 'install',
             '--user', '--noninteractive', '--assumeyes',
             'flathub', flatpak_id],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode == 0:
            msg = f'Successfully installed {flatpak_id}'
            if callback:
                callback(True, msg)
            return True, msg
        else:
            stderr = result.stderr.strip()
            msg = f'Failed to install {flatpak_id}: {stderr}'
            if callback:
                callback(False, msg)
            return False, msg

    except subprocess.TimeoutExpired:
        msg = f'Installation of {flatpak_id} timed out'
        if callback:
            callback(False, msg)
        return False, msg
    except (FileNotFoundError, OSError) as e:
        msg = f'Error: {e}'
        if callback:
            callback(False, msg)
        return False, msg


def is_flatpak_installed_on_host(flatpak_id):
    """Check if a Flatpak is installed, handling sandbox."""
    import os
    if os.path.exists('/.flatpak-info'):
        try:
            result = subprocess.run(
                ['flatpak-spawn', '--host', 'flatpak', 'info', flatpak_id],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    else:
        return is_flatpak_installed(flatpak_id)
