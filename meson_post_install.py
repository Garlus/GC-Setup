#!/usr/bin/env python3

import os
import subprocess

prefix = os.environ.get('MESON_INSTALL_PREFIX', '/usr/local')
datadir = os.path.join(prefix, 'share')

# Update icon cache
icon_cache_dir = os.path.join(datadir, 'icons', 'hicolor')
if os.path.exists(icon_cache_dir):
    print('Updating icon cache...')
    subprocess.call(['gtk-update-icon-cache', '-qtf', icon_cache_dir])

# Update desktop database
desktop_dir = os.path.join(datadir, 'applications')
if os.path.exists(desktop_dir):
    print('Updating desktop database...')
    subprocess.call(['update-desktop-database', '-q', desktop_dir])
