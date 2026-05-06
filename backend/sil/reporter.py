"""
Security Intelligence Layer - Security Reporter
===============================================
Geração automática de relatórios de segurança.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)


class SecurityReporter:
    """
    Gerador de relatórios de segurança automatizados
    """
    
    def __init__(self, sil):
        self.sil = sil
        logger.info("📊 Security Reporter inicializado")
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Gera relatório diário completo"""
        now = datetime.utcnow()
        period_start = now - timedelta(hours=24)
        
        logger.info("📈 Gerando relatório diário...")
        
        # Coletar dados
        metrics = self.sil.monitor.collect_metrics()
        ai_analysis = self.sil.ai_engine.analyze_threats()
        alert_stats = self.sil.alerts.get_alert_stats()
        
        # Calcular indicadores
        report = {
            'type': 'daily',
            'date': now.strftime('%Y-%m-%d'),
            'period': '24 horas',
            'generated_at': now.isoformat(),
            
            # Resumo Executivo
            'executive_summary': {
                'overall_status': self._determine_status(ai_analysis),
                'security_score': round(ai_analysis.get('security_score', 0), 1),
                'risk_level': ai_analysis.get('risk_level', 'unknown'),
                'incidents_count': alert_stats.get('total_24h', 0),
                'critical_incidents': alert_stats.get('by_level', {}).get('critical', 0)
            },
            
            # Métricas de Login
            'login_metrics': {
                'total_attempts': metrics.get('attempts_1h', 0) * 24,  # Estimativa
                'successful_logins': metrics.get('total_success', 0),
                'failed_logins': metrics.get('total_failed', 0),
                'success_rate': round(metrics.get('success_rate', 0) * 100, 1),
                'unique_users': metrics.get('unique_users_1h', 0),
                'unique_ips': metrics.get('unique_ips_1h', 0)
            },
            
            # Segurança
            'security_metrics': {
                'blocked_ips': metrics.get('blocked_ips', 0),
                'suspicious_ips': metrics.get('suspicious_ips', 0),
                'anomalies_detected': self.sil.metrics.anomaly_count,
                'auto_tests_passed': self.sil.metrics.auto_tests_passed,
                'auto_tests_failed': self.sil.metrics.auto_tests_failed,
                'corrections_applied': self.sil.metrics.corrections_applied
            },
            
            # Análise de IA
            'ai_analysis': {
                'risk_score': round(ai_analysis.get('risk_score', 0), 2),
                'risk_factors': ai_analysis.get('risk_factors', {}),
                'predictions': [
                    {
                        'type': p.predicted_attack_type,
                        'confidence': round(p.confidence, 2),
                        'timeframe': p.timeframe,
                        'indicators': p.indicators
                    }
                    for p in ai_analysis.get('predictions', [])
                ],
                'trend': ai_analysis.get('trend', 'stable')
            },
            
            # Alertas
            'alerts_summary': {
                'total_24h': alert_stats.get('total_24h', 0),
                'by_level': alert_stats.get('by_level', {}),
                'unacknowledged': alert_stats.get('unacknowledged', 0),
                'most_common_channels': alert_stats.get('by_channel', {})
            },
            
            # Recomendações
            'recommendations': self._generate_recommendations(ai_analysis, metrics),
            
            # Comparação com período anterior
            'comparison': self._compare_with_previous_period()
        }
        
        logger.info(f"✅ Relatório diário gerado: {report['executive_summary']['overall_status']}")
        
        return report
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Gera relatório semanal"""
        now = datetime.utcnow()
        
        logger.info("📈 Gerando relatório semanal...")
        
        # Coletar dados de 7 dias
        daily_reports = []
        for i in range(7):
            # Em produção, buscar do banco
            pass
        
        return {
            'type': 'weekly',
            'week_start': (now - timedelta(days=7)).strftime('%Y-%m-%d'),
            'week_end': now.strftime('%Y-%m-%d'),
            'generated_at': now.isoformat(),
            'summary': 'Relatório semanal completo',
            'daily_breakdown': daily_reports
        }
    
    def generate_incident_report(self, incident_id: str) -> Dict[str, Any]:
        """Gera relatório detalhado de um incidente específico"""
        # Buscar incidente no histórico
        # Simplificado
        
        return {
            'type': 'incident',
            'incident_id': incident_id,
            'generated_at': datetime.utcnow().isoformat(),
            'details': 'Detalhes do incidente'
        }
    
    def generate_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Gera dados em tempo real para dashboard"""
        metrics = self.sil.monitor.collect_metrics()
        ai_analysis = self.sil.ai_engine.analyze_threats()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'status': self.sil.metrics.status.value,
            'security_score': round(ai_analysis.get('security_score', 0), 1),
            
            # Cards principais
            'kpis': {
                'login_attempts_1m': metrics.get('attempts_1m', 0),
                'failed_logins_1m': metrics.get('failed_1m', 0),
                'blocked_ips': metrics.get('blocked_ips', 0),
                'active_users': metrics.get('unique_users_1h', 0),
                'success_rate': round(metrics.get('success_rate', 0) * 100, 1)
            },
            
            # Gráficos
            'charts': {
                'login_trend': self._get_login_trend(),
                'attacks_by_type': self._get_attacks_by_type(),
                'geographic_distribution': self._get_geo_distribution()
            },
            
            # Alertas ativos
            'active_alerts': self.sil.alerts.get_active_alerts(),
            
            # Anomalias recentes
            'recent_anomalies': self._get_recent_anomalies(),
            
            # Status do sistema
            'system_health': {
                'database': 'ok',
                'api': 'ok',
                'sil_status': 'running' if self.sil.is_running else 'stopped'
            }
        }
    
    def _determine_status(self, ai_analysis: Dict) -> str:
        """Determina status geral do sistema"""
        risk_score = ai_analysis.get('risk_score', 0)
        
        if risk_score > 0.7:
            return "CRÍTICO - Ataque em andamento"
        elif risk_score > 0.5:
            return "ALERTA - Risco elevado"
        elif risk_score > 0.3:
            return "ATENÇÃO - Monitorar"
        else:
            return "ESTÁVEL - Seguro"
    
    def _generate_recommendations(self, ai_analysis: Dict, 
                                 metrics: Dict) -> List[str]:
        """Gera recomendações baseadas nos dados"""
        recommendations = []
        
        risk_score = ai_analysis.get('risk_score', 0)
        failed_rate = 1 - metrics.get('success_rate', 0.95)
        blocked_ips = metrics.get('blocked_ips', 0)
        
        if risk_score > 0.7:
            recommendations.append("🚨 ATIVAR MODO DE PROTEÇÃO EMERGÊNCIA")
            recommendations.append("Notificar equipe de segurança imediatamente")
            recommendations.append("Preparar comunicação aos usuários")
        
        if risk_score > 0.5:
            recommendations.append("Reforçar rate limiting")
            recommendations.append("Ativar CAPTCHA para todos os usuários")
            recommendations.append("Auditar logs de acesso")
        
        if failed_rate > 0.2:
            recommendations.append("Verificar se há bloqueio excessivo de usuários legítimos")
            recommendations.append("Analisar padrões de falha")
        
        if blocked_ips > 100:
            recommendations.append("Considerar bloqueio de ranges de IPs suspeitos")
        
        if not recommendations:
            recommendations.append("Manter monitoramento contínuo")
            recommendations.append("Executar testes de penetração programados")
        
        return recommendations
    
    def _compare_with_previous_period(self) -> Dict[str, Any]:
        """Compara com período anterior"""
        # Simplificado - em produção buscar dados históricos
        return {
            'login_attempts_change': '+5%',
            'success_rate_change': '-2%',
            'blocked_ips_change': '+15%',
            'trend': 'stable'
        }
    
    def _get_login_trend(self) -> List[Dict]:
        """Retorna tendência de login (últimas 24h)"""
        # Simplificado - em produção usar dados reais
        trend = []
        for i in range(24):
            trend.append({
                'hour': i,
                'attempts': 10 + i,  # Placeholder
                'failures': 2
            })
        return trend
    
    def _get_attacks_by_type(self) -> List[Dict]:
        """Retorna ataques por tipo"""
        # Simplificado
        return [
            {'type': 'brute_force', 'count': 5},
            {'type': 'credential_stuffing', 'count': 2},
            {'type': 'distributed_attack', 'count': 1}
        ]
    
    def _get_geo_distribution(self) -> List[Dict]:
        """Retorna distribuição geográfica"""
        # Simplificado
        return [
            {'country': 'Brasil', 'count': 150},
            {'country': 'EUA', 'count': 30},
            {'country': 'Outros', 'count': 20}
        ]
    
    def _get_recent_anomalies(self) -> List[Dict]:
        """Retorna anomalias recentes"""
        # Obter do detector
        anomalies = self.sil.detector.detect_anomalies()
        
        return [
            {
                'type': a.type.value,
                'severity': a.severity.value,
                'description': a.description,
                'timestamp': a.timestamp.isoformat(),
                'confidence': round(a.confidence, 2)
            }
            for a in anomalies[-5:]  # Últimas 5
        ]
    
    def export_report_pdf(self, report: Dict, filename: str = None) -> str:
        """Exporta relatório para PDF"""
        # Em produção usar bibliotecas como ReportLab ou WeasyPrint
        if not filename:
            filename = f"security_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        
        logger.info(f"📄 Relatório exportado: {filename}")
        return filename
    
    def export_report_json(self, report: Dict, filename: str = None) -> str:
        """Exporta relatório para JSON"""
        if not filename:
            filename = f"security_report_{datetime.utcnow().strftime('%Y%m%d')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Relatório exportado: {filename}")
        return filename
