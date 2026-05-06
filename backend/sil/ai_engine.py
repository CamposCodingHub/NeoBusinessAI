"""
Security Intelligence Layer - Security AI Engine
=================================================
Inteligência Artificial interna para análise de ameaças e previsões.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class ThreatPrediction:
    """Previsão de ameaça"""
    risk_score: float  # 0.0 a 1.0
    predicted_attack_type: str
    confidence: float
    timeframe: str  # "next_hour", "next_day", "next_week"
    indicators: List[str]
    recommended_actions: List[str]


class SecurityAI:
    """
    IA de segurança para análise preditiva e comportamental
    """
    
    def __init__(self, sil):
        self.sil = sil
        
        # Modelos de ML simplificados (em produção usar sklearn/tensorflow)
        self._risk_weights = {
            'failed_login_rate': 0.25,
            'unique_ips': 0.15,
            'geographic_anomaly': 0.20,
            'time_anomaly': 0.15,
            'device_anomaly': 0.15,
            'behavior_change': 0.10
        }
        
        # Baselines comportamentais por usuário
        self._user_baselines: Dict[str, Dict] = {}
        
        # Histórico de ameaças para aprendizado
        self._threat_history: List[Dict] = []
        
        logger.info("🧠 Security AI Engine inicializada")
    
    def analyze_threats(self) -> Dict[str, Any]:
        """Analisa ameaças atuais e prevê riscos futuros"""
        # Coletar dados
        metrics = self.sil.monitor.collect_metrics()
        
        # Calcular scores de risco
        risk_factors = self._calculate_risk_factors(metrics)
        
        # Calcular score geral
        total_risk = sum(
            risk_factors.get(factor, 0) * weight
            for factor, weight in self._risk_weights.items()
        )
        
        # Gerar previsões
        predictions = self._generate_predictions(total_risk, risk_factors)
        
        return {
            'risk_score': min(total_risk, 1.0),
            'risk_level': self._risk_level(total_risk),
            'risk_factors': risk_factors,
            'predictions': predictions,
            'trend': self._calculate_trend(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def calculate_security_score(self) -> float:
        """Calcula score de segurança geral (0-10)"""
        metrics = self.sil.monitor.collect_metrics()
        
        # Fatores positivos (aumentam score)
        success_rate = metrics.get('success_rate', 0.95)
        blocked_threats = metrics.get('blocked_ips', 0)
        
        # Fatores negativos (diminuem score)
        failed_rate = 1 - success_rate
        anomaly_count = self.sil.metrics.anomaly_count
        
        # Cálculo ponderado
        score = 10.0
        score -= failed_rate * 5  # Até -5 pontos por alta taxa de falha
        score -= min(anomaly_count / 10, 3)  # Até -3 por anomalias
        score += min(blocked_threats / 10, 2)  # Até +2 por ameaças bloqueadas
        
        return max(0, min(10, score))
    
    def _calculate_risk_factors(self, metrics: Dict) -> Dict[str, float]:
        """Calcula fatores individuais de risco"""
        factors = {}
        
        # 1. Taxa de falha de login
        attempts = metrics.get('attempts_1m', 1)
        failed = metrics.get('failed_1m', 0)
        failure_rate = failed / max(attempts, 1)
        factors['failed_login_rate'] = min(failure_rate * 2, 1.0)  # Normalizar
        
        # 2. Múltiplos IPs
        unique_ips = metrics.get('unique_ips_1h', 0)
        factors['unique_ips'] = min(unique_ips / 100, 1.0)
        
        # 3. Anomalias geográficas (placeholder)
        factors['geographic_anomaly'] = 0.0
        
        # 4. Anomalias de horário
        factors['time_anomaly'] = self._detect_time_anomalies()
        
        # 5. Anomalias de dispositivo
        factors['device_anomaly'] = 0.0
        
        # 6. Mudança comportamental
        factors['behavior_change'] = self._detect_behavior_changes()
        
        return factors
    
    def _detect_time_anomalies(self) -> float:
        """Detecta anomalias baseadas em horários de login"""
        recent_attempts = list(self.sil.monitor._attempts_1h)
        if not recent_attempts:
            return 0.0
        
        # Extrair horas
        hours = [a.timestamp.hour for a in recent_attempts]
        
        # Verificar se a maioria está em horário incomum (2-6 da manhã)
        unusual_hours = sum(1 for h in hours if 2 <= h <= 6)
        unusual_rate = unusual_hours / len(hours)
        
        return unusual_rate
    
    def _detect_behavior_changes(self) -> float:
        """Detecta mudanças abruptas no comportamento de usuários"""
        # Analisar usuários ativos
        recent_attempts = list(self.sil.monitor._attempts_1h)
        users = set(a.email for a in recent_attempts)
        
        behavior_scores = []
        
        for user in users:
            user_attempts = [a for a in recent_attempts if a.email == user]
            if len(user_attempts) < 2:
                continue
            
            # Verificar dispositivos diferentes
            devices = set(a.device_fingerprint for a in user_attempts if a.device_fingerprint)
            if len(devices) > 2:
                behavior_scores.append(0.7)  # Alto risco
            elif len(devices) > 1:
                behavior_scores.append(0.4)  # Médio risco
        
        return max(behavior_scores) if behavior_scores else 0.0
    
    def _generate_predictions(self, total_risk: float, 
                             risk_factors: Dict) -> List[ThreatPrediction]:
        """Gera previsões de ameaças"""
        predictions = []
        
        # Previsão 1: Ataque iminente
        if total_risk > 0.7:
            predictions.append(ThreatPrediction(
                risk_score=total_risk,
                predicted_attack_type="brute_force_or_distributed",
                confidence=0.8,
                timeframe="next_hour",
                indicators=[
                    f"Taxa de falha elevada: {risk_factors.get('failed_login_rate', 0):.1%}",
                    "Múltiplos IPs detectados",
                    "Padrão consistente de ataque"
                ],
                recommended_actions=[
                    "Ativar rate limiting agressivo",
                    "Preparar CAPTCHA",
                    "Notificar equipe de segurança"
                ]
            ))
        
        # Previsão 2: Credential stuffing
        if risk_factors.get('failed_login_rate', 0) > 0.5 and risk_factors.get('unique_ips', 0) > 0.3:
            predictions.append(ThreatPrediction(
                risk_score=0.6,
                predicted_attack_type="credential_stuffing",
                confidence=0.7,
                timeframe="next_hour",
                indicators=[
                    "Muitas falhas de múltiplos IPs",
                    "Padrão de senhas vazadas"
                ],
                recommended_actions=[
                    "Verificar credenciais vazadas",
                    "Forçar 2FA",
                    "Notificar usuários"
                ]
            ))
        
        # Previsão 3: Account takeover
        if risk_factors.get('behavior_change', 0) > 0.5:
            predictions.append(ThreatPrediction(
                risk_score=0.75,
                predicted_attack_type="account_takeover",
                confidence=0.65,
                timeframe="next_day",
                indicators=[
                    "Múltiplos dispositivos detectados",
                    "Mudança comportamental"
                ],
                recommended_actions=[
                    "Verificar identidade do usuário",
                    "Solicitar verificação adicional",
                    "Monitorar atividades"
                ]
            ))
        
        return predictions
    
    def _risk_level(self, score: float) -> str:
        """Converte score numérico em nível de risco"""
        if score < 0.3:
            return "low"
        elif score < 0.5:
            return "medium"
        elif score < 0.7:
            return "high"
        else:
            return "critical"
    
    def _calculate_trend(self) -> str:
        """Calcula tendência de segurança"""
        # Comparar com dados históricos
        # Simplificado - em produção usar séries temporais
        return "stable"
    
    def analyze_user_risk(self, email: str) -> Dict[str, Any]:
        """Analisa risco específico de um usuário"""
        patterns = self.sil.monitor.get_login_patterns(email, hours=168)  # 7 dias
        
        if patterns.get('status') != 'ok':
            return {'risk': 'unknown', 'score': 0.5}
        
        risk_factors = []
        risk_score = 0.0
        
        # Falhas recentes
        if patterns.get('failures', 0) > patterns.get('success', 0):
            risk_factors.append("Mais falhas que sucessos")
            risk_score += 0.3
        
        # Múltiplos IPs
        if patterns.get('unique_ips', 0) > 3:
            risk_factors.append("IPs múltiplos")
            risk_score += 0.2
        
        # Múltiplos dispositivos
        if patterns.get('unique_devices', 0) > 2:
            risk_factors.append("Múltiplos dispositivos")
            risk_score += 0.2
        
        # Múltiplos países
        if patterns.get('unique_countries', 0) > 1:
            risk_factors.append("Múltiplos países")
            risk_score += 0.3
        
        return {
            'email': email,
            'risk_score': min(risk_score, 1.0),
            'risk_level': self._risk_level(risk_score),
            'factors': risk_factors,
            'patterns': patterns,
            'recommendations': self._generate_user_recommendations(risk_score, risk_factors)
        }
    
    def _generate_user_recommendations(self, risk_score: float, 
                                     factors: List[str]) -> List[str]:
        """Gera recomendações para usuário específico"""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("Forçar alteração de senha no próximo login")
            recommendations.append("Ativar 2FA obrigatório")
        
        if "Múltiplos países" in factors:
            recommendations.append("Verificar viagens recentes")
        
        if "Múltiplos dispositivos" in factors:
            recommendations.append("Revisar dispositivos autorizados")
        
        if not recommendations:
            recommendations.append("Manter monitoramento")
        
        return recommendations
    
    def learn_from_incident(self, incident: Dict):
        """Aprende com incidentes para melhorar detecção"""
        self._threat_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': incident.get('type'),
            'severity': incident.get('severity'),
            'outcome': incident.get('outcome'),
            'data': incident
        })
        
        # Limitar histórico
        if len(self._threat_history) > 1000:
            self._threat_history = self._threat_history[-1000:]
        
        logger.info(f"🧠 Aprendizado: Incidente {incident.get('type')} registrado")
    
    def get_security_insights(self) -> Dict[str, Any]:
        """Retorna insights de segurança baseados em análise"""
        metrics = self.sil.monitor.collect_metrics()
        
        # Calcular estatísticas
        attempts_1h = metrics.get('attempts_1h', 0)
        success_rate = metrics.get('success_rate', 0)
        
        insights = []
        
        # Insight 1: Volume de tentativas
        if attempts_1h > 1000:
            insights.append({
                'type': 'warning',
                'message': f'Volume alto de tentativas: {attempts_1h}/hora',
                'recommendation': 'Investigar possível ataque distribuído'
            })
        
        # Insight 2: Taxa de sucesso
        if success_rate < 0.8:
            insights.append({
                'type': 'alert',
                'message': f'Taxa de sucesso baixa: {success_rate:.1%}',
                'recommendation': 'Verificar se há bloqueio excessivo'
            })
        
        # Insight 3: IPs bloqueados
        blocked = metrics.get('blocked_ips', 0)
        if blocked > 50:
            insights.append({
                'type': 'info',
                'message': f'{blocked} IPs bloqueados ativamente',
                'recommendation': 'Sistema de proteção funcionando'
            })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'insights': insights,
            'overall_assessment': 'Seguro' if success_rate > 0.9 and attempts_1h < 500 else 'Atenção'
        }
