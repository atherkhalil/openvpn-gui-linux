#!/usr/bin/env python3
"""
OpenVPN Linux UI - Main GUI Application
"""

import sys
import os
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox,
    QDialog, QLineEdit, QFileDialog, QStatusBar, QFrame, QTextEdit,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from openvpn_manager import OpenVPNManager


# Modern light mode color scheme
COLORS = {
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F5F5F5',
    'bg_tertiary': '#EEEEEE',
    'text_primary': '#212121',
    'text_secondary': '#757575',
    'accent': '#2196F3',
    'accent_hover': '#1976D2',
    'success': '#4CAF50',
    'success_hover': '#45a049',
    'danger': '#F44336',
    'danger_hover': '#D32F2F',
    'border': '#E0E0E0',
    'shadow': 'rgba(0, 0, 0, 0.1)',
}


def apply_modern_style(app):
    """Apply modern light mode styling to the application"""
    style = f"""
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-size: 12pt;
    }}
    
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}
    
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px;
    }}
    
    QListWidget {{
        background-color: {COLORS['bg_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px;
        font-size: 12pt;
        selection-background-color: {COLORS['accent']};
        selection-color: white;
    }}
    
    QListWidget::item {{
        padding: 10px;
        border-radius: 6px;
        margin: 2px;
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['bg_tertiary']};
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    
    QPushButton {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 12pt;
        font-weight: 600;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['bg_tertiary']};
        border-color: {COLORS['accent']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['border']};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_secondary']};
        border-color: {COLORS['border']};
    }}
    
    QPushButton[class="connect"] {{
        background-color: {COLORS['success']};
        color: white;
        border-color: {COLORS['success']};
    }}
    
    QPushButton[class="connect"]:hover {{
        background-color: {COLORS['success_hover']};
        border-color: {COLORS['success_hover']};
    }}
    
    QPushButton[class="disconnect"] {{
        background-color: {COLORS['danger']};
        color: white;
        border-color: {COLORS['danger']};
    }}
    
    QPushButton[class="disconnect"]:hover {{
        background-color: {COLORS['danger_hover']};
        border-color: {COLORS['danger_hover']};
    }}
    
    QPushButton[class="logs"] {{
        background-color: {COLORS['accent']};
        color: white;
        border-color: {COLORS['accent']};
    }}
    
    QPushButton[class="logs"]:hover {{
        background-color: {COLORS['accent_hover']};
        border-color: {COLORS['accent_hover']};
    }}
    
    QLineEdit {{
        background-color: {COLORS['bg_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 6px;
        padding: 10px;
        font-size: 12pt;
        selection-background-color: {COLORS['accent']};
    }}
    
    QLineEdit:focus {{
        border-color: {COLORS['accent']};
    }}
    
    QTextEdit {{
        background-color: {COLORS['bg_primary']};
        border: 2px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px;
        font-family: 'Monospace', 'Courier New', monospace;
        font-size: 11pt;
        color: {COLORS['text_primary']};
    }}
    
    QDialog {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QStatusBar {{
        background-color: {COLORS['bg_secondary']};
        border-top: 1px solid {COLORS['border']};
    }}
    """
    app.setStyleSheet(style)


