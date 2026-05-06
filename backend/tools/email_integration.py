"""
Sistema de Integração com Email Corporativo - LexScan IA
IMAP/SMTP integration for corporate email processing
"""

import os
import re
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup

from ai.groq_client import GroqClient
from tools.security import encrypt_credential, decrypt_credential


@dataclass
class EmailAccount:
    """Configuração de conta de email"""
    id: int
    user_id: int
    email_address: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    username: str
    password: str  # Encriptado
    provider: str  # 'gmail', 'outlook', 'corporate', 'other'
    is_active: bool = True
    last_sync: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class EmailMessage:
    """Representa um email processado"""
    id: str
    account_id: int
    message_id: str
    subject: str
    sender: str
    sender_name: str
    recipients: List[str]
    date: datetime
    body_text: str
    body_html: str
    is_read: bool
    is_important: bool = False
    is_flagged: bool = False
    attachments: List[Dict] = None
    summary: str = ""
    urgency_score: float = 0.0  # 0.0 a 1.0
    action_items: List[str] = None
    category: str = "other"  # 'legal', 'client', 'internal', 'spam', 'other'
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'subject': self.subject,
            'sender': self.sender,
            'sender_name': self.sender_name,
            'date': self.date.isoformat() if self.date else None,
            'body_preview': self.body_text[:200] + "..." if len(self.body_text) > 200 else self.body_text,
            'summary': self.summary,
            'urgency_score': self.urgency_score,
            'is_important': self.is_important,
            'is_read': self.is_read,
            'category': self.category,
            'action_items': self.action_items or []
        }


