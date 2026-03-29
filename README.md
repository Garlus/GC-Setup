
# GC-Setup

**Garlicus Computer - Setup**

A GNOME application for setting up and configuring your Linux system with popular applications, extensions, and system tweaks.

## ⚠️ Primary Target: Fedora Linux

This tool is primarily designed and tested for **Fedora Linux**. While it includes support for other distributions (Debian/Ubuntu, Arch Linux, openSUSE), the best experience and most reliable functionality is on Fedora with the `dnf` package manager.

**Supported distributions:**
- ✅ **Fedora** (primary, fully tested)
- ⚠️ Debian/Ubuntu (apt) - community supported
- ⚠️ Arch Linux (pacman) - community supported  
- ⚠️ openSUSE (zypper) - community supported

## Quick Install (One-Line Command)

Install and run GC-Setup with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | bash
```

**What this does:**
- Installs Flatpak (if not present)
- Adds Flathub repository
- Clones and builds GC-Setup
- Installs as a Flatpak application
- Optionally launches the app

**For more installation options, see [INSTALL.md](INSTALL.md)**

## Features

- **Flatpak Apps** — Install curated apps from Flathub across categories
- **GNOME Shell Extensions** — Install popular extensions directly from extensions.gnome.org
- **System Packages** — Get copyable terminal commands for native packages with automatic detection of your package manager
- **Font Rendering** — One-click sharp font rendering (macOS-style)
- **System Tweaks** — Quick actions for system updates, cleanup, virtualization, and more


## Manual Building

### Requirements

### Install the SDK

```bash
flatpak install flathub org.gnome.Sdk//49
```

### Build with GNOME Builder

Open the project in GNOME Builder and hit the Play button.

## Running GC-Setup

After installation via the install script:

```bash
# Launch from command line
flatpak run io.github.gcsetup.GCSetup

# Or search for "GC-Setup" in your application menu
```

To update:
```bash
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | bash
```

## Uninstalling

```bash
flatpak uninstall --user io.github.gcsetup.GCSetup
rm -rf ~/.local/share/gc-setup
```

## Contributing

Contributions are welcome! If you're using GC-Setup on a non-Fedora distribution, please report any issues and consider contributing fixes for your platform.

## License

GPL-3.0
