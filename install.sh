#!/bin/bash
# Installation script for OpenVPN Manager
# Installs the binary and desktop entry

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARY_SOURCE="$SCRIPT_DIR/dist/openvpn-manager"
BINARY_DEST="/usr/local/bin/openvpn-manager"
DESKTOP_SOURCE="$SCRIPT_DIR/openvpn-manager.desktop"
DESKTOP_DEST="/usr/local/share/applications/openvpn-manager.desktop"
ICON_SOURCE_DIR="$SCRIPT_DIR/icons"
ICON_DEST_DIR="/usr/local/share/icons/hicolor"

echo "Installing OpenVPN Manager..."

# Check if binary exists
if [ ! -f "$BINARY_SOURCE" ]; then
    echo "Error: Binary not found at $BINARY_SOURCE"
    echo "Please run ./build.sh first to create the binary."
    exit 1
fi

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script requires sudo privileges."
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Install binary
echo "Installing binary to $BINARY_DEST..."
cp "$BINARY_SOURCE" "$BINARY_DEST"
chmod +x "$BINARY_DEST"
echo "✓ Binary installed"

# Install desktop entry
if [ -f "$DESKTOP_SOURCE" ]; then
    echo "Installing desktop entry..."
    cp "$DESKTOP_SOURCE" "$DESKTOP_DEST"
    chmod 644 "$DESKTOP_DEST"
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/local/share/applications/ 2>/dev/null || true
    fi
    echo "✓ Desktop entry installed"
fi

# Install icons if they exist
if [ -d "$ICON_SOURCE_DIR" ]; then
    echo "Installing icons..."
    
    # Generate PNG icons from SVG if available
    if [ -f "$ICON_SOURCE_DIR/openvpn-manager.svg" ]; then
        # Generate PNG icons in standard sizes if converter is available
        if command -v inkscape &> /dev/null; then
            for size in 16 24 32 48 64 128 256 512; do
                png_file="$ICON_SOURCE_DIR/openvpn-manager-${size}x${size}.png"
                if [ ! -f "$png_file" ]; then
                    inkscape "$ICON_SOURCE_DIR/openvpn-manager.svg" -o "$png_file" -w "$size" -h "$size" 2>/dev/null || true
                fi
            done
        elif command -v convert &> /dev/null; then
            for size in 16 24 32 48 64 128 256 512; do
                png_file="$ICON_SOURCE_DIR/openvpn-manager-${size}x${size}.png"
                if [ ! -f "$png_file" ]; then
                    convert "$ICON_SOURCE_DIR/openvpn-manager.svg" -resize "${size}x${size}" "$png_file" 2>/dev/null || true
                fi
            done
        fi
    fi
    
    # Install PNG icons in standard sizes
    for size in 16 24 32 48 64 128 256 512; do
        if [ -f "$ICON_SOURCE_DIR/openvpn-manager-${size}x${size}.png" ]; then
            mkdir -p "$ICON_DEST_DIR/${size}x${size}/apps"
            cp "$ICON_SOURCE_DIR/openvpn-manager-${size}x${size}.png" \
               "$ICON_DEST_DIR/${size}x${size}/apps/openvpn-manager.png"
        fi
    done
    
    # Install scalable SVG icon
    if [ -f "$ICON_SOURCE_DIR/openvpn-manager.svg" ]; then
        mkdir -p "$ICON_DEST_DIR/scalable/apps"
        cp "$ICON_SOURCE_DIR/openvpn-manager.svg" \
           "$ICON_DEST_DIR/scalable/apps/openvpn-manager.svg"
    fi
    
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        for theme_dir in /usr/local/share/icons/*/; do
            if [ -d "$theme_dir" ]; then
                gtk-update-icon-cache -f -t "$theme_dir" 2>/dev/null || true
            fi
        done
    fi
    echo "✓ Icons installed"
fi

echo ""
echo "Installation complete!"
echo ""
echo "You can now run OpenVPN Manager by:"
echo "  1. Typing 'openvpn-manager' in terminal"
echo "  2. Finding it in your applications menu"
echo ""