class AddProfileDialog(QDialog):
    """Dialog for adding a new OpenVPN profile"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add OpenVPN Profile")
        self.setMinimumWidth(600)
        self.setMinimumHeight(200)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Profile name
        name_label = QLabel("Profile Name:")
        name_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My VPN Server")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)
        
        # Config file path
        path_label = QLabel("Config File:")
        path_label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/path/to/config.ovpn")
        self.path_input.setMinimumHeight(40)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumWidth(100)
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add Profile")
        add_btn.setDefault(True)
        add_btn.setMinimumHeight(40)
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(self.accept)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file dialog to select .ovpn file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenVPN Config File",
            os.path.expanduser("~"),
            "OpenVPN Config Files (*.ovpn);;All Files (*)"
        )
        if file_path:
            self.path_input.setText(file_path)
            # Auto-fill name if empty
            if not self.name_input.text():
                name = Path(file_path).stem
                self.name_input.setText(name)
    
    def get_profile_data(self):
        """Get the profile name and path from the dialog"""
        return {
            "name": self.name_input.text().strip(),
            "path": self.path_input.text().strip()
        }


class PasswordDialog(QDialog):
    """Dialog for entering sudo password"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sudo Password Required")
        self.setMinimumWidth(400)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        label = QLabel("Enter your sudo password:")
        label.setFont(QFont("", 12, QFont.Bold))
        layout.addWidget(label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.setMinimumHeight(40)
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_password(self):
        """Get the entered password"""
        return self.password_input.text()


class LogsDialog(QDialog):
    """Dialog for displaying OpenVPN connection logs"""
    
    def __init__(self, manager: OpenVPNManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("OpenVPN Connection Logs")
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Connection Logs")
        header_font = QFont("", 14, QFont.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(36)
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Timer to update logs
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_logs)
        self.update_timer.start(500)  # Update every 500ms
    
    def update_logs(self):
        """Update the log display"""
        if not self.manager.is_connected():
            return
        
        logs = self.manager.get_logs()
        if logs:
            text = "\n".join(logs)
            current_text = self.log_text.toPlainText()
            if current_text != text:
                self.log_text.setPlainText(text)
                # Auto-scroll to bottom
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.clear()
    
    def closeEvent(self, event):
        """Stop timer when dialog closes"""
        self.update_timer.stop()
        super().closeEvent(event)


class OpenVPNMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.manager = OpenVPNManager()
        self.password = None
        self.logs_dialog: Optional[LogsDialog] = None
        
        self.setWindowTitle("OpenVPN Connection Manager")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        central_widget.setLayout(main_layout)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(20)
        
        # Load and display icon
        icon_path = Path(__file__).parent / "icons" / "openvpn-manager.svg"
        if not icon_path.exists():
            # Try alternative path (for when running from different directory)
            icon_path = Path(os.path.dirname(os.path.abspath(__file__))) / "icons" / "openvpn-manager.svg"
        
        if icon_path.exists():
            try:
                # Create SVG renderer
                svg_renderer = QSvgRenderer(str(icon_path))
                if svg_renderer.isValid():
                    # Create pixmap for the icon (larger size to match title)
                    icon_size = 48
                    icon_pixmap = QPixmap(icon_size, icon_size)
                    icon_pixmap.fill(Qt.transparent)
                    # Render SVG to pixmap
                    painter = QPainter(icon_pixmap)
                    painter.setRenderHint(QPainter.Antialiasing)
                    svg_renderer.render(painter)
                    painter.end()
                    
                    # Create label for icon
                    icon_label = QLabel()
                    icon_label.setPixmap(icon_pixmap)
                    icon_label.setAlignment(Qt.AlignCenter)
                    icon_label.setStyleSheet("background-color: transparent;")
                    title_layout.addWidget(icon_label)
            except Exception as e:
                # If SVG loading fails, just skip the icon
                print(f"Could not load icon: {e}")
        
        # Title text
        title = QLabel("OpenVPN Connection Manager")
        title_font = QFont("", 30, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 10px;")
        title_layout.addWidget(title)
        
        # Add title layout to main layout
        title_widget = QWidget()
        title_widget.setLayout(title_layout)
        main_layout.addWidget(title_widget)
        
        # Status frame
        status_frame = QFrame()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_frame.setLayout(status_layout)
        
        status_label_text = QLabel("Status:")
        status_label_text.setFont(QFont("", 14, QFont.Bold))
        status_layout.addWidget(status_label_text)
        
        self.status_label = QLabel("Disconnected")
        status_font = QFont("", 14, QFont.Bold)
        self.status_label.setFont(status_font)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        main_layout.addWidget(status_frame)
        
        # Profile list
        # list_label = QLabel("VPN Profiles:")
        # list_label.setFont(QFont("", 14, QFont.Bold))
        # main_layout.addWidget(list_label)
        
        self.profile_list = QListWidget() # TODO: Add label to the profile list
        # self.profile_list_label = QLabel("VPN Profiles")
        # self.profile_list_label.setFont(QFont("", 14, QFont.Bold))
        # self.profile_list_label.setAlignment(Qt.AlignCenter)
        # self.profile_list_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        # self.profile_list.setPlaceholderWidget(self.profile_list_label)
        # self.profile_list_scroll_area = QScrollArea()
        # self.profile_list_scroll_area.setWidget(self.profile_list)
        # self.profile_list_scroll_area.setWidgetResizable(True)
        # self.profile_list_scroll_area.setFixedHeight(300)
        self.profile_list.setMinimumHeight(400)
        # make the font bigger
        self.profile_list.setFont(QFont("", 40, QFont.Bold))
        # self.profile_list.setStyleSheet(f"color: {COLORS['text_primary']};")
        # self.profile_list.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        # self.profile_list.setStyleSheet(f"border: 2px solid {COLORS['border']};")
        # self.profile_list.setStyleSheet(f"border-radius: 8px;")
        # self.profile_list.setStyleSheet(f"padding: 12px;")
        # self.profile_list.setStyleSheet(f"margin: 12px;")
        # self.profile_list.setStyleSheet(f"font-size: 14pt;")
        self.profile_list.itemDoubleClicked.connect(self.on_profile_double_clicked)
        main_layout.addWidget(self.profile_list)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.add_btn = QPushButton("Add Profile")
        self.add_btn.setMinimumHeight(44)
        self.add_btn.clicked.connect(self.add_profile)
        button_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("Delete Profile")
        self.delete_btn.setMinimumHeight(44)
        self.delete_btn.clicked.connect(self.delete_profile)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.logs_btn = QPushButton("View Logs")
        self.logs_btn.setProperty("class", "logs")
        self.logs_btn.setMinimumHeight(44)
        self.logs_btn.setMinimumWidth(120)
        self.logs_btn.clicked.connect(self.toggle_logs)
        self.logs_btn.setEnabled(False)
        button_layout.addWidget(self.logs_btn)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setProperty("class", "connect")
        self.connect_btn.setMinimumHeight(44)
        self.connect_btn.setMinimumWidth(120)
        self.connect_btn.clicked.connect(self.connect_vpn)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setProperty("class", "disconnect")
        self.disconnect_btn.setMinimumHeight(44)
        self.disconnect_btn.setMinimumWidth(120)
        self.disconnect_btn.clicked.connect(self.disconnect_vpn)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Timer to update connection status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Update every 2 seconds
        
        # Timer to periodically check for IP (in case interface takes time to initialize)
        self.ip_check_timer = QTimer()
        self.ip_check_timer.timeout.connect(self.check_ip)
        self.ip_check_timer.start(3000)  # Check every 3 seconds
        
        # Load profiles
        self.refresh_profiles()
        self.update_status()
    
    def refresh_profiles(self):
        """Refresh the profile list"""
        self.profile_list.clear()
        profiles = self.manager.get_profiles()
        
        for profile in profiles:
            profile_name = profile["name"]
            vpn_ip = profile.get("vpn_ip")
            
            # Create display text with VPN IP if available
            if vpn_ip:
                display_text = f"{profile_name} • {vpn_ip}"
            else:
                display_text = profile_name
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, profile_name)
            self.profile_list.addItem(item)
    
    def add_profile(self):
        """Open dialog to add a new profile"""
        dialog = AddProfileDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_profile_data()
            
            if not data["name"]:
                QMessageBox.warning(self, "Error", "Please enter a profile name.")
                return
            
            if not data["path"]:
                QMessageBox.warning(self, "Error", "Please select a config file.")
                return
            
            if self.manager.add_profile(data["name"], data["path"]):
                self.refresh_profiles()
                self.statusBar().showMessage(f"Profile '{data['name']}' added successfully", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to add profile. Check if the config file exists.")
    
    def delete_profile(self):
        """Delete the selected profile"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a profile to delete.")
            return
        
        profile_name = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.manager.remove_profile(profile_name):
                self.refresh_profiles()
                self.statusBar().showMessage(f"Profile '{profile_name}' deleted", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to delete profile.")
    
    def on_profile_double_clicked(self, item):
        """Handle double-click on profile item"""
        if not self.manager.is_connected():
            self.connect_vpn()
    
    def toggle_logs(self):
        """Toggle logs dialog visibility"""
        if self.logs_dialog is None or not self.logs_dialog.isVisible():
            if self.logs_dialog is None:
                self.logs_dialog = LogsDialog(self.manager, self)
            self.logs_dialog.show()
            self.logs_dialog.raise_()
            self.logs_dialog.activateWindow()
        else:
            self.logs_dialog.hide()
    
    def connect_vpn(self):
        """Connect to the selected VPN profile"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a profile to connect.")
            return
        
        profile_name = current_item.data(Qt.UserRole)
        
        # Check if already connected
        if self.manager.is_connected():
            QMessageBox.warning(self, "Error", "Already connected. Please disconnect first.")
            return
        
        # Get password if needed
        if not self.password:
            password_dialog = PasswordDialog(self)
            if password_dialog.exec() == QDialog.Accepted:
                self.password = password_dialog.get_password()
            else:
                return
        
        # Connect
        success, message = self.manager.connect(profile_name, self.password)
        
        if success:
            self.statusBar().showMessage(message, 3000)
            # Start fetching public IP in background
            self.manager.get_public_ip()
            self.update_ui_state()
        else:
            QMessageBox.warning(self, "Connection Error", message)
            self.password = None  # Reset password on failure
    
    def disconnect_vpn(self):
        """Disconnect from VPN"""
        # Close logs dialog if open
        if self.logs_dialog and self.logs_dialog.isVisible():
            self.logs_dialog.close()
        
        success, message = self.manager.disconnect()
        
        if success:
            self.statusBar().showMessage(message, 3000)
            self.password = None  # Clear password after disconnect
        else:
            QMessageBox.warning(self, "Disconnect Error", message)
        
        self.update_ui_state()
    
    def update_status(self):
        """Update connection status display"""
        is_connected, profile_name = self.manager.get_connection_status()
        
        if is_connected:
            # Get public IP from icanhazip.com
            public_ip = self.manager.get_public_ip()
            status_text = f"Connected to {profile_name}"
            if public_ip:
                status_text += f" • Public IP: {public_ip}"
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.update_ui_state()
    
    def check_ip(self):
        """Periodically check for VPN IP address and public IP"""
        if self.manager.is_connected():
            # This will trigger IP lookup if not already found
            self.manager.get_connection_ip()
            # Get public IP
            self.manager.get_public_ip()
            # Update status to show IP if found
            self.update_status()
    
    def update_ui_state(self):
        """Update UI button states based on connection status"""
        is_connected = self.manager.is_connected()
        
        self.connect_btn.setEnabled(not is_connected)
        self.disconnect_btn.setEnabled(is_connected)
        self.logs_btn.setEnabled(is_connected)
        self.add_btn.setEnabled(not is_connected)
        self.delete_btn.setEnabled(not is_connected)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    apply_modern_style(app)
    
    window = OpenVPNMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
