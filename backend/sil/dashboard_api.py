"""
Security Intelligence Layer - Dashboard API
===========================================
API REST para o dashboard de segurança em tempo real.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from database import get_db
from security import require_role, Role
from .core import get_sil

router = APIRouter(prefix="/sil", tags=["Security Intelligence Layer"])
security = HTTPBearer()


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get("/status")
async def get_security_status():
    """Retorna status atual da segurança"""
    sil = get_sil()
    
    return {
        'system_status': 'operational' if sil.is_running else 'stopped',
        'security_score': sil.metrics.security_score,
        'status': sil.metrics.status.value,
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'monitor': 'active',
            'detector': 'active',
            'ai_engine': 'active',
            'autotest': 'active'
        }
    }


@router.get("/metrics")
async def get_realtime_metrics():
    """Retorna métricas em tempo real"""
    sil = get_sil()
    
    return sil.get_current_metrics()


@router.get("/dashboard")
async def get_dashboard_data():
    """Retorna dados completos do dashboard"""
    sil = get_sil()
    
    return sil.reporter.generate_realtime_dashboard_data()


# ==================== ENDPOINTS DE MONITORAMENTO ====================

@router.get("/monitor/logins")
async def get_login_statistics(
    hours: int = 24,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna estatísticas de login"""
    sil = get_sil()
    
    return {
        'period_hours': hours,
        'metrics': sil.monitor.collect_metrics(),
        'blocked_ips': sil.monitor.get_blocked_ips(),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/monitor/users/{email}/patterns")
async def get_user_login_patterns(
    email: str,
    hours: int = 24,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna padrões de login de usuário específico"""
    sil = get_sil()
    
    return sil.monitor.get_login_patterns(email, hours)


@router.post("/monitor/unblock-ip/{ip}")
async def unblock_ip(
    ip: str,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Desbloqueia um IP manualmente"""
    sil = get_sil()
    
    success = sil.monitor.unblock_ip(ip)
    
    if success:
        return {
            'success': True,
            'message': f'IP {ip} desbloqueado',
            'unblocked_by': admin_user.get('email'),
            'timestamp': datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="IP não encontrado ou já desbloqueado")


# ==================== ENDPOINTS DE ANÁLISE ====================

@router.get("/analysis/threats")
async def get_threat_analysis(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna análise de ameaças da IA"""
    sil = get_sil()
    
    return sil.ai_engine.analyze_threats()


@router.get("/analysis/user/{email}/risk")
async def get_user_risk_analysis(
    email: str,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna análise de risco de usuário"""
    sil = get_sil()
    
    return sil.ai_engine.analyze_user_risk(email)


@router.get("/analysis/insights")
async def get_security_insights(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna insights de segurança"""
    sil = get_sil()
    
    return sil.ai_engine.get_security_insights()


# ==================== ENDPOINTS DE ALERTAS ====================

@router.get("/alerts")
async def get_alerts(
    level: Optional[str] = None,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna alertas de segurança"""
    sil = get_sil()
    
    return {
        'alerts': sil.alerts.get_active_alerts(level),
        'stats': sil.alerts.get_alert_stats(),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Marca alerta como reconhecido"""
    sil = get_sil()
    
    success = sil.alerts.acknowledge_alert(alert_id, admin_user.get('email'))
    
    if success:
        return {
            'success': True,
            'message': f'Alerta {alert_id} reconhecido',
            'acknowledged_by': admin_user.get('email'),
            'timestamp': datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")


# ==================== ENDPOINTS DE SIMULAÇÃO ====================

@router.post("/simulations/run/{attack_type}")
async def run_attack_simulation(
    attack_type: str,
    background_tasks: BackgroundTasks,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Executa simulação de ataque (apenas admin)"""
    sil = get_sil()
    
    # Executar em background para não bloquear
    background_tasks.add_task(sil.run_simulation, attack_type)
    
    return {
        'success': True,
        'message': f'Simulação {attack_type} iniciada em background',
        'attack_type': attack_type,
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/simulations/status")
async def get_simulation_status(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna status do simulador"""
    sil = get_sil()
    
    return sil.simulator.get_simulation_status()


# ==================== ENDPOINTS DE RELATÓRIOS ====================

@router.get("/reports/daily")
async def get_daily_report(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna relatório diário"""
    sil = get_sil()
    
    return sil.reporter.generate_daily_report()


@router.get("/reports/weekly")
async def get_weekly_report(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna relatório semanal"""
    sil = get_sil()
    
    return sil.reporter.generate_weekly_report()


@router.post("/reports/export/{format}")
async def export_report(
    format: str,  # json ou pdf
    report_type: str = "daily",
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Exporta relatório"""
    sil = get_sil()
    
    # Gerar relatório
    if report_type == "daily":
        report = sil.reporter.generate_daily_report()
    else:
        report = sil.reporter.generate_weekly_report()
    
    # Exportar
    if format == "json":
        filename = sil.reporter.export_report_json(report)
    elif format == "pdf":
        filename = sil.reporter.export_report_pdf(report)
    else:
        raise HTTPException(status_code=400, detail="Formato deve ser 'json' ou 'pdf'")
    
    return {
        'success': True,
        'filename': filename,
        'format': format,
        'timestamp': datetime.utcnow().isoformat()
    }


# ==================== ENDPOINTS DE CONTROLE ====================

@router.post("/control/emergency-lockdown")
async def activate_emergency_lockdown(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Ativa lockdown de emergência"""
    sil = get_sil()
    
    sil.autocorrect.emergency_lockdown()
    
    return {
        'success': True,
        'message': 'Lockdown de emergência ativado',
        'activated_by': admin_user.get('email'),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.post("/control/disable-emergency")
async def disable_emergency_mode(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Desativa modo de emergência"""
    sil = get_sil()
    
    sil.autocorrect.disable_emergency_mode()
    
    return {
        'success': True,
        'message': 'Modo de emergência desativado',
        'deactivated_by': admin_user.get('email'),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.post("/control/run-autotest")
async def run_autotest(
    background_tasks: BackgroundTasks,
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Executa auto-testes manualmente"""
    sil = get_sil()
    
    background_tasks.add_task(sil.autotest.run_all_tests)
    
    return {
        'success': True,
        'message': 'Auto-testes iniciados em background',
        'timestamp': datetime.utcnow().isoformat()
    }


# ==================== ENDPOINTS DE CONFIGURAÇÃO ====================

@router.get("/config")
async def get_sil_config(
    admin_user = Depends(require_role(Role.ADMIN))
):
    """Retorna configurações atuais do SIL"""
    sil = get_sil()
    
    return {
        'is_running': sil.is_running,
        'metrics_interval': 5,
        'detection_interval': 10,
        'ai_analysis_interval': 60,
        'autotest_interval': 3600,
        'reporting_interval': 86400,
        'emergency_mode': sil.autocorrect._emergency_mode,
        'corrections_applied': sil.autocorrect._corrections_applied
    }
