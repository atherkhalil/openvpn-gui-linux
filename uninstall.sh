#!/bin/bash
# Uninstall script for OpenVPN Manager

set -e

echo "Uninstalling OpenVPN Manager..."

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script requires sudo privileges."
    echo "Please run: sudo ./uninstall.sh"
    exit 1
fi

# Remove binary
if [ -f "/usr/local/bin/openvpn-manager" ]; then
    echo "Removing binary..."
    rm -f /usr/local/bin/openvpn-manager
    echo "✓ Binary removed"
fi

# Remove desktop entry
if [ -f "/usr/local/share/applications/openvpn-manager.desktop" ]; then
    echo "Removing desktop entry..."
    rm -f /usr/local/share/applications/openvpn-manager.desktop
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/local/share/applications/ 2>/dev/null || true
    fi
    echo "✓ Desktop entry removed"
fi

# Remove icons
ICON_REMOVED=false
for size_dir in /usr/local/share/icons/hicolor/*/apps/; do
    if [ -f "${size_dir}openvpn-manager.png" ]; then
        rm -f "${size_dir}openvpn-manager.png"
        ICON_REMOVED=true
    fi
    if [ -f "${size_dir}openvpn-manager.svg" ]; then
        rm -f "${size_dir}openvpn-manager.svg"
        ICON_REMOVED=true
    fi
done

if [ "$ICON_REMOVED" = true ]; then
    # Update icon cache
    if command -v gtk-update-icon-cache &> /dev/null; then
        for theme_dir in /usr/local/share/icons/*/; do
            if [ -d "$theme_dir" ]; then
                gtk-update-icon-cache -f -t "$theme_dir" 2>/dev/null || true
            fi
        done
    fi
    echo "✓ Icons removed"
fi

echo ""
echo "Uninstallation complete!"
echo ""

