import pytest
import os
import sys
import time
from core.integrator import SystemIntegrator
from core.resilience import ErrorCategory, ErrorSeverity

class TestIntegration:
    @pytest.fixture
    def integrator(self):
        return SystemIntegrator()
        
    def test_initialization(self, integrator):
        """Test l'initialisation de tous les composants"""
        assert integrator.initialize() == True
        
    def test_error_handling(self, integrator):
        """Test la gestion des erreurs"""
        # Simule une erreur réseau
        try:
            raise ConnectionError("Test network error")
        except Exception as e:
            integrator.resilience.handle_error(e, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM)
            
        # Vérifie que l'erreur a été enregistrée
        cursor = integrator.resilience.conn.cursor()
        cursor.execute("SELECT * FROM error_history WHERE category = ?", ("NETWORK",))
        errors = cursor.fetchall()
        assert len(errors) > 0
        
    def test_data_collection(self, integrator):
        """Test la collecte de données"""
        data = integrator.collect_data('system')
        assert data is not None
        assert isinstance(data, dict)
        
    def test_command_execution(self, integrator):
        """Test l'exécution de commandes"""
        result = integrator.execute_command('test', {'param': 'value'})
        assert result is not None
        
    def test_stealth(self, integrator):
        """Test les mécanismes de furtivité"""
        assert integrator.stealth.check_environment() in [True, False]
        
    def test_persistence(self, integrator):
        """Test les mécanismes de persistance"""
        methods = integrator.persistence.list_methods()
        assert len(methods) > 0
        
    def test_network_operations(self, integrator):
        """Test les opérations réseau"""
        interfaces = integrator.network.get_interfaces()
        assert isinstance(interfaces, list)
        
    def test_brain_analysis(self, integrator):
        """Test l'analyse du cerveau"""
        result = integrator.brain.analyze_environment()
        assert isinstance(result, dict)
        
    def test_obfuscation(self, integrator):
        """Test l'obfuscation"""
        test_code = "print('test')"
        result = integrator.obfuscator.obfuscate(test_code)
        assert isinstance(result, str)
        assert result != test_code
        
    def test_resilience_recovery(self, integrator):
        """Test la récupération après erreur"""
        # Simule une erreur fatale
        try:
            raise MemoryError("Test memory error")
        except Exception as e:
            integrator.resilience.handle_error(e, ErrorCategory.MEMORY, ErrorSeverity.FATAL)
            
        # Vérifie que le système se rétablit
        time.sleep(2)
        assert integrator.initialize() == True
        
    def test_backup_restore(self, integrator):
        """Test la sauvegarde et restauration"""
        # Force une sauvegarde
        integrator.resilience._perform_backup()
        
        # Vérifie que le backup existe
        backup_dir = os.path.join(os.path.dirname(integrator.resilience.conn.path), 'backups')
        assert os.path.exists(backup_dir)
        assert len(os.listdir(backup_dir)) > 0
        
    @pytest.mark.cleanup
    def test_cleanup(self, integrator):
        """Test le nettoyage final"""
        integrator.shutdown()
        assert not integrator.resilience.is_running
