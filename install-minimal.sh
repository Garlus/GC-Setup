#!/bin/bash
# GC-Setup Quick Install (Minimal version - assumes Flatpak is installed)

set -e

REPO_URL="https://github.com/gcsetup/gc-setup.git"
INSTALL_DIR="$HOME/.local/share/gc-setup"
BUILD_DIR="/tmp/gc-setup-build-$$"

echo "🚀 Installing GC-Setup..."

# Clone or update
if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR" && git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Install GNOME runtime
echo "📦 Installing dependencies..."
flatpak install --user -y flathub org.gnome.Platform//49 org.gnome.Sdk//49 2>/dev/null || true

# Build and install
echo "🔨 Building GC-Setup..."
cd "$INSTALL_DIR"
flatpak-builder --user --install --force-clean "$BUILD_DIR" io.github.gcsetup.GCSetup.yml

# Cleanup
rm -rf "$BUILD_DIR"

echo "✅ Installation complete!"
echo ""
echo "Run with: flatpak run io.github.gcsetup.GCSetup"
