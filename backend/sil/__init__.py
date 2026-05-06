"""
Security Intelligence Layer (SIL)
==================================
Sistema de auto-auditoria contínua em tempo real para segurança enterprise.

Módulos:
- monitor: Monitoramento contínuo de login e atividades
- detector: Detecção de anomalias e ataques
- autotest: Auto-testes periódicos de segurança
- ai_engine: IA interna de análise de segurança
- dashboard: API do painel de segurança
- alerts: Sistema de alertas
- autocorrect: Auto-correção de falhas
- simulator: Simulação de ataques controlada
- reporter: Geração de relatórios automáticos

Uso:
    from sil import SecurityIntelligenceLayer
    sil = SecurityIntelligenceLayer()
    sil.start_monitoring()
"""

from .core import SecurityIntelligenceLayer
from .monitor import LoginMonitor
from .detector import AnomalyDetector
from .autotest import SecurityAutoTester
from .ai_engine import SecurityAI
from .alerts import AlertManager
from .reporter import SecurityReporter

__version__ = "1.0.0"
__author__ = "NeoBusiness AI Security Team"

__all__ = [
    "SecurityIntelligenceLayer",
    "LoginMonitor", 
    "AnomalyDetector",
    "SecurityAutoTester",
    "SecurityAI",
    "AlertManager",
    "SecurityReporter",
]