class EmailIntegrationManager:
    """Gerenciador de integração com email corporativo"""
    
    PROVIDER_SETTINGS = {
        'gmail': {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'auth_method': 'oauth2_or_password'
        },
        'outlook': {
            'imap_server': 'outlook.office365.com',
            'imap_port': 993,
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587,
            'auth_method': 'oauth2_or_password'
        },
        'yahoo': {
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587,
            'auth_method': 'password'
        },
        'icloud': {
            'imap_server': 'imap.mail.me.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.me.com',
            'smtp_port': 587,
            'auth_method': 'password'
        }
    }
    
    def __init__(self):
        self.groq = GroqClient()
        self.current_connections: Dict[int, imaplib.IMAP4_SSL] = {}
    
    def detect_provider(self, email_address: str) -> str:
        """Detecta o provedor baseado no domínio"""
        domain = email_address.split('@')[1].lower()
        
        provider_map = {
            'gmail.com': 'gmail',
            'googlemail.com': 'gmail',
            'outlook.com': 'outlook',
            'hotmail.com': 'outlook',
            'live.com': 'outlook',
            'msn.com': 'outlook',
            'office365.com': 'outlook',
            'yahoo.com': 'yahoo',
            'ymail.com': 'yahoo',
            'icloud.com': 'icloud',
            'me.com': 'icloud',
            'mac.com': 'icloud'
        }
        
        return provider_map.get(domain, 'corporate')
    
    def get_provider_settings(self, provider: str) -> Dict:
        """Retorna configurações do provedor"""
        return self.PROVIDER_SETTINGS.get(provider, {
            'imap_server': '',
            'imap_port': 993,
            'smtp_server': '',
            'smtp_port': 587,
            'auth_method': 'password'
        })
    
    def test_connection(self, account: EmailAccount) -> Tuple[bool, str]:
        """Testa a conexão IMAP"""
        try:
            # SECURITY: Decrypt password before using
            decrypted_password = decrypt_credential(account.password)
            
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.username, decrypted_password)
            mail.select('INBOX')
            mail.close()
            mail.logout()
            return True, "Conexão estabelecida com sucesso!"
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            if 'AUTHENTICATIONFAILED' in error_msg:
                return False, "Autenticação falhou. Verifique usuário e senha."
            elif 'Invalid credentials' in error_msg:
                return False, "Credenciais inválidas."
            else:
                return False, f"Erro de conexão: {error_msg}"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def connect(self, account: EmailAccount) -> imaplib.IMAP4_SSL:
        """Estabelece conexão IMAP"""
        if account.id in self.current_connections:
            try:
                self.current_connections[account.id].noop()
                return self.current_connections[account.id]
            except:
                pass
        
        # SECURITY: Decrypt password before using
        decrypted_password = decrypt_credential(account.password)
        
        mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
        mail.login(account.username, decrypted_password)
        self.current_connections[account.id] = mail
        return mail
    
    def disconnect(self, account_id: int):
        """Fecha conexão IMAP"""
        if account_id in self.current_connections:
            try:
                self.current_connections[account_id].close()
                self.current_connections[account_id].logout()
            except:
                pass
            del self.current_connections[account_id]
    
    def fetch_emails(
        self, 
        account: EmailAccount, 
        folder: str = 'INBOX',
        limit: int = 50,
        since: Optional[datetime] = None,
        unread_only: bool = False
    ) -> List[EmailMessage]:
        """Busca emails da caixa de entrada"""
        mail = self.connect(account)
        mail.select(folder)
        
        # Construir critérios de busca
        search_criteria = ['ALL']
        
        if since:
            date_str = since.strftime('%d-%b-%Y')
            search_criteria = [f'SINCE {date_str}']
        
        if unread_only:
            search_criteria.append('UNSEEN')
        
        search_str = ' '.join(search_criteria)
        _, search_data = mail.search(None, search_str)
        
        email_ids = search_data[0].split()
        
        # Pegar os mais recentes
        email_ids = email_ids[-limit:]
        
        emails = []
        for e_id in reversed(email_ids):  # Mais recentes primeiro
            try:
                _, data = mail.fetch(e_id, '(RFC822)')
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                parsed_email = self._parse_email(email_message, account.id)
                if parsed_email:
                    emails.append(parsed_email)
            except Exception as e:
                print(f"[ERRO] Falha ao processar email {e_id}: {e}")
                continue
        
        return emails
    
    def _parse_email(self, email_message, account_id: int) -> Optional[EmailMessage]:
        """Parseia um email em estrutura EmailMessage"""
        try:
            # Extrair headers
            message_id = email_message.get('Message-ID', '')
            subject = self._decode_header(email_message.get('Subject', '(Sem assunto)'))
            sender_raw = email_message.get('From', '')
            sender_name, sender_email = self._parse_sender(sender_raw)
            date_str = email_message.get('Date')
            
            # Parsear data
            try:
                date = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()
            except:
                date = datetime.now()
            
            # Extrair corpo
            body_text, body_html = self._extract_body(email_message)
            
            # Extrair destinatários
            to = email_message.get('To', '')
            recipients = [addr.strip() for addr in to.split(',')] if to else []
            
            # Extrair anexos
            attachments = self._extract_attachments(email_message)
            
            return EmailMessage(
                id=f"{account_id}_{message_id}",
                account_id=account_id,
                message_id=message_id,
                subject=subject,
                sender=sender_email,
                sender_name=sender_name,
                recipients=recipients,
                date=date,
                body_text=body_text,
                body_html=body_html,
                is_read=False,  # Será determinado posteriormente
                attachments=attachments
            )
        except Exception as e:
            print(f"[ERRO] Parse de email falhou: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decodifica header de email"""
        if not header:
            return ""
        
        decoded_parts = email.header.decode_header(header)
        result = []
        
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(charset or 'utf-8', errors='ignore'))
                except:
                    result.append(part.decode('utf-8', errors='ignore'))
            else:
                result.append(part)
        
        return ' '.join(result)
    
    def _parse_sender(self, sender: str) -> Tuple[str, str]:
        """Extrai nome e email do remetente"""
        match = re.match(r'"?([^"]*)"?\s*<([^>]+)>', sender)
        if match:
            name = match.group(1).strip()
            email = match.group(2).strip()
            return name, email
        
        # Se não tem nome, retorna email como nome também
        email = sender.strip()
        return email, email
    
    def _extract_body(self, email_message) -> Tuple[str, str]:
        """Extrai corpo texto e HTML do email"""
        text_content = ""
        html_content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Ignorar anexos
                if 'attachment' in content_disposition:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='ignore')
                        
                        if content_type == 'text/plain':
                            text_content += decoded
                        elif content_type == 'text/html':
                            html_content += decoded
                except:
                    pass
        else:
            content_type = email_message.get_content_type()
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='ignore')
                    
                    if content_type == 'text/plain':
                        text_content = decoded
                    elif content_type == 'text/html':
                        html_content = decoded
            except:
                pass
        
        # Se temos HTML mas não texto, converter HTML para texto
        if not text_content and html_content:
            text_content = self._html_to_text(html_content)
        
        return text_content.strip(), html_content.strip()
    
    def _html_to_text(self, html: str) -> str:
        """Converte HTML para texto simples"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Remover scripts e styles
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except:
            return html
    
    def _extract_attachments(self, email_message) -> List[Dict]:
        """Extrai informações de anexos"""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b'')
                        })
        
        return attachments
    
    def analyze_email_with_ai(self, email_msg: EmailMessage) -> EmailMessage:
        """Usa IA para analisar email e extrair insights"""
        if not email_msg.body_text:
            return email_msg
        
        # Prompt para análise
        prompt = f"""Analise o seguinte email e forneça:
