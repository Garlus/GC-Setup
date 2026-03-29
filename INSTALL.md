# GC-Setup Installation Guide

## Quick Install (Recommended)

### One-Line Installation

Install GC-Setup with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | bash
```

This will automatically:
- ✅ Install Flatpak (if needed)
- ✅ Configure Flathub repository
- ✅ Install GNOME Platform/SDK
- ✅ Clone GC-Setup repository
- ✅ Build and install as Flatpak
- ✅ Create desktop launcher

**Supported distributions:**
- Fedora (primary)
- Debian/Ubuntu
- Arch Linux/Manjaro
- openSUSE

### Minimal Installation (If you already have Flatpak)

```bash
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install-minimal.sh | bash
```

---

## Manual Installation

### Prerequisites

1. **Install Flatpak:**
   ```bash
   # Fedora
   sudo dnf install flatpak flatpak-builder
   
   # Debian/Ubuntu
   sudo apt install flatpak flatpak-builder
   
   # Arch Linux
   sudo pacman -S flatpak flatpak-builder
   
   # openSUSE
   sudo zypper install flatpak flatpak-builder
   ```

2. **Add Flathub repository:**
   ```bash
   flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo
   ```

3. **Install GNOME SDK:**
   ```bash
   flatpak install --user flathub org.gnome.Platform//49 org.gnome.Sdk//49
   ```

4. **Install Git (if not already installed):**
   ```bash
   # Fedora
   sudo dnf install git
   
   # Debian/Ubuntu
   sudo apt install git
   
   # Arch Linux
   sudo pacman -S git
   ```

### Building from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gcsetup/gc-setup.git
   cd gc-setup
   ```

2. **Build and install:**
   ```bash
   flatpak-builder --user --install --force-clean build-dir io.github.gcsetup.GCSetup.yml
   ```

3. **Run GC-Setup:**
   ```bash
   flatpak run io.github.gcsetup.GCSetup
   ```

---

## Running GC-Setup

### From Command Line
```bash
flatpak run io.github.gcsetup.GCSetup
```

### From Application Menu
Search for "GC-Setup" in your GNOME application overview or app menu.

### Create an Alias (Optional)
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias gc-setup='flatpak run io.github.gcsetup.GCSetup'
```

Then reload and run:
```bash
source ~/.bashrc
gc-setup
```

---

## Updating GC-Setup

### Using the Install Script
Simply run the install script again:
```bash
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | bash
```

### Manual Update
```bash
cd ~/.local/share/gc-setup
git pull
flatpak-builder --user --install --force-clean /tmp/gc-setup-build io.github.gcsetup.GCSetup.yml
```

### Using Flatpak (if available on Flathub)
```bash
flatpak update io.github.gcsetup.GCSetup
```

---

## Uninstalling

### Remove Flatpak Application
```bash
flatpak uninstall --user io.github.gcsetup.GCSetup
```

### Remove Source Files
```bash
rm -rf ~/.local/share/gc-setup
```

### Remove Configuration (Optional)
```bash
rm -rf ~/.config/gc-setup
```

### Complete Removal
```bash
flatpak uninstall --user io.github.gcsetup.GCSetup
rm -rf ~/.local/share/gc-setup
rm -rf ~/.config/gc-setup
```

---

## Troubleshooting

### Build Fails

**Error: "No such file or directory"**
- Make sure Git is installed: `sudo dnf install git`
- Check internet connection

**Error: "flatpak-builder: command not found"**
- Install flatpak-builder: `sudo dnf install flatpak-builder`

**Error: "Runtime org.gnome.Platform not installed"**
- Install GNOME runtime: `flatpak install --user flathub org.gnome.Platform//49 org.gnome.Sdk//49`

### Application Won't Launch

**Check if installed:**
```bash
flatpak list --user | grep GCSetup
```

**Re-install if needed:**
```bash
flatpak uninstall --user io.github.gcsetup.GCSetup
curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | bash
```

**Check logs:**
```bash
flatpak run io.github.gcsetup.GCSetup 2>&1 | less
```

### Permissions Issues

GC-Setup needs to run host commands. If you see permission errors:

1. **Check Flatpak permissions:**
   ```bash
   flatpak info --show-permissions io.github.gcsetup.GCSetup
   ```

2. **Grant additional permissions if needed:**
   ```bash
   flatpak override --user io.github.gcsetup.GCSetup --talk-name=org.freedesktop.Flatpak
   ```

---

## Development Setup

### Using GNOME Builder

1. Install GNOME Builder:
   ```bash
   flatpak install flathub org.gnome.Builder
   ```

2. Open the project in Builder:
   ```bash
   cd gc-setup
   flatpak run org.gnome.Builder .
   ```

3. Click the Play button to build and run.

### Using Meson (Native)

```bash
meson setup builddir
meson compile -C builddir
meson install -C builddir --destdir=/tmp/gc-setup-install
```

---

## Additional Resources

- **Repository:** https://github.com/gcsetup/gc-setup
- **Issues:** https://github.com/gcsetup/gc-setup/issues
- **Flatpak Documentation:** https://docs.flatpak.org/

---

## Security Note

**About running scripts from the internet:**

The one-line install command downloads and executes a script. If you're concerned about security, you can:

1. **Review the script first:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh | less
   ```

2. **Download and inspect before running:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/gcsetup/gc-setup/main/install.sh -o install.sh
   cat install.sh  # Review the script
   bash install.sh
   ```

3. **Follow manual installation steps** (see above)

We recommend reviewing any script before executing it on your system.
