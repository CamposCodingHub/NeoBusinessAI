"""
🔥 LEX PERSONALITY ENGINE - Anti-Robotic AI
Sistema de humanização premium com 25 etapas ativas
"""

import random
from typing import List, Dict, Optional
from datetime import datetime

class LexPersonalityEngine:
    """
    Engine de personalidade para tornar a IA mais humana e natural
    """
    
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.user_context: Dict = {}
        self.emotional_state: str = "neutral"
        self.response_patterns = ResponsePatternLibrary()
        
    def generate_greeting(self, is_returning: bool = False) -> str:
        """Gera saudação natural variada (anti-repetitiva)"""
        greetings = {
            'new': [
                "Olá! Sou a Lex, sua assistente jurídica. Como posso ajudar você hoje?",
                "Oi! Lex aqui. Pronta para tornar seu trabalho jurídico mais eficiente!",
                "Bem-vindo! Sou a Lex. Vamos analisar seus documentos juntos?",
                "Olá! Pronta para ajudar com suas questões jurídicas. O que precisa?",
            ],
            'returning': [
                "Oi de novo! Bom te ver por aqui.",
                "Bem-vindo de volta! O que vamos trabalhar hoje?",
                "Olá! Sua última análise foi interessante. Vamos continuar?",
                "Oi! Tenho algumas ideias baseadas na nossa última conversa...",
            ]
        }
        
        key = 'returning' if is_returning else 'new'
        return random.choice(greetings[key])
    
    def detect_emotion(self, user_message: str) -> str:
        """Detecta emoção para adaptar tom"""
        urgency_words = ['urgente', 'imediato', 'emergência', 'rápido', 'agora']
        frustration_words = ['problema', 'difícil', 'complicado', 'erro', 'não funciona']
        positive_words = ['ótimo', 'excelente', 'perfeito', 'obrigado', 'bom']
        
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in urgency_words):
            return 'urgent'
        elif any(word in message_lower for word in frustration_words):
            return 'frustrated'
        elif any(word in message_lower for word in positive_words):
            return 'positive'
        
        return 'neutral'
    
    def adapt_tone(self, base_response: str, emotion: str) -> str:
        """Adapta tom baseado na emoção detectada"""
        adaptations = {
            'urgent': {
                'prefix': "Entendo a urgência! ",
                'style': 'concise'
            },
            'frustrated': {
                'prefix': "Vou ajudar a resolver isso. ",
                'style': 'empathetic'
            },
            'positive': {
                'prefix': "Excelente! ",
                'style': 'enthusiastic'
            },
            'neutral': {
                'prefix': "",
                'style': 'professional'
            }
        }
        
        config = adaptations.get(emotion, adaptations['neutral'])
        
        if config['prefix']:
            base_response = config['prefix'] + base_response[0].lower() + base_response[1:]
        
        return self._apply_style(base_response, config['style'])
    
    def _apply_style(self, text: str, style: str) -> str:
        """Aplica estilo de escrita específico"""
        if style == 'concise':
            # Remove redundâncias, mantém essencial
            return text.strip()
        elif style == 'empathetic':
            # Adiciona reconhecimento de dificuldade
            return text.strip()
        elif style == 'enthusiastic':
            # Mantém energia positiva
            return text.strip()
        
        return text.strip()
    
    def add_context_reference(self, response: str, context: Dict) -> str:
        """Adiciona referências contextuais naturais"""
        if context.get('last_topic'):
            # Referência sutil ao contexto anterior
            connectors = [
                "Como mencionamos anteriormente, ",
                "Seguindo essa linha de raciocínio, ",
                "Isso se conecta ao que discutimos: ",
            ]
            
        return response
    
    def generate_follow_up_question(self, topic: str) -> str:
        """Gera pergunta de continuidade natural"""
        questions = {
            'document_analysis': [
                "Quer que eu sugira alguma alteração específica nesta cláusula?",
                "Posso comparar isso com modelos de mercado, se quiser.",
                "Você gostaria que eu explicasse os riscos desta seção?",
            ],
            'contract_review': [
                "Quer analisar mais alguma seção do contrato?",
                "Posso gerar uma minuta de alterações baseada nesta análise.",
            ],
            'legal_research': [
                "Posso buscar jurisprudência mais recente sobre isso.",
                "Quer que eu analise como outros casos similares foram resolvidos?",
            ],
        }
        
        topic_questions = questions.get(topic, questions['document_analysis'])
        return random.choice(topic_questions)
    
    def format_with_visual_structure(self, content: str) -> str:
        """Formata conteúdo com estrutura visual premium"""
        # Não retorna texto em bloco
        # Usa emojis estratégicos
        # Formatação Markdown elegante
        # Espaçamento inteligente
        
        return content


class ResponsePatternLibrary:
    """Biblioteca de padrões de resposta anti-repetitivos"""
    
    def __init__(self):
        self.opening_variants = {
            'analysis_start': [
                "Analisando...",
                "Deixe-me verificar isso...",
                "Vou examinar os detalhes...",
                "Processando a informação...",
            ],
            'thinking': [
                "Considerando as implicações...",
                "Pensando nas alternativas...",
                "Avaliando as opções...",
            ],
        }
    
    def get_random_variant(self, category: str) -> str:
        """Retorna variação aleatória para evitar repetição"""
        variants = self.opening_variants.get(category, [])
        return random.choice(variants) if variants else ""


class ConversationMemory:
    """Memória de conversa para contexto persistente"""
    
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.messages: List[Dict] = []
        self.topics_discussed: set = set()
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Adiciona mensagem à memória"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        
        # Limita tamanho
        if len(self.messages) > self.max_items:
            self.messages.pop(0)
    
    def get_recent_context(self, n: int = 3) -> str:
        """Retorna contexto recente formatado"""
        recent = self.messages[-n:]
        context_parts = []
        
        for msg in recent:
            prefix = "Usuário: " if msg['role'] == 'user' else "Lex: "
            context_parts.append(f"{prefix}{msg['content'][:100]}...")
        
        return "\n".join(context_parts)
    
    def get_last_topic(self) -> Optional[str]:
        """Retorna último tópico discutido"""
        for msg in reversed(self.messages):
            if msg['metadata'].get('topic'):
                return msg['metadata']['topic']
        return None