1. Um resumo conciso (máximo 3 linhas)
2. Nível de urgência (0-10, onde 10 é muito urgente)
3. Categoria (legal, client, internal, spam, other)
4. Itens de ação identificados (máximo 3)
5. Se é importante (sim/não)

Assunto: {email_msg.subject}
Remetente: {email_msg.sender_name} <{email_msg.sender}>
Conteúdo:
{email_msg.body_text[:3000]}

Responda em JSON:
{{
    "summary": "resumo aqui",
    "urgency": 7,
    "category": "legal",
    "action_items": ["ação 1", "ação 2"],
    "is_important": true
}}"""
        
        try:
            response = self.groq.generate_fast(prompt)
            
            # Extrair JSON da resposta
            import json
            # Procurar JSON na resposta
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                email_msg.summary = analysis.get('summary', '')
                email_msg.urgency_score = analysis.get('urgency', 0) / 10.0
                email_msg.category = analysis.get('category', 'other')
                email_msg.action_items = analysis.get('action_items', [])
                email_msg.is_important = analysis.get('is_important', False)
        except Exception as e:
            print(f"[AVISO] Falha na análise de IA: {e}")
            # Fallback: criar resumo simples
            email_msg.summary = email_msg.body_text[:100] + "..." if len(email_msg.body_text) > 100 else email_msg.body_text
            email_msg.category = self._categorize_simple(email_msg)
        
        return email_msg
    
    def _categorize_simple(self, email_msg: EmailMessage) -> str:
        """Categorização simples baseada em palavras-chave"""
        text = (email_msg.subject + " " + email_msg.body_text).lower()
        
        legal_keywords = [
            'processo', 'ação', 'petição', 'contestação', 'recurso',
            'sentença', 'decisão', 'despacho', 'vara', 'fórum',
            'tribunal', 'juiz', 'advogado', 'oab', 'prazo',
            'audiência', 'conciliação', 'julgamento'
        ]
        
        client_keywords = [
            'cliente', 'contrato', 'proposta', 'cotação',
            'reunião', 'atendimento', 'dúvida', 'consulta'
        ]
        
        if any(kw in text for kw in legal_keywords):
            return 'legal'
        elif any(kw in text for kw in client_keywords):
            return 'client'
        elif email_msg.sender.endswith(('@lexscan.ai', '@empresa.com')):
            return 'internal'
        else:
            return 'other'
    
    def mark_as_read(self, account: EmailAccount, message_id: str):
        """Marca email como lido"""
        try:
            mail = self.connect(account)
            mail.select('INBOX')
            
            # Buscar por Message-ID
            _, search_data = mail.search(None, f'HEADER Message-ID "{message_id}"')
            email_ids = search_data[0].split()
            
            for e_id in email_ids:
                mail.store(e_id, '+FLAGS', '\\Seen')
        except Exception as e:
            print(f"[ERRO] Falha ao marcar como lido: {e}")
    
    def send_email(
        self, 
        account: EmailAccount,
        to: str,
        subject: str,
        body: str,
        html_body: str = None
    ) -> bool:
        """Envia email usando SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = account.email_address
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            msg['Date'] = email.utils.format_datetime(datetime.now())
            
            # Parte texto
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            
            # Parte HTML (opcional)
            if body_html:
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            # Conectar ao SMTP
            server = smtplib.SMTP(account.smtp_server, account.smtp_port)
            server.starttls()
            server.login(account.username, decrypted_password)
            server.send_message(msg)
            server.quit()
            
            return True, "Email enviado com sucesso!"
        except Exception as e:
            print(f"[ERRO] Falha ao enviar email: {e}")
            return False, str(e)
            return False
    
    def get_important_emails(
        self, 
        account: EmailAccount,
        hours: int = 24
    ) -> List[EmailMessage]:
        """Retorna emails importantes das últimas N horas"""
        since = datetime.now() - timedelta(hours=hours)
        emails = self.fetch_emails(account, since=since, limit=100)
        
        # Analisar cada email
        analyzed = [self.analyze_email_with_ai(e) for e in emails]
        
        # Filtrar importantes (urgência > 0.7 ou marcado como importante)
        important = [
            e for e in analyzed 
            if e.urgency_score > 0.7 or e.is_important or e.category == 'legal'
        ]
        
        # Ordenar por urgência
        important.sort(key=lambda x: x.urgency_score, reverse=True)
        
        return important
    
    def generate_daily_summary(
        self, 
        account: EmailAccount,
        emails: List[EmailMessage]
    ) -> str:
        """Gera resumo diário de emails"""
        if not emails:
            return "Nenhum email novo nas últimas 24 horas."
        
        legal_emails = [e for e in emails if e.category == 'legal']
        urgent_emails = [e for e in emails if e.urgency_score > 0.8]
        
        summary = f"""📧 RESUMO DIÁRIO DE EMAILS - {datetime.now().strftime('%d/%m/%Y')}

Total de emails: {len(emails)}
• 🏛️ Jurídicos: {len(legal_emails)}
• 🔴 Urgentes: {len(urgent_emails)}

"""
        
        if urgent_emails:
            summary += "⚠️ EMAILS URGENTES:\n"
            for e in urgent_emails[:5]:
                summary += f"• {e.subject} ({e.sender_name})\n"
            summary += "\n"
        
        if legal_emails:
            summary += "🏛️ ASSUNTOS JURÍDICOS:\n"
            for e in legal_emails[:5]:
                summary += f"• {e.subject}\n"
                if e.action_items:
                    for item in e.action_items:
                        summary += f"  → {item}\n"
            summary += "\n"
        
        summary += "💡 Recomendações:\n"
        summary += f"• {len(urgent_emails)} emails requerem atenção imediata\n"
        if legal_emails:
            summary += f"• Verifique {len(legal_emails)} assuntos jurídicos\n"
        summary += "• Não se esqueça de responder emails de clientes\n"
        
        return summary


# Instância global
email_manager = EmailIntegrationManager()


# ============================================
# TESTES
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE INTEGRAÇÃO EMAIL - LexScan IA")
    print("=" * 60)
    
    # Teste de detecção de provedor
    test_emails = [
        "usuario@gmail.com",
        "advogado@hotmail.com",
        "contato@escritorio.com.br",
        "diretor@empresaxyz.com"
    ]
    
    print("\n🧪 Teste de detecção de provedor:")
    for email_addr in test_emails:
        provider = email_manager.detect_provider(email_addr)
        print(f"  {email_addr} → {provider}")
    
    print("\n" + "=" * 60)
    print("✅ Sistema de integração com email pronto!")
    print("=" * 60)
    print("\nPara usar, configure uma conta de email:")
    print("1. Acesse Configurações > Integrações > Email")
    print("2. Adicione suas credenciais IMAP/SMTP")
    print("3. Comece a receber resumos automáticos!")
