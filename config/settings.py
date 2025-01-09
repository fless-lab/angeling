"""
Configuration globale pour le framework Angeling
"""

import os
from typing import Dict, Any

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Créer les répertoires nécessaires
for directory in [TEMP_DIR, BACKUP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configuration de la résilience
RESILIENCE_CONFIG: Dict[str, Any] = {
    'backup_interval': 3600,  # 1 heure
    'max_retries': 3,
    'retry_delay': 5,
    'error_thresholds': {
        'LOW': 10,
        'MEDIUM': 5,
        'HIGH': 3,
        'FATAL': 1
    }
}

# Configuration de la furtivité
STEALTH_CONFIG: Dict[str, Any] = {
    'check_interval': 60,
    'sandbox_sleep': 1000,
    'debug_sleep': 500,
    'vm_sleep': 1500
}

# Configuration réseau
NETWORK_CONFIG: Dict[str, Any] = {
    'max_connections': 100,
    'timeout': 30,
    'retry_interval': 5,
    'chunk_size': 8192
}

# Configuration de la persistance
PERSISTENCE_CONFIG: Dict[str, Any] = {
    'check_interval': 300,
    'backup_count': 5,
    'methods': [
        'registry',
        'startup',
        'service',
        'scheduled_task',
        'wmi',
        'dll_hijack'
    ]
}

# Configuration du cerveau
BRAIN_CONFIG: Dict[str, Any] = {
    'learning_rate': 0.01,
    'memory_size': 1000,
    'decision_threshold': 0.7
}

# Configuration de l'obfuscation
OBFUSCATION_CONFIG: Dict[str, Any] = {
    'enabled': True,
    'complexity': 3,
    'layers': [
        'rename',
        'flow_control',
        'string_encode',
        'dead_code'
    ]
}

# Configuration de la collecte
COLLECTOR_CONFIG: Dict[str, Any] = {
    'max_size': 1024 * 1024 * 10,  # 10MB
    'interval': 300,
    'types': [
        'system',
        'browser',
        'files',
        'network'
    ]
}

# Configuration du routage
ROUTER_CONFIG: Dict[str, Any] = {
    'max_routes': 10,
    'timeout': 30,
    'retry_count': 3
}

# Configuration globale
GLOBAL_CONFIG: Dict[str, Any] = {
    'debug': False,
    'version': '2.0.0',
    'beacon_interval': 300,
    'max_memory': 1024 * 1024 * 100,  # 100MB
    'resilience': RESILIENCE_CONFIG,
    'stealth': STEALTH_CONFIG,
    'network': NETWORK_CONFIG,
    'persistence': PERSISTENCE_CONFIG,
    'brain': BRAIN_CONFIG,
    'obfuscation': OBFUSCATION_CONFIG,
    'collector': COLLECTOR_CONFIG,
    'router': ROUTER_CONFIG
}
