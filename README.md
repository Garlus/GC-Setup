<<<<<<< HEAD
# GC-Setup
=======
# GC-Setup

Set up your GNOME desktop with apps, extensions, and system tweaks.

GC-Setup is a GTK4/libadwaita application that helps you quickly configure a fresh GNOME desktop installation. Select the apps you want from Flathub, choose GNOME Shell extensions, and get guidance on system-level packages — all from a single interface.

<!-- TODO: Add screenshot -->
<!-- ![GC-Setup Screenshot](data/screenshots/main.png) -->

## Features

- **Flatpak Apps** — Install curated apps from Flathub across categories: Browsers, Media, Communication, Development, Productivity, Gaming, and Utilities
- **GNOME Shell Extensions** — Install popular extensions (Blur my Shell, Night Theme Switcher, Luminus) directly from extensions.gnome.org
- **System Packages** — Get copyable terminal commands for native packages (Steam, Microsoft Fonts, codecs, xpadneo, btop++, fastfetch) with automatic detection of your package manager (apt/dnf/pacman/zypper)
- **Font Rendering** — One-click sharp font rendering (macOS-style) with Apply/Revert buttons
- **Helium Browser** — Automatic AppImage installation from GitHub Releases with desktop integration
- **Smart Detection** — Already-installed software is automatically detected and greyed out on startup

## Building

### Requirements

- GNOME SDK 49 (`org.gnome.Sdk//49`)
- GNOME Platform 49 (`org.gnome.Platform//49`)
- Flatpak Builder

### Install the SDK

```bash
flatpak install flathub org.gnome.Sdk//49
```

### Build with GNOME Builder

Open the project in GNOME Builder and hit the Play button. Builder will use the Flatpak manifest automatically.

### Build with Flatpak Builder (CLI)

```bash
flatpak-builder --user --install --force-clean build-dir io.github.gcsetup.GCSetup.yml
```

### Build with Meson (for development)

```bash
meson setup builddir
meson install -C builddir
```

## Running

After installing via Flatpak:

```bash
flatpak run io.github.gcsetup.GCSetup
```

## How It Works

GC-Setup runs as a Flatpak but needs to install software on the host system. It achieves this through:

- **Flatpak apps**: Installed via `flatpak install` using `flatpak-spawn --host` to escape the sandbox
- **GNOME Extensions**: Downloaded from extensions.gnome.org API and installed via `gnome-extensions install`
- **Helium browser**: Downloaded as AppImage from GitHub Releases with automatic `.desktop` file creation
- **System packages**: Since native package installation requires root privileges outside the sandbox, GC-Setup provides copyable terminal commands for the user's detected package manager
- **Font rendering**: Applied via `gsettings` through `flatpak-spawn --host`

## Project Structure

```
GC-Setup/
├── meson.build                        # Meson build system
├── io.github.gcsetup.GCSetup.yml      # Flatpak manifest (GNOME 49)
├── data/
│   ├── gc-setup.in                    # Launcher script template
│   ├── *.desktop                      # Desktop entry
│   ├── *.appdata.xml                  # AppStream metadata
│   └── icons/                         # App icon
└── src/
    ├── main.py                        # Application entry point
    ├── window.py                      # Main window (AdwOverlaySplitView)
    ├── pages/
    │   ├── apps_page.py               # Flatpak apps selection
    │   ├── extensions_page.py         # GNOME extensions selection
    │   └── misc_page.py               # System packages & font rendering
    ├── installer/
    │   ├── flatpak.py                 # Flatpak install backend
    │   ├── extensions.py              # Extension install backend
    │   ├── appimage.py                # Helium AppImage installer
    │   ├── detection.py               # Already-installed detection
    │   └── dialog.py                  # Progress window
    └── data/
        ├── apps.json                  # App catalog
        ├── extensions.json            # Extensions catalog
        └── misc.json                  # System package commands
```

## License

GPL-3.0-or-later
>>>>>>> 99473a7 (lokale Änderungen sichern)
