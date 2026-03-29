#!/bin/bash
# GC-Setup Quick Installer
# This script installs GC-Setup as a Flatpak application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
   ____  ____      ____       _               
  / ___|/ ___|    / ___|  ___| |_ _   _ _ __  
 | |  _| |   _____\___ \ / _ \ __| | | | '_ \ 
 | |_| | |__|_____|___) |  __/ |_| |_| | |_) |
  \____|\____|    |____/ \___|\__|\__,_| .__/ 
                                       |_|    
EOF
echo -e "${NC}"
echo -e "${GREEN}GC-Setup Installer${NC}"
echo -e "Primarily designed for ${YELLOW}Fedora Linux${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Do not run this script as root!${NC}"
    echo "Flatpak should be installed as a regular user."
    exit 1
fi

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

echo -e "${BLUE}→${NC} Detected distribution: ${YELLOW}$DISTRO${NC}"

# Warn if not Fedora
if [ "$DISTRO" != "fedora" ]; then
    echo -e "${YELLOW}⚠ Warning: GC-Setup is primarily designed for Fedora.${NC}"
    echo -e "  Other distributions may have limited functionality."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Check and install Flatpak
echo ""
echo -e "${BLUE}→${NC} Checking for Flatpak..."

if ! command -v flatpak &> /dev/null; then
    echo -e "${YELLOW}Flatpak not found. Installing...${NC}"
    
    case "$DISTRO" in
        fedora)
            sudo dnf install -y flatpak
            ;;
        ubuntu|debian)
            sudo apt update
            sudo apt install -y flatpak
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm flatpak
            ;;
        opensuse*)
            sudo zypper install -y flatpak
            ;;
        *)
            echo -e "${RED}Error: Unable to auto-install Flatpak on $DISTRO${NC}"
            echo "Please install Flatpak manually and re-run this script."
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✓${NC} Flatpak is installed"
fi

# Add Flathub repository
echo -e "${BLUE}→${NC} Configuring Flathub repository..."
if ! flatpak remote-list | grep -q flathub; then
    flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo
    echo -e "${GREEN}✓${NC} Flathub repository added"
else
    echo -e "${GREEN}✓${NC} Flathub already configured"
fi

# Install GNOME Platform and SDK
echo -e "${BLUE}→${NC} Installing GNOME runtime (this may take a while)..."
flatpak install --user -y flathub org.gnome.Platform//49 org.gnome.Sdk//49 2>/dev/null || true
echo -e "${GREEN}✓${NC} GNOME runtime ready"

# Install flatpak-builder
echo -e "${BLUE}→${NC} Checking for flatpak-builder..."
if ! command -v flatpak-builder &> /dev/null; then
    echo -e "${YELLOW}Installing flatpak-builder...${NC}"
    
    case "$DISTRO" in
        fedora)
            sudo dnf install -y flatpak-builder
            ;;
        ubuntu|debian)
            sudo apt install -y flatpak-builder
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm flatpak-builder
            ;;
        opensuse*)
            sudo zypper install -y flatpak-builder
            ;;
        *)
            echo -e "${YELLOW}Warning: Could not install flatpak-builder${NC}"
            ;;
    esac
else
    echo -e "${GREEN}✓${NC} flatpak-builder is installed"
fi

# Determine installation directory
INSTALL_DIR="$HOME/.local/share/gc-setup"
BUILD_DIR="/tmp/gc-setup-build-$$"

echo -e "${BLUE}→${NC} Installation directory: ${YELLOW}$INSTALL_DIR${NC}"

# Clone or update repository
echo -e "${BLUE}→${NC} Downloading GC-Setup..."

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}Git not found. Installing...${NC}"
        case "$DISTRO" in
            fedora)
                sudo dnf install -y git
                ;;
            ubuntu|debian)
                sudo apt install -y git
                ;;
            arch|manjaro)
                sudo pacman -S --noconfirm git
                ;;
            opensuse*)
                sudo zypper install -y git
                ;;
        esac
    fi
    
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/gcsetup/gc-setup.git "$INSTALL_DIR" || \
    git clone https://gitlab.com/gcsetup/gc-setup.git "$INSTALL_DIR" || {
        echo -e "${RED}Error: Could not clone repository${NC}"
        echo "Please check your internet connection or clone manually:"
        echo "  git clone <repository-url> $INSTALL_DIR"
        exit 1
    }
fi

echo -e "${GREEN}✓${NC} Source code ready"

# Build the Flatpak
echo ""
echo -e "${BLUE}→${NC} Building GC-Setup Flatpak..."
echo "This may take several minutes on first build..."

cd "$INSTALL_DIR"

# Create build directory
mkdir -p "$BUILD_DIR"

# Build and install
if flatpak-builder --user --install --force-clean "$BUILD_DIR" io.github.gcsetup.GCSetup.yml; then
    echo -e "${GREEN}✓${NC} Build completed successfully"
else
    echo -e "${RED}Error: Build failed${NC}"
    echo "You can try building manually with:"
    echo "  cd $INSTALL_DIR"
    echo "  flatpak-builder --user --install --force-clean $BUILD_DIR io.github.gcsetup.GCSetup.yml"
    exit 1
fi

# Clean up build directory
rm -rf "$BUILD_DIR"

# Create desktop launcher if not exists
DESKTOP_FILE="$HOME/.local/share/applications/gc-setup.desktop"
if [ ! -f "$DESKTOP_FILE" ]; then
    echo -e "${BLUE}→${NC} Creating desktop launcher..."
    flatpak run --command=update-desktop-database io.github.gcsetup.GCSetup 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                            ║${NC}"
echo -e "${GREEN}║   ✓ Installation completed successfully!  ║${NC}"
echo -e "${GREEN}║                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "You can now run GC-Setup with:"
echo -e "  ${YELLOW}flatpak run io.github.gcsetup.GCSetup${NC}"
echo ""
echo -e "Or search for '${YELLOW}GC-Setup${NC}' in your application menu."
echo ""

# Ask if user wants to launch now
read -p "Launch GC-Setup now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${BLUE}→${NC} Launching GC-Setup..."
    flatpak run io.github.gcsetup.GCSetup &
    echo -e "${GREEN}✓${NC} GC-Setup is starting..."
fi

echo ""
echo -e "For updates, run this script again or use:"
echo -e "  ${YELLOW}flatpak update io.github.gcsetup.GCSetup${NC}"
echo ""
echo -e "${BLUE}Thank you for using GC-Setup!${NC}"
