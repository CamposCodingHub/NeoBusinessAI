"""
Sistema de Notificações - LexScan IA
Envio de emails para alertas de prazos
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

class NotificationManager:
    """Gerencia notificações por email"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.enabled = bool(self.smtp_username and self.smtp_password)
        
        if self.enabled:
            print(f"[NOTIFICATIONS] Email configurado: {self.smtp_username}")
        else:
            print("[NOTIFICATIONS] Email NÃO configurado. Configure SMTP_USERNAME e SMTP_PASSWORD")
    
    def test_connection(self) -> Dict:
        """Testa conexão com servidor SMTP"""
        if not self.enabled:
            return {
                'success': False,
                'error': 'Credenciais SMTP não configuradas',
                'setup_instructions': [
                    '1. Configure variáveis de ambiente:',
                    '   SMTP_SERVER=smtp.gmail.com',
                    '   SMTP_PORT=587',
                    '   SMTP_USERNAME=seu_email@gmail.com',
                    '   SMTP_PASSWORD=sua_senha_app',
                    '',
                    '2. Para Gmail, use Senha de App:',
                    '   https://myaccount.google.com/apppasswords'
                ]
            }
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                
            return {
                'success': True,
                'message': f'Conexão SMTP OK ({self.smtp_server}:{self.smtp_port})',
                'configured_email': self.smtp_username
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> Dict:
        """
        Envia email
        
        Args:
            to_email: Email do destinatário
            subject: Assunto
            html_content: Conteúdo HTML
            text_content: Conteúdo texto (opcional)
        
        Returns:
            Resultado do envio
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Sistema de email não configurado'
            }
        
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"LexScan IA <{self.smtp_username}>"
            msg['To'] = to_email
            
            # Adicionar conteúdo
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"[EMAIL] Enviado para {to_email}: {subject}")
            
            return {
                'success': True,
                'message': f'Email enviado para {to_email}',
                'subject': subject,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_deadline_alert(self, to_email: str, deadline_info: Dict, document_info: Dict) -> Dict:
        """
        Envia alerta de prazo
        
        Args:
            to_email: Email do usuário
            deadline_info: Informações do prazo
            document_info: Informações do documento
        """
        urgency = deadline_info.get('urgency', 'medium')
        days = deadline_info.get('days', '15')
        
        # Cores por urgência
        colors = {
            'high': '#ef4444',
            'medium': '#c9a227', 
            'low': '#10b981'
        }
        urgency_color = colors.get(urgency, '#c9a227')
        
        urgency_text = {
            'high': '🔴 URGENTE',
            'medium': '🟠 MÉDIO',
            'low': '🟢 BAIXO'
        }.get(urgency, 'MÉDIO')
        
        subject = f"[{urgency_text}] Prazo de {days} dias - {document_info.get('filename', 'Documento')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {urgency_color}; color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                .content {{ background: #f8fafc; padding: 20px; margin-top: 20px; border-radius: 8px; }}
                .deadline {{ background: {urgency_color}20; border-left: 4px solid {urgency_color}; padding: 15px; margin: 15px 0; }}
                .button {{ background: #1e3a5f; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 15px; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚖️ LexScan IA</h1>
                    <h2>Alerta de Prazo Processual</h2>
                </div>
                
                <div class="content">
                    <div class="deadline">
                        <h3 style="margin-top: 0; color: {urgency_color};">{urgency_text}</h3>
                        <p><strong>Prazo:</strong> {days} dias</p>
                        <p><strong>Documento:</strong> {document_info.get('filename', 'N/A')}</p>
                        <p><strong>Tipo:</strong> {document_info.get('type', 'N/A')}</p>
                        <p><strong>Nº Processo:</strong> {document_info.get('process_number', 'N/A')}</p>
                    </div>
                    
                    <h3>Contexto:</h3>
                    <p>{deadline_info.get('context', 'Verificar documento para mais detalhes.')}</p>
                    
                    <a href="http://localhost:3000/dashboard" class="button">
                        📄 Ver no Dashboard
                    </a>
                </div>
                
                <div class="footer">
                    <p>⚖️ LexScan IA - Automação Documental Jurídica</p>
                    <p>Este é um email automático. Não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
LexScan IA - Alerta de Prazo

{urgency_text}
Prazo: {days} dias
Documento: {document_info.get('filename', 'N/A')}
Tipo: {document_info.get('type', 'N/A')}
Nº Processo: {document_info.get('process_number', 'N/A')}

Contexto:
{deadline_info.get('context', 'Verificar documento para mais detalhes.')}

Acesse: http://localhost:3000/dashboard

---
LexScan IA - Automação Documental Jurídica
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def check_and_notify_deadlines(self, user_email: str, documents: List[Dict]) -> List[Dict]:
        """
        Verifica prazos e envia notificações
        
        Args:
            user_email: Email do usuário
            documents: Lista de documentos
            
        Returns:
            Lista de notificações enviadas
        """
        notifications = []
        
        for doc in documents:
            for deadline in doc.get('deadlines', []):
                # Só notificar prazos urgentes (menos de 5 dias)
                if deadline.get('urgency') == 'high':
                    result = self.send_deadline_alert(user_email, deadline, doc)
                    notifications.append({
                        'document_id': doc.get('id'),
                        'document_name': doc.get('filename'),
                        'deadline': deadline,
                        'notification': result,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return notifications


# Instância global
notification_manager = NotificationManager()


if __name__ == "__main__":
    # Teste
    print("=" * 60)
    print("TESTE SISTEMA DE NOTIFICAÇÕES")
    print("=" * 60)
    
    # Testar conexão
    test_result = notification_manager.test_connection()
    print(f"\nTeste de conexão: {'✅ SUCESSO' if test_result['success'] else '❌ FALHA'}")
    if not test_result['success']:
        print(f"Erro: {test_result.get('error')}")
        if 'setup_instructions' in test_result:
            print("\n" + "\n".join(test_result['setup_instructions']))
    else:
        print(f"Email configurado: {test_result.get('configured_email')}")
        
        # Simular envio de alerta
        print("\n📧 Simulando envio de alerta de prazo...")
        
        # Aqui você precisaria ter credenciais válidas para testar envio real
        # Por enquanto, só mostramos que o sistema está pronto
        print("Sistema pronto para enviar notificações!")
        print("Configure SMTP_USERNAME e SMTP_PASSWORD para ativar.")
