# OpenVPN Linux UI

A modern GUI application for managing OpenVPN connections on Linux. This tool provides an easy-to-use interface for connecting to VPN servers, managing profiles, and monitoring connection status.

## Features

- ✅ **Connect/Disconnect VPN** - Easy one-click connection to your VPN servers
- ✅ **Profile Management** - Add, delete, and organize multiple VPN profiles
- ✅ **Status Monitoring** - Real-time connection status display
- ✅ **Modern UI** - Clean, intuitive interface built with Qt/PySide6
- ✅ **Secure** - Uses sudo for OpenVPN operations with password protection

## Technology Stack

- **Python 3** - Core programming language
- **PySide6** - Modern Qt-based GUI framework for native Linux look and feel
- **pexpect** - Handles sudo password prompts securely
- **subprocess** - Manages OpenVPN process execution

## Installation

### Prerequisites

1. **Python 3.8+** - Check with `python3 --version`
2. **OpenVPN** - Must be installed and accessible via `openvpn` command
3. **Qt/X11 system libraries** - Required for PySide6 GUI:
   ```bash
   sudo apt install libxcb-cursor0 libxcb-cursor-dev
   ```
   Or on other distributions:
   - **Fedora/RHEL**: `sudo dnf install libxcb-cursor`
   - **Arch**: `sudo pacman -S libxcb-cursor`
4. **sudo access** - Required for running OpenVPN (you may want to configure NOPASSWD for convenience)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd /home/ather/work/Projects/Personal/openvpn_linux_ui
   ```

2. **Run the setup script (recommended):**
   ```bash
   chmod +x setup.sh run.sh
   ./setup.sh
   ```
   
   This will automatically:
   - Create a Python virtual environment
   - Install all required dependencies
   - Set up everything you need

   **Or manually set up a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   
   **Note:** Modern Linux distributions (Debian/Ubuntu) protect the system Python installation. Using a virtual environment is required and recommended.

## Usage

### Running the Application

**Using the launcher script (easiest):**
```bash
./run.sh
```

**Or manually:**
```bash
source venv/bin/activate
python3 main.py
```

The launcher script automatically activates the virtual environment for you.

## Building and Installing as System Application

You can compile the application into a standalone binary and install it system-wide so it appears in your applications menu.

### Building the Binary

1. **Run the build script:**
   ```bash
   ./build.sh
   ```
   
   This will:
   - Create a standalone binary using PyInstaller
   - Bundle all dependencies
   - Create an executable in the `dist/` directory

2. **The binary will be created at:**
   ```
   dist/openvpn-manager
   ```

### Installing System-Wide

After building, install the application system-wide:

```bash
sudo ./install.sh
```

This will:
- Install the binary to `/usr/local/bin/openvpn-manager`
- Add a desktop entry so it appears in your applications menu
- Install icons for the application
- Make it accessible from anywhere via `openvpn-manager` command

### Running After Installation

Once installed, you can run OpenVPN Manager by:
- **Command line:** Simply type `openvpn-manager`
- **Applications menu:** Search for "OpenVPN Manager" in your applications launcher

### Uninstalling

To remove the system installation, use the uninstall script:

```bash
sudo ./uninstall.sh
```

This will remove:
- The binary from `/usr/local/bin/`
- The desktop entry
- All installed icons
- Update system caches

### Adding a Profile

1. Click **"Add Profile"** button
2. Enter a descriptive name for your VPN connection (e.g., "Work VPN", "Home Server")
3. Click **"Browse..."** to select your `.ovpn` config file, or enter the path manually
4. Click **"Add Profile"** to save

### Connecting to VPN

1. Select a profile from the list
2. Click **"Connect"** button
3. Enter your sudo password when prompted
4. Wait for connection to establish (status will update automatically)

You can also double-click a profile to connect quickly.

### Disconnecting

Click the **"Disconnect"** button to terminate the VPN connection.

### Deleting a Profile

1. Select the profile you want to remove
2. Click **"Delete Profile"** button
3. Confirm the deletion

**Note:** This only removes the profile from the manager. The original `.ovpn` file is not deleted.

## Configuration

### Sudo Password

The application will prompt for your sudo password each time you connect. For convenience, you can configure sudo to allow OpenVPN without a password:

1. Edit sudoers file:
   ```bash
   sudo visudo
   ```

2. Add this line (replace `yourusername` with your actual username):
   ```
   yourusername ALL=(ALL) NOPASSWD: /usr/sbin/openvpn
   ```

   Or for any location:
   ```
   yourusername ALL=(ALL) NOPASSWD: /usr/bin/openvpn, /usr/sbin/openvpn, /usr/local/bin/openvpn
   ```

3. Save and exit

**Warning:** Only do this if you trust your system security. This allows running OpenVPN without a password prompt.

### Profile Storage

Profiles are stored in `~/.openvpn_manager/profiles.json`. This file contains metadata about your profiles (names, paths, etc.). Your actual `.ovpn` config files remain in their original locations.

## Troubleshooting

### "Command not found: openvpn"

Make sure OpenVPN is installed:
```bash
which openvpn
sudo apt install openvpn  # Ubuntu/Debian
sudo yum install openvpn  # RHEL/CentOS
```

### Connection fails immediately

- Check that your `.ovpn` config file is valid
- Verify the config file path is correct
- Check system logs: `journalctl -xe`
- Try running the OpenVPN command manually to see error messages:
  ```bash
  sudo openvpn --config /path/to/your/config.ovpn
  ```

### Permission denied errors

- Ensure you have sudo access
- Check that the OpenVPN binary is accessible
- Verify file permissions on your `.ovpn` config file

### Application won't start

- Verify all dependencies are installed: `pip3 list | grep -i pyside`
- Check Python version: `python3 --version` (needs 3.8+)
- Check for error messages in terminal

### Qt platform plugin errors (xcb-cursor0)

If you see errors like:
```
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed
Could not load the Qt platform plugin "xcb"
```

Install the missing system libraries:
```bash
sudo apt install libxcb-cursor0 libxcb-cursor-dev
```

This is a system-level dependency required for Qt/PySide6 to work with X11.

## Project Structure

```
openvpn_linux_ui/
├── main.py                    # Main GUI application
├── openvpn_manager.py         # OpenVPN connection and profile management
├── requirements.txt           # Python dependencies (runtime)
├── requirements-build.txt     # Build dependencies (includes PyInstaller)
├── setup.sh                   # Setup script (creates venv and installs deps)
├── run.sh                     # Launcher script (activates venv and runs app)
├── build.sh                   # Build script (creates standalone binary)
├── install.sh                 # Installation script (installs to system)
├── uninstall.sh               # Uninstall script (removes system installation)
├── openvpn-manager.desktop    # Desktop entry file
├── icons/                     # Application icons
│   └── openvpn-manager.svg    # SVG icon
├── dist/                      # Build output directory (created by build.sh)
├── build/                     # PyInstaller build files (created by build.sh)
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## Development

### Running from source

```bash
python3 main.py
```

### Dependencies

**Runtime dependencies:**
- `PySide6>=6.6.0` - Qt GUI framework
- `pexpect>=4.9.0` - Terminal interaction for password prompts

**Build dependencies (for creating binary):**
- `PyInstaller>=6.0.0` - For creating standalone executables

**System dependencies:**
- `libxcb-cursor0` - Qt/X11 library (see Prerequisites)
- `openvpn` - OpenVPN binary

## License

This project is open source. Feel free to modify and distribute as needed.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

