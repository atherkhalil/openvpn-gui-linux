#!/usr/bin/env python3
"""
OpenVPN Manager - GUI application for managing OpenVPN connections on Linux
"""

import os
import subprocess
import signal
import time
import pexpect
import threading
import re
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import deque
import json


class OpenVPNManager:
    """Manages OpenVPN connections and profiles"""
    
    def __init__(self, profiles_dir: str = None):
        """
        Initialize the OpenVPN manager
        
        Args:
            profiles_dir: Directory to store profile metadata (default: ~/.openvpn_manager)
        """
        if profiles_dir is None:
            profiles_dir = os.path.expanduser("~/.openvpn_manager")
        
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.profiles_file = self.profiles_dir / "profiles.json"
        self.current_process: Optional[subprocess.Popen] = None
        self.current_profile: Optional[str] = None
        self.logs: deque = deque(maxlen=1000)  # Store last 1000 log lines
        self.log_lock = threading.Lock()
        self.log_thread: Optional[threading.Thread] = None
        self.connection_ip: Optional[str] = None  # VPN IP address
        self.public_ip: Optional[str] = None  # Public IP address
        
        # Load existing profiles
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict[str, Dict]:
        """Load profiles from JSON file"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_profiles(self):
        """Save profiles to JSON file"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def add_profile(self, name: str, config_path: str) -> bool:
        """
        Add a new OpenVPN profile
        
        Args:
            name: Profile name
            config_path: Path to .ovpn config file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(config_path):
            return False
        
        # Extract VPN server IP/address from config
        vpn_ip = self._extract_vpn_ip_from_config(config_path)
        
        self.profiles[name] = {
            "name": name,
            "config_path": config_path,
            "vpn_ip": vpn_ip,
            "created_at": str(Path(config_path).stat().st_mtime)
        }
        self._save_profiles()
        return True
    
    def _extract_vpn_ip_from_config(self, config_path: str) -> Optional[str]:
        """
        Extract VPN server IP/address from .ovpn config file
        
        Args:
            config_path: Path to .ovpn config file
            
        Returns:
            VPN server IP/address or None
        """
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Look for 'remote' directive (most common)
            # Format: remote <host> <port> [proto]
            remote_match = re.search(r'^\s*remote\s+(\S+)', content, re.MULTILINE)
            if remote_match:
                host = remote_match.group(1)
                # Check if it's an IP address or hostname
                ip_match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$', host)
                if ip_match:
                    return ip_match.group(1)
                else:
                    # It's a hostname, try to resolve it
                    try:
                        import socket
                        ip = socket.gethostbyname(host)
                        return ip
                    except:
                        return host  # Return hostname if can't resolve
            
            # Look for 'remote-random-hostname' or other remote directives
            # Some configs might have multiple remotes
            remote_hostname_match = re.search(r'remote\s+([a-zA-Z0-9.-]+)', content, re.IGNORECASE)
            if remote_hostname_match:
                host = remote_hostname_match.group(1)
                try:
                    import socket
                    ip = socket.gethostbyname(host)
                    return ip
                except:
                    return host
            
        except Exception:
            pass
        
        return None
    
    def remove_profile(self, name: str) -> bool:
        """
        Remove a profile
        
        Args:
            name: Profile name
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles()
            return True
        return False
    
    def get_profiles(self) -> List[Dict]:
        """Get list of all profiles"""
        # Ensure all profiles have VPN IP extracted
        for name, profile in self.profiles.items():
            if 'vpn_ip' not in profile or not profile.get('vpn_ip'):
                vpn_ip = self._extract_vpn_ip_from_config(profile['config_path'])
                if vpn_ip:
                    profile['vpn_ip'] = vpn_ip
                    self._save_profiles()
        return list(self.profiles.values())
    
    def connect(self, profile_name: str, password: str = None) -> Tuple[bool, str]:
        """
        Connect to OpenVPN using a profile
        
        Args:
            profile_name: Name of the profile to connect
            password: Sudo password (if None, will prompt)
            
        Returns:
            Tuple of (success, message)
        """
        if self.is_connected():
            return False, "Already connected. Please disconnect first."
        
        if profile_name not in self.profiles:
            return False, f"Profile '{profile_name}' not found."
        
        config_path = self.profiles[profile_name]["config_path"]
        
        if not os.path.exists(config_path):
            return False, f"Config file not found: {config_path}"
        
        try:
            # Build the command
            cmd = ["sudo", "openvpn", "--config", config_path]
            
            if password:
                # Use pexpect to handle sudo password prompt
                child = pexpect.spawn(" ".join(cmd), encoding='utf-8', timeout=30)
                
                # Handle password prompt
                index = child.expect(['password', 'Password', '[sudo]', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
                
                if index < 3:  # Password prompt detected
                    child.sendline(password)
                    # Wait a moment to see if authentication succeeds
                    try:
                        child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=2)
                    except:
                        pass
                    
                    # Check if child process is still alive (auth might have succeeded)
                    if child.isalive():
                        # Process started successfully, let it run
                        # Clear previous logs
                        with self.log_lock:
                            self.logs.clear()
                        
                        # Start log reading thread for pexpect
                        self.current_process = child
                        self.log_thread = threading.Thread(target=self._read_logs_pexpect, daemon=True)
                        self.log_thread.start()
                        self.current_profile = profile_name
                        return True, f"Connecting to {profile_name}..."
                    else:
                        # Process died, likely authentication failed
                        child.close()
                        return False, "Authentication failed. Please check your password."
                else:
                    # No password prompt, might have NOPASSWD configured
                    child.close()
            
            # Try without password or use subprocess if pexpect didn't work
            # Start the process in background using subprocess
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr into stdout
                universal_newlines=True,
                bufsize=1,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Clear previous logs
            with self.log_lock:
                self.logs.clear()
            
            # Start log reading thread
            self.log_thread = threading.Thread(target=self._read_logs, daemon=True)
            self.log_thread.start()
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if process is still running (if it died immediately, there was an error)
            if self.current_process.poll() is not None:
                # Process died, get error message
                error_msg = "Process exited immediately"
                if self.logs:
                    with self.log_lock:
                        error_msg = "\n".join(list(self.logs)[-5:])
                self.current_process = None
                self.log_thread = None
                return False, f"Failed to start OpenVPN: {error_msg[:200]}"
            
            self.current_profile = profile_name
            return True, f"Connecting to {profile_name}..."
            
        except pexpect.exceptions.TIMEOUT:
            return False, "Connection timeout. Please check your password and try again."
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def disconnect(self) -> Tuple[bool, str]:
        """
        Disconnect from OpenVPN
        
        Returns:
            Tuple of (success, message)
        """
        if not self.is_connected():
            return False, "Not connected"
        
        try:
            # Kill the process
            if self.current_process:
                # Handle pexpect spawn objects
                if hasattr(self.current_process, 'terminate'):
                    # subprocess.Popen
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                        self.current_process.wait(timeout=5)
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        # Process already dead or won't terminate
                        try:
                            os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                else:
                    # pexpect spawn object
                    try:
                        self.current_process.terminate(force=True)
                        self.current_process.wait()
                    except:
                        pass
                
                self.current_process = None
                self.current_profile = None
                self.log_thread = None
                self.connection_ip = None
                
                # Also kill any remaining openvpn processes
                subprocess.run(["sudo", "pkill", "openvpn"], 
                             capture_output=True, timeout=5)
                
                return True, "Disconnected successfully"
        except Exception as e:
            # Fallback: kill all openvpn processes
            try:
                subprocess.run(["sudo", "pkill", "-9", "openvpn"], 
                             capture_output=True, timeout=5)
            except:
                pass
            self.current_process = None
            self.current_profile = None
            self.log_thread = None
            self.connection_ip = None
            return True, "Disconnected (force)"
    
    def is_connected(self) -> bool:
        """Check if currently connected to VPN"""
        if self.current_process is None:
            return False
        
        # Check if process is still running
        # For pexpect spawn objects, use isalive()
        if hasattr(self.current_process, 'isalive'):
            if not self.current_process.isalive():
                self.current_process = None
                self.current_profile = None
                self.connection_ip = None
                return False
        elif hasattr(self.current_process, 'poll'):
            # subprocess.Popen object
            if self.current_process.poll() is not None:
                self.current_process = None
                self.current_profile = None
                self.connection_ip = None
                return False
        
        return True
    
    def get_connection_status(self) -> Tuple[bool, Optional[str]]:
        """
        Get current connection status
        
        Returns:
            Tuple of (is_connected, profile_name or None)
        """
        if self.is_connected():
            return True, self.current_profile
        return False, None
    
    def _read_logs(self):
        """Read logs from subprocess.Popen stdout"""
        if not self.current_process:
            return
        
        try:
            for line in iter(self.current_process.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                if line:
                    with self.log_lock:
                        self.logs.append(line)
                    # Extract IP from logs
                    self._extract_ip_from_log(line)
        except Exception:
            pass
    
    def _read_logs_pexpect(self):
        """Read logs from pexpect spawn object"""
        if not self.current_process:
            return
        
        try:
            buffer = ""
            while self.current_process and self.current_process.isalive():
                try:
                    # Read available data
                    try:
                        data = self.current_process.read_nonblocking(size=4096, timeout=0.1)
                        buffer += data
                    except pexpect.exceptions.TIMEOUT:
                        # No data available, process any buffered lines
                        if buffer:
                            lines = buffer.splitlines(keepends=True)
                            buffer = lines[-1] if lines else ""
                            for line in lines[:-1]:
                                line = line.rstrip()
                                if line:
                                    with self.log_lock:
                                        self.logs.append(line)
                                    self._extract_ip_from_log(line)
                        continue
                    except pexpect.exceptions.EOF:
                        # Process remaining buffer
                        if buffer:
                            for line in buffer.splitlines():
                                line = line.rstrip()
                                if line:
                                    with self.log_lock:
                                        self.logs.append(line)
                                    self._extract_ip_from_log(line)
                        break
                    
                    # Process complete lines from buffer
                    while '\n' in buffer or '\r\n' in buffer:
                        if '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                        elif '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                        else:
                            break
                        
                        line = line.rstrip()
                        if line:
                            with self.log_lock:
                                self.logs.append(line)
                            self._extract_ip_from_log(line)
                            
                except Exception as e:
                    # If read_nonblocking fails, try alternative approach
                    try:
                        index = self.current_process.expect([pexpect.EOF, pexpect.TIMEOUT, '.+'], timeout=0.5)
                        if index == 0:  # EOF
                            break
                        elif index == 2:  # Got output
                            line = self.current_process.before
                            if line and line.strip():
                                line = line.strip()
                                with self.log_lock:
                                    self.logs.append(line)
                                self._extract_ip_from_log(line)
                    except:
                        continue
        except Exception:
            pass
    
    def get_logs(self) -> List[str]:
        """
        Get current logs
        
        Returns:
            List of log lines
        """
        with self.log_lock:
            return list(self.logs)
    
    def _extract_ip_from_log(self, line: str):
        """Extract IP address from OpenVPN log line or network interface"""
        # Check if connection is established
        if "Initialization Sequence Completed" in line or "TUN/TAP device" in line:
            # Try to get IP from tun/tap interface
            self._get_vpn_ip_from_interface()
        elif "Peer Connection Initiated" in line:
            # Connection starting, will get IP when established
            pass
    
    def _get_vpn_ip_from_interface(self):
        """Get VPN IP address from network interface"""
        try:
            # Try to find tun or tap interface
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                current_iface = None
                for iface_line in result.stdout.split('\n'):
                    # Check for interface name (tun or tap)
                    if_match = re.match(r'^\d+:\s+(\w+):', iface_line)
                    if if_match:
                        iface_name = if_match.group(1)
                        if 'tun' in iface_name or 'tap' in iface_name:
                            current_iface = iface_name
                    # Check for IP on current interface
                    if current_iface:
                        ip_match = re.search(r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', iface_line)
                        if ip_match:
                            self.connection_ip = ip_match.group(1)
                            break
        except Exception:
            pass
    
    def get_public_ip(self) -> Optional[str]:
        """
        Get public IP address from icanhazip.com
        
        Returns:
            Public IP address string or None
        """
        try:
            with urllib.request.urlopen('https://icanhazip.com', timeout=5) as response:
                ip = response.read().decode('utf-8').strip()
                # Validate it's an IP address
                if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                    self.public_ip = ip
                    return ip
        except Exception:
            pass
        return self.public_ip
    
    def get_connection_ip(self) -> Optional[str]:
        """
        Get the VPN IP address
        
        Returns:
            IP address string or None
        """
        # Update IP if connected
        if self.is_connected() and not self.connection_ip:
            self._get_vpn_ip_from_interface()
        return self.connection_ip
    
    def get_profile_vpn_ip(self, profile_name: str) -> Optional[str]:
        """
        Get the VPN server IP for a profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            VPN server IP or None
        """
        if profile_name in self.profiles:
            return self.profiles[profile_name].get('vpn_ip')
        return None

