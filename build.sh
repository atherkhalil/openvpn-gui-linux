#!/bin/bash
# Build script for creating a standalone binary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Building OpenVPN Manager binary..."

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running setup first..."
    "$SCRIPT_DIR/setup.sh"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install build dependencies
echo "Installing build dependencies..."
pip install -q pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"

# Create icon directory if it doesn't exist
ICON_DIR="$SCRIPT_DIR/icons"
mkdir -p "$ICON_DIR"

# Check if icon exists
if [ ! -f "$ICON_DIR/openvpn-manager.svg" ]; then
    echo "Warning: Icon not found at $ICON_DIR/openvpn-manager.svg"
fi

# Convert SVG to PNG for PyInstaller (PyInstaller works better with PNG)
ICON_PNG=""
if [ -f "$ICON_DIR/openvpn-manager.svg" ]; then
    ICON_PNG="$ICON_DIR/openvpn-manager.png"
    # Try to convert SVG to PNG if inkscape or convert is available
    if command -v inkscape &> /dev/null; then
        echo "Converting SVG icon to PNG..."
        inkscape "$ICON_DIR/openvpn-manager.svg" -o "$ICON_PNG" -w 512 -h 512 2>/dev/null || ICON_PNG=""
    elif command -v convert &> /dev/null; then
        echo "Converting SVG icon to PNG..."
        convert "$ICON_DIR/openvpn-manager.svg" -resize 512x512 "$ICON_PNG" 2>/dev/null || ICON_PNG=""
    else
        echo "Warning: No SVG converter found (inkscape or imagemagick). PyInstaller may not use the icon."
        ICON_PNG=""
    fi
    
    # If conversion failed, try using SVG anyway (PyInstaller might support it)
    if [ -z "$ICON_PNG" ] || [ ! -f "$ICON_PNG" ]; then
        echo "Using SVG icon directly (conversion failed or converter not available)"
        ICON_PNG="$ICON_DIR/openvpn-manager.svg"
    fi
elif [ -f "$ICON_DIR/openvpn-manager.png" ]; then
    ICON_PNG="$ICON_DIR/openvpn-manager.png"
else
    echo "Warning: No icon found. Building without icon."
    ICON_PNG=""
fi

# Build with PyInstaller
echo "Building binary with PyInstaller..."
PYINSTALLER_ARGS=(
    --name="openvpn-manager"
    --onefile
    --noconsole
    --clean
    --noconfirm
    --add-data="openvpn_manager.py:."
    --hidden-import=PySide6.QtCore
    --hidden-import=PySide6.QtGui
    --hidden-import=PySide6.QtWidgets
    --hidden-import=PySide6.QtOpenGL
    --hidden-import=pexpect
    --collect-submodules=PySide6
    --collect-all=PySide6
)

if [ -n "$ICON_PNG" ] && [ -f "$ICON_PNG" ]; then
    PYINSTALLER_ARGS+=(--icon="$ICON_PNG")
fi

PYINSTALLER_ARGS+=(main.py)

pyinstaller "${PYINSTALLER_ARGS[@]}"

if [ -f "$DIST_DIR/openvpn-manager" ]; then
    echo ""
    echo "✓ Build successful!"
    echo "Binary location: $DIST_DIR/openvpn-manager"
    echo ""
    echo "To install system-wide, run:"
    echo "  ./install.sh"
else
    echo "✗ Build failed. Check the output above for errors."
    exit 1
fi

