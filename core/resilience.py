import os
import sys
import time
import random
import logging
import threading
import traceback
import socket
import sqlite3
import json
import queue
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum, auto
import psutil

class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = auto()      # Erreur mineure, peut continuer
    MEDIUM = auto()   # Erreur significative, nécessite une attention
    HIGH = auto()     # Erreur critique, nécessite une récupération
    FATAL = auto()    # Erreur fatale, nécessite un redémarrage

class ErrorCategory(Enum):
    """Catégories d'erreurs pour le traitement approprié"""
    NETWORK = auto()      # Erreurs réseau
    FILESYSTEM = auto()   # Erreurs système de fichiers
    MEMORY = auto()       # Erreurs de mémoire
    PROCESS = auto()      # Erreurs de processus
    RESOURCE = auto()     # Erreurs de ressources
    SECURITY = auto()     # Erreurs de sécurité
    DATABASE = auto()     # Erreurs de base de données
    UNKNOWN = auto()      # Erreurs inconnues

class ResilienceManager:
    def __init__(self):
        self.logger = logging.getLogger('ResilienceManager')
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {cat: [] for cat in ErrorCategory}
        self.error_history: List[Dict] = []
        self.recovery_queue = queue.PriorityQueue()
        self.monitoring_thread = None
        self.backup_thread = None
        self.is_running = False
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.FATAL: 1
        }
        self.last_backup = datetime.now()
        self.backup_interval = timedelta(hours=1)
        
        # Initialize la base de données de résilience
        self._init_resilience_db()
        
    def _init_resilience_db(self):
        """Initialise la base de données pour stocker l'historique et les métriques"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'resilience.db')
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Table pour l'historique des erreurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    category TEXT,
                    severity TEXT,
                    error_msg TEXT,
                    stack_trace TEXT,
                    resolution TEXT
                )
            ''')
            
            # Table pour les métriques de résilience
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resilience_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    metric_type TEXT,
                    metric_value REAL,
                    details TEXT
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize resilience database: {str(e)}")
            
    def start_monitoring(self):
        """Démarre les threads de surveillance et de backup"""
        self.is_running = True
        
        # Thread de surveillance principal
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Thread de backup
        self.backup_thread = threading.Thread(target=self._backup_loop)
        self.backup_thread.daemon = True
        self.backup_thread.start()
        
    def stop_monitoring(self):
        """Arrête les threads de surveillance"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        if self.backup_thread:
            self.backup_thread.join()
            
    def _monitoring_loop(self):
        """Boucle principale de surveillance"""
        while self.is_running:
            try:
                # Vérifie les ressources système
                self._check_system_resources()
                
                # Traite les erreurs en attente
                self._process_recovery_queue()
                
                # Analyse les tendances d'erreurs
                self._analyze_error_patterns()
                
                # Attend un intervalle aléatoire
                time.sleep(random.uniform(5, 15))
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                
    def _backup_loop(self):
        """Boucle de backup des données critiques"""
        while self.is_running:
            try:
                if datetime.now() - self.last_backup >= self.backup_interval:
                    self._perform_backup()
                    self.last_backup = datetime.now()
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"Backup loop error: {str(e)}")
                
    def _check_system_resources(self):
        """Vérifie l'état des ressources système"""
        try:
            # Vérification CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.handle_error(
                    Exception("High CPU usage detected"),
                    ErrorCategory.RESOURCE,
                    ErrorSeverity.MEDIUM
                )
                
            # Vérification mémoire
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.handle_error(
                    Exception("High memory usage detected"),
                    ErrorCategory.MEMORY,
                    ErrorSeverity.MEDIUM
                )
                
            # Vérification disque
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.handle_error(
                    Exception("Low disk space detected"),
                    ErrorCategory.RESOURCE,
                    ErrorSeverity.HIGH
                )
                
            # Vérification réseau
            net_connections = psutil.net_connections()
            if len(net_connections) > 1000:
                self.handle_error(
                    Exception("Too many network connections"),
                    ErrorCategory.NETWORK,
                    ErrorSeverity.MEDIUM
                )
                
        except Exception as e:
            self.logger.error(f"Resource check failed: {str(e)}")
            
    def _process_recovery_queue(self):
        """Traite la file d'attente de récupération"""
        while not self.recovery_queue.empty():
            try:
                priority, error_info = self.recovery_queue.get_nowait()
                
                # Applique la stratégie de récupération appropriée
                category = error_info['category']
                if category == ErrorCategory.NETWORK:
                    self._recover_network(error_info)
                elif category == ErrorCategory.FILESYSTEM:
                    self._recover_filesystem(error_info)
                elif category == ErrorCategory.PROCESS:
                    self._recover_process(error_info)
                elif category == ErrorCategory.MEMORY:
                    self._recover_memory(error_info)
                    
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Recovery processing failed: {str(e)}")
                
    def _analyze_error_patterns(self):
        """Analyse les tendances dans l'historique des erreurs"""
        try:
            cursor = self.conn.cursor()
            
            # Analyse par catégorie
            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM error_history
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY category
            ''')
            
            category_counts = cursor.fetchall()
            for category, count in category_counts:
                if count > 10:  # Seuil d'alerte
                    self.logger.warning(f"High error rate detected for category {category}: {count} errors/hour")
                    
            # Analyse par sévérité
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM error_history
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY severity
            ''')
            
            severity_counts = cursor.fetchall()
            for severity, count in severity_counts:
                threshold = self.error_thresholds.get(ErrorSeverity[severity], 5)
                if count > threshold:
                    self.logger.warning(f"Error threshold exceeded for severity {severity}: {count} errors/hour")
                    
        except Exception as e:
            self.logger.error(f"Error pattern analysis failed: {str(e)}")
            
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    severity: ErrorSeverity, retry_count: int = 0):
        """Gère une erreur avec récupération appropriée"""
        try:
            # Log l'erreur
            error_info = {
                'timestamp': datetime.now().isoformat(),
                'category': category.name,
                'severity': severity.name,
                'error_msg': str(error),
                'stack_trace': traceback.format_exc(),
                'retry_count': retry_count
            }
            
            # Stocke dans la base de données
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO error_history 
                (timestamp, category, severity, error_msg, stack_trace)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                error_info['timestamp'],
                error_info['category'],
                error_info['severity'],
                error_info['error_msg'],
                error_info['stack_trace']
            ))
            self.conn.commit()
            
            # Ajoute à la file de récupération avec priorité basée sur la sévérité
            priority = {
                ErrorSeverity.LOW: 3,
                ErrorSeverity.MEDIUM: 2,
                ErrorSeverity.HIGH: 1,
                ErrorSeverity.FATAL: 0
            }[severity]
            
            self.recovery_queue.put((priority, error_info))
            
            # Exécute les handlers spécifiques à la catégorie
            for handler in self.error_handlers.get(category, []):
                try:
                    handler(error_info)
                except Exception as e:
                    self.logger.error(f"Error handler failed: {str(e)}")
                    
            # Vérifie si un redémarrage est nécessaire
            if severity == ErrorSeverity.FATAL:
                self._handle_fatal_error(error_info)
                
        except Exception as e:
            self.logger.error(f"Error handling failed: {str(e)}")
            
    def register_error_handler(self, category: ErrorCategory, 
                             handler: Callable[[Dict], None]):
        """Enregistre un gestionnaire d'erreur pour une catégorie spécifique"""
        if category in self.error_handlers:
            self.error_handlers[category].append(handler)
            
    def _recover_network(self, error_info: Dict):
        """Récupération des erreurs réseau"""
        try:
            # Réinitialise les connexions
            for conn in socket.socket(socket.AF_INET, socket.SOCK_STREAM):
                try:
                    conn.close()
                except:
                    pass
                    
            # Attend avant de réessayer
            time.sleep(random.uniform(1, 5))
            
            # Met à jour le statut de récupération
            self._update_recovery_status(error_info['id'], "Network recovery completed")
            
        except Exception as e:
            self.logger.error(f"Network recovery failed: {str(e)}")
            
    def _recover_filesystem(self, error_info: Dict):
        """Récupération des erreurs système de fichiers"""
        try:
            # Vérifie et répare les permissions
            affected_path = error_info.get('path')
            if affected_path and os.path.exists(affected_path):
                try:
                    os.chmod(affected_path, 0o755)
                except:
                    pass
                    
            # Nettoie les fichiers temporaires si nécessaire
            temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
            if os.path.exists(temp_dir):
                try:
                    for file in os.listdir(temp_dir):
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except:
                            pass
                except:
                    pass
                    
            self._update_recovery_status(error_info['id'], "Filesystem recovery completed")
            
        except Exception as e:
            self.logger.error(f"Filesystem recovery failed: {str(e)}")
            
    def _recover_process(self, error_info: Dict):
        """Récupération des erreurs de processus"""
        try:
            # Nettoie les ressources
            for handler in self.error_handlers.get(ErrorCategory.PROCESS, []):
                try:
                    handler(error_info)
                except:
                    pass
                    
            # Redémarre le processus si nécessaire
            if error_info.get('severity') == ErrorSeverity.HIGH.name:
                self._restart_process()
                
            self._update_recovery_status(error_info['id'], "Process recovery completed")
            
        except Exception as e:
            self.logger.error(f"Process recovery failed: {str(e)}")
            
    def _recover_memory(self, error_info: Dict):
        """Récupération des erreurs de mémoire"""
        try:
            # Force le garbage collector
            import gc
            gc.collect()
            
            # Libère la mémoire si possible
            if hasattr(sys, 'set_memory_limit'):
                sys.set_memory_limit(sys.maxsize)
                
            self._update_recovery_status(error_info['id'], "Memory recovery completed")
            
        except Exception as e:
            self.logger.error(f"Memory recovery failed: {str(e)}")
            
    def _handle_fatal_error(self, error_info: Dict):
        """Gestion des erreurs fatales"""
        try:
            # Sauvegarde l'état
            self._perform_backup()
            
            # Log l'erreur fatale
            self.logger.critical(f"Fatal error encountered: {error_info['error_msg']}")
            
            # Tente de redémarrer proprement
            self._restart_process()
            
        except Exception as e:
            self.logger.error(f"Fatal error handling failed: {str(e)}")
            sys.exit(1)
            
    def _perform_backup(self):
        """Effectue une sauvegarde des données critiques"""
        try:
            # Sauvegarde la base de données
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'resilience_{timestamp}.db')
            
            # Copie la base de données
            with self.conn:
                backup = sqlite3.connect(backup_path)
                self.conn.backup(backup)
                backup.close()
                
            # Nettoie les vieux backups
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            
    def _cleanup_old_backups(self, backup_dir: str):
        """Nettoie les anciennes sauvegardes"""
        try:
            # Garde seulement les 5 derniers backups
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('resilience_')],
                reverse=True
            )
            
            for old_backup in backups[5:]:
                try:
                    os.remove(os.path.join(backup_dir, old_backup))
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
            
    def _update_recovery_status(self, error_id: int, resolution: str):
        """Met à jour le statut de récupération dans la base de données"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE error_history
                SET resolution = ?
                WHERE id = ?
            ''', (resolution, error_id))
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update recovery status: {str(e)}")
            
    def _restart_process(self):
        """Redémarre le processus de manière contrôlée"""
        try:
            # Sauvegarde l'état
            self._perform_backup()
            
            # Ferme proprement les ressources
            self.stop_monitoring()
            self.conn.close()
            
            # Redémarre le processus
            python = sys.executable
            os.execl(python, python, *sys.argv)
            
        except Exception as e:
            self.logger.error(f"Process restart failed: {str(e)}")
            sys.exit(1)  # Force exit if restart fails
