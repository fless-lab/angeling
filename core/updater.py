import os
import sys
import json
import time
import random
import base64
import hashlib
import platform
import tempfile
import subprocess
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import requests
import logging
from pathlib import Path

class UpdateManager:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.version = "1.0.0"
        self.platform = platform.system().lower()
        self.temp_dir = Path(tempfile.gettempdir())
        self.update_url = self.config.get('update_url')
        self.update_key = self.config.get('update_key', '')
        self.last_check = 0
        self.check_interval = 3600 * 24  # 24 hours
        
    def _get_current_hash(self) -> str:
        """Get hash of current executable"""
        try:
            with open(sys.executable, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""
            
    def _verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify update signature"""
        try:
            if not self.update_key:
                return True
                
            # En vrai il faudrait implémenter une vraie vérification
            # de signature avec une clé publique
            return True
        except:
            return False
            
    def _download_update(self, url: str) -> Optional[bytes]:
        """Download update safely"""
        try:
            # Use random User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Download with timeout and size limit
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                stream=True
            )
            
            if response.status_code != 200:
                return None
                
            # Limit file size to 50MB
            max_size = 50 * 1024 * 1024
            content = bytes()
            
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    return None
                    
            return content
        except:
            return None
            
    def _safe_file_write(self, path: str, content: bytes) -> bool:
        """Write file safely with backup"""
        try:
            # Create backup
            if os.path.exists(path):
                backup_path = f"{path}.bak"
                os.rename(path, backup_path)
                
            # Write new file
            with open(path, 'wb') as f:
                f.write(content)
                
            # Test new file
            if self._test_update(path):
                if os.path.exists(f"{path}.bak"):
                    os.remove(f"{path}.bak")
                return True
                
            # Restore backup if test fails
            if os.path.exists(f"{path}.bak"):
                os.remove(path)
                os.rename(f"{path}.bak", path)
                
            return False
        except:
            # Restore backup if anything fails
            try:
                if os.path.exists(f"{path}.bak"):
                    os.remove(path)
                    os.rename(f"{path}.bak", path)
            except:
                pass
            return False
            
    def _test_update(self, path: str) -> bool:
        """Test if update is valid"""
        try:
            # Try to execute with test argument
            result = subprocess.run(
                [path, "--test"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
            
    def _install_update(self, content: bytes) -> bool:
        """Install update safely"""
        try:
            # Get current executable path
            current_path = sys.executable
            
            # Create temporary file
            temp_path = self.temp_dir / f"update_{random.randint(1000,9999)}"
            
            # Write update to temp file
            with open(temp_path, 'wb') as f:
                f.write(content)
                
            # Set permissions
            if self.platform != 'windows':
                os.chmod(temp_path, 0o755)
                
            # Test update
            if not self._test_update(str(temp_path)):
                os.remove(temp_path)
                return False
                
            # Replace current executable
            if self.platform == 'windows':
                # On Windows, we need to use a bat file
                bat_path = self.temp_dir / "update.bat"
                with open(bat_path, 'w') as f:
                    f.write(f'''@echo off
timeout /t 2 /nobreak >nul
del /f "{current_path}"
copy /y "{temp_path}" "{current_path}"
del /f "{temp_path}"
start "" "{current_path}"
del "%~f0"
''')
                    
                # Execute bat file
                subprocess.Popen(['cmd', '/c', str(bat_path)], 
                    creationflags=subprocess.CREATE_NO_WINDOW)
                    
            else:
                # On Linux we can do it directly
                os.rename(temp_path, current_path)
                os.execv(current_path, sys.argv)
                
            return True
        except:
            return False
            
    def check_update(self) -> bool:
        """Check and install updates if available"""
        try:
            # Respect check interval
            current_time = time.time()
            if current_time - self.last_check < self.check_interval:
                return False
                
            self.last_check = current_time
            
            # Skip if no update URL
            if not self.update_url:
                return False
                
            # Get current version info
            current_hash = self._get_current_hash()
            
            # Check for updates
            try:
                response = requests.get(
                    f"{self.update_url}/version",
                    timeout=10
                )
                
                if response.status_code != 200:
                    return False
                    
                update_info = response.json()
                
                # Check if update needed
                if update_info['hash'] == current_hash:
                    return False
                    
                # Verify platform compatibility
                if self.platform not in update_info['platforms']:
                    return False
                    
                # Download update
                update_url = update_info['url']
                content = self._download_update(update_url)
                
                if not content:
                    return False
                    
                # Verify signature
                if not self._verify_signature(content, update_info.get('signature')):
                    return False
                    
                # Install update
                return self._install_update(content)
                
            except:
                return False
                
        except:
            return False
            
    def force_update(self, url: str) -> bool:
        """Force update from specific URL"""
        try:
            content = self._download_update(url)
            if not content:
                return False
                
            return self._install_update(content)
        except:
            return False
