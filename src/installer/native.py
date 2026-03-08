"""Native package installer — detects host package manager and installs packages.

Supports apt, dnf, pacman, and zypper.  Uses flatpak-spawn --host when
running inside a Flatpak sandbox.  Falls back to Flatpak if a
flatpak_fallback ID is specified and native install fails.
"""

import os
import subprocess

from src.installer.flatpak import install_flatpak_on_host


# Package managers and how to detect them (in priority order)
_PKG_MANAGERS = ['apt', 'dnf', 'pacman', 'zypper']

# Cached result so we only detect once
_detected_packager = None


def detect_package_manager():
    """Detect which package manager is available on the host.

    Returns one of 'apt', 'dnf', 'pacman', 'zypper', or None.
    """
    global _detected_packager
    if _detected_packager is not None:
        return _detected_packager

    for pm in _PKG_MANAGERS:
        if _check_binary_on_host(pm):
            _detected_packager = pm
            return pm

    _detected_packager = ''  # empty string = checked but not found
    return None


def install_native(item, callback=None):
    """Install a native package item.

    Reads item['install']['packages'] to find the right package name for
    the detected package manager, then runs the install command via the
    host shell.  If native install fails and item['install']['flatpak_fallback']
    is set, falls back to Flatpak.

    Args:
        item: A catalog item dict with item['install'] containing
              'packages' and optionally 'flatpak_fallback'.
        callback: Optional callable(success, message).

    Returns:
        (success: bool, message: str)
    """
    install_info = item.get('install', {})
    packages = install_info.get('packages', {})
    fallback_id = install_info.get('flatpak_fallback', '')
    name = item.get('name', 'Unknown')

    pm = detect_package_manager()
    if not pm:
        if fallback_id:
            return _do_flatpak_fallback(fallback_id, name, callback)
        msg = 'No supported package manager found on the host system'
        if callback:
            callback(False, msg)
        return False, msg

    pkg = packages.get(pm, '')
    if not pkg:
        if fallback_id:
            return _do_flatpak_fallback(fallback_id, name, callback)
        msg = f'No package name defined for {pm}'
        if callback:
            callback(False, msg)
        return False, msg

    # Build the install command
    cmd_str = _build_install_command(pm, pkg)
    success, message = _run_on_host(cmd_str, name)

    if success:
        if callback:
            callback(True, message)
        return True, message

    # Native failed — try flatpak fallback if available
    if fallback_id:
        return _do_flatpak_fallback(fallback_id, name, callback)

    if callback:
        callback(False, message)
    return False, message


def _build_install_command(pm, pkg):
    """Build the shell install command for the given package manager."""
    if pm == 'apt':
        return f'sudo apt install -y {pkg}'
    elif pm == 'dnf':
        return f'sudo dnf install -y {pkg}'
    elif pm == 'pacman':
        return f'sudo pacman -S --noconfirm {pkg}'
    elif pm == 'zypper':
        return f'sudo zypper install -y {pkg}'
    return f'{pm} install {pkg}'


def _run_on_host(cmd_str, name):
    """Run a shell command on the host (via flatpak-spawn if sandboxed).

    Returns (success, message).
    """
    try:
        if os.path.exists('/.flatpak-info'):
            cmd = ['flatpak-spawn', '--host', 'bash', '-c', cmd_str]
        else:
            cmd = ['bash', '-c', cmd_str]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )

        if result.returncode == 0:
            return True, f'Successfully installed {name}'
        else:
            stderr = result.stderr.strip()
            return False, f'Failed to install {name}: {stderr}'

    except subprocess.TimeoutExpired:
        return False, f'Installation of {name} timed out'
    except (FileNotFoundError, OSError) as e:
        return False, f'Error installing {name}: {e}'


def _do_flatpak_fallback(flatpak_id, name, callback=None):
    """Fall back to Flatpak installation."""
    success, message = install_flatpak_on_host(flatpak_id)
    if success:
        message = f'Installed {name} via Flatpak (native install unavailable)'
    if callback:
        callback(success, message)
    return success, message


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


def resolve_system_command(item):
    """Resolve the correct system command for the detected package manager.

    For items with install.method == 'system', picks the right command
    from install.commands based on the detected package manager.

    Returns the command string or empty string if not available.
    """
    install_info = item.get('install', {})
    commands = install_info.get('commands', {})

    # Check for 'all' key first (universal command)
    if 'all' in commands:
        return commands['all']

    pm = detect_package_manager()
    if pm and pm in commands:
        return commands[pm]

    # No matching command
    return ''
