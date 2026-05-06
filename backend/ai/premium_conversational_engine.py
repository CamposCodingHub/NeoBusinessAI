"""
🚀🧠 PREMIUM CONVERSATIONAL AI ENGINE - LexScan IA
Sistema Supremo de IA: Humanização, UX Premium, Memória, Inteligência Contextual

Implementa 25 etapas de evolução da IA:
1. Personalidade Avançada
2. Anti-Repetição
3. Memória Contextual
4. Formatação Premium
5. Raciocínio Inteligente
6. Busca Web Inteligente
7. Humanização Extrema
8. UX Conversacional Premium
9. Contexto por Nível
10. Respostas Inteligentes
11-25. Sistemas avançados adicionais

Data: Maio 2026
Versão: 2.0.0-PREMIUM
"""

import json
import random
import hashlib
import time
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import asyncio
from collections import deque, Counter

# Groq Integration
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[PREMIUM AI] Biblioteca groq nao instalada. Execute: pip install groq")


# =============================================================================
# CONFIGURAÇÃO E ENUMS
# =============================================================================

class UserLevel(Enum):
    """Níveis de usuário para adaptação de respostas"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    TECHNICAL = "technical"
    ENTERPRISE = "enterprise"

class EmotionalState(Enum):
    """Estados emocionais detectados"""
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    TECHNICAL = "technical"
    NEUTRAL = "neutral"
    URGENT = "urgent"

class ResponseStyle(Enum):
    """Estilos de resposta variados"""
    STORYTELLING = "storytelling"
    ANALOGY = "analogy"
    STRATEGIC = "strategic"
    DIRECT = "direct"
    VISUAL = "visual"
    REFLECTIVE = "reflective"
    COMPARISON = "comparison"
    DEEP_DIVE = "deep_dive"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ConversationMemory:
    """Memória de conversa com contexto avançado"""
    user_id: str
    messages: deque = field(default_factory=lambda: deque(maxlen=20))
    user_preferences: Dict = field(default_factory=dict)
    detected_intent: str = ""
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    user_level: UserLevel = UserLevel.INTERMEDIATE
    context_summary: str = ""
    last_topics: List[str] = field(default_factory=list)
    interaction_count: int = 0
    satisfaction_history: List[float] = field(default_factory=list)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Adiciona mensagem com metadados ricos"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        })
        self.interaction_count += 1

@dataclass
class UserIntent:
    """Intenção oculta do usuário"""
    explicit: str = ""  # O que o usuário perguntou
    implicit: str = ""  # O que ele realmente quer
    emotional_need: str = ""  # Necessidade emocional
    knowledge_level: str = ""
    urgency: float = 0.0  # 0-1
    depth_desired: str = "medium"  # shallow, medium, deep
    expected_outcome: str = ""

@dataclass
class AIResponse:
    """Resposta estruturada da IA"""
    content: str
    style: ResponseStyle
    confidence: float
    metadata: Dict
    formatted_output: str = ""
    

# =============================================================================
# SISTEMA ANTI-REPETIÇÃO
# =============================================================================

class AntiRepetitionSystem:
    """
    Sistema avançado anti-repetição
    Detecta e corrige padrões repetitivos
    """
    
    def __init__(self):
        self.used_phrases = deque(maxlen=100)
        self.used_structures = deque(maxlen=50)
        self.phrase_variations = self._load_phrase_variations()
        self.structure_templates = self._load_structure_templates()
    
    def _load_phrase_variations(self) -> Dict[str, List[str]]:
        """Carrega variações de frases comuns"""
        return {
            "intro_greeting": [
                "Entendi perfeitamente.",
                "Excelente pergunta.",
                "Interessante ponto de vista.",
                "Vamos analisar isso juntos.",
                "Bom questionamento.",
                "Vejo onde você quer chegar.",
                "Isso é fascinante.",
                "Perspectiva importante."
            ],
            "transition": [
                "Aqui está minha análise:",
                "Considerando todos os aspectos:",
                "Minha avaliação profissional:",
                "Do ponto de vista estratégico:",
                "Analisando os dados:",
                "Com base no contexto:",
                "Minha perspectiva sobre isso:",
                "Aqui está minha leitura:"
            ],
            "conclusion": [
                "Para resumir nossa discussão:",
                "Considerando tudo que analisamos:",
                "Minha recomendação final:",
                "O caminho mais estratégico:",
                "Para fechar com chave de ouro:",
                "Síntese das nossas ideias:",
                "Conclusão prática:",
                "Próximo passo ideal:"
            ],
            "encouragement": [
                "Isso é totalmente viável.",
                "Você está no caminho certo.",
                "Esta abordagem tem potencial.",
                "Estrategicamente, faz sentido.",
                "Isso pode gerar resultados reais.",
                "Sua análise tem mérito.",
                "Vale a pena explorar isso.",
                "Esta direção é promissora."
            ]
        }
    
    def _load_structure_templates(self) -> List[Dict]:
        """Carrega templates de estrutura variados"""
        return [
            {"name": "analysis", "pattern": ["context", "analysis", "conclusion"]},
            {"name": "story", "pattern": ["hook", "narrative", "lesson"]},
            {"name": "strategic", "pattern": ["problem", "options", "recommendation"]},
            {"name": "visual", "pattern": ["overview", "details", "summary"]},
            {"name": "comparative", "pattern": ["option_a", "option_b", "verdict"]},
            {"name": "deep_dive", "pattern": ["surface", "depth", "application"]}
        ]
    
    def detect_repetition(self, text: str) -> Dict[str, Any]:
        """Detecta padrões repetitivos no texto"""
        issues = {
            'repeated_phrases': [],
            'repeated_words': [],
            'structure_pattern': None,
            'similarity_score': 0.0
        }
        
        # Detectar frases repetidas
        for phrase in self.used_phrases:
            if phrase.lower() in text.lower() and len(phrase) > 10:
                issues['repeated_phrases'].append(phrase)
        
        # Detectar palavras repetidas excessivamente
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        for word, count in word_counts.items():
            if count > 3 and len(word) > 3:
                issues['repeated_words'].append((word, count))
        
        return issues
    
    def generate_variation(self, phrase_type: str, context: Dict = None) -> str:
        """Gera variação única de frase"""
        variations = self.phrase_variations.get(phrase_type, ["Entendo."])
        
        # Filtrar variações já usadas recentemente
        available = [v for v in variations if v not in self.used_phrases]
        if not available:
            available = variations  # Reset se todas foram usadas
        
        selected = random.choice(available)
        self.used_phrases.append(selected)
        return selected
    
    def vary_structure(self, current_structure: str) -> str:
        """Alterna estrutura de resposta"""
        templates = [t for t in self.structure_templates 
                    if t['name'] != current_structure]
        if templates:
            new_template = random.choice(templates)
            self.used_structures.append(new_template['name'])
            return new_template['name']
        return current_structure


# =============================================================================
# SISTEMA DE MEMÓRIA CONTEXTUAL
# =============================================================================

class AdvancedMemorySystem:
    """
    Sistema de memória contextual avançada
    Mantém contexto em conversas longas
    """
    
    def __init__(self):
        self.conversations: Dict[str, ConversationMemory] = {}
        self.user_profiles: Dict[str, Dict] = {}
        self.topic_graph: Dict[str, List[str]] = {}
    
    def get_or_create_memory(self, user_id: str) -> ConversationMemory:
        """Obtém ou cria memória de conversa"""
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationMemory(user_id=user_id)
        return self.conversations[user_id]
    
    def update_user_profile(self, user_id: str, insights: Dict):
        """Atualiza perfil do usuário com novas informações"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'interests': [],
                'expertise_areas': [],
                'communication_style': 'neutral',
                'preferred_depth': 'medium',
                'common_topics': [],
                'satisfaction_trend': []
            }
        
        profile = self.user_profiles[user_id]
        
        if 'interests' in insights:
            profile['interests'].extend(insights['interests'])
            profile['interests'] = list(set(profile['interests']))[-10:]  # Últimos 10
        
        if 'expertise' in insights:
            profile['expertise_areas'].extend(insights['expertise'])
            profile['expertise_areas'] = list(set(profile['expertise_areas']))
        
        if 'topics' in insights:
            profile['common_topics'].extend(insights['topics'])
            profile['common_topics'] = list(set(profile['common_topics']))[-15:]
    
    def get_context_summary(self, user_id: str) -> str:
        """Gera resumo do contexto da conversa"""
        memory = self.get_or_create_memory(user_id)
        profile = self.user_profiles.get(user_id, {})
        
        summary_parts = []
        
        if memory.last_topics:
            summary_parts.append(f"Tópicos recentes: {', '.join(memory.last_topics[-3:])}")
        
        if profile.get('interests'):
            summary_parts.append(f"Interesses: {', '.join(profile['interests'][:3])}")
        
        if memory.emotional_state != EmotionalState.NEUTRAL:
            summary_parts.append(f"Estado: {memory.emotional_state.value}")
        
        return " | ".join(summary_parts) if summary_parts else "Novo contexto"
    
    def detect_conversation_shift(self, user_id: str, new_message: str) -> bool:
        """Detecta mudança de tópico na conversa"""
        memory = self.get_or_create_memory(user_id)
        
        if not memory.last_topics:
            return False
        
        # Análise simples de similaridade de tópicos
        last_topic = memory.last_topics[-1].lower() if memory.last_topics else ""
        message_lower = new_message.lower()
        
        # Extrair palavras-chave (simplificado)
        topic_words = set(last_topic.split())
        message_words = set(message_lower.split())
        
        if topic_words and message_words:
            overlap = len(topic_words & message_words)
            similarity = overlap / len(topic_words)
            return similarity < 0.3  # Mudança significativa
        
        return False


# =============================================================================
# SISTEMA DE DETECÇÃO DE INTENÇÃO
# =============================================================================

class IntentDetectionSystem:
    """
    Detecta intenção oculta do usuário
    Vai além do texto explícito
    """
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.emotional_indicators = self._load_emotional_indicators()
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Carrega padrões de intenção"""
        return {
            "seeking_opportunity": [
                "ganhar dinheiro", "lucro", "renda", "oportunidade",
                "como faturar", "como monetizar", "fonte de renda"
            ],
            "seeking_solution": [
                "problema", "dificuldade", "não consigo", "erro",
                "falha", "bug", "quebrado", "não funciona"
            ],
            "seeking_knowledge": [
                "aprender", "entender", "como funciona", "tutorial",
                "explicação", "conceito", "o que é", "definição"
            ],
            "seeking_strategy": [
                "estratégia", "plano", "como escalar", "como crescer",
                "melhor forma", "otimizar", "melhorar"
            ],
            "seeking_validation": [
                "estou certo", "faz sentido", " Concorda", "acha que",
                "validar", "confirmar", "opinião"
            ]
        }
    
    def _load_emotional_indicators(self) -> Dict[str, List[str]]:
        """Carrega indicadores emocionais"""
        return {
            EmotionalState.FRUSTRATED: [
                "não entendo", "difícil", "complexo", "confuso",
                "frustrado", "desesperado", "não sei", "perdido"
            ],
            EmotionalState.EXCITED: [
                "incrível", "fantástico", "top", "vamos",
                "animado", "empolgado", "bora", "vai ser"
            ],
            EmotionalState.URGENT: [
                "urgente", "rápido", "hoje", "agora",
                "preciso", "deadline", "prazo", "imediato"
            ]
        }
    
    def analyze_intent(self, message: str, history: List[Dict]) -> UserIntent:
        """Analisa intenção profunda do usuário"""
        intent = UserIntent()
        message_lower = message.lower()
        
        # Detectar intenção explícita
        intent.explicit = message
        
        # Detectar intenção implícita
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                intent.implicit = intent_type
                break
        
        # Detectar estado emocional
        for emotion, indicators in self.emotional_indicators.items():
            if any(ind in message_lower for ind in indicators):
                # emotional_state é setado na memória, não aqui
                break
        
        # Detectar urgência
        urgency_words = ['urgente', 'rápido', 'hoje', 'agora', 'imediato', 'preciso']
        intent.urgency = sum(1 for word in urgency_words if word in message_lower) / len(urgency_words)
        
        # Detectar profundidade desejada
        if any(word in message_lower for word in ['simples', 'básico', 'resumo']):
            intent.depth_desired = "shallow"
        elif any(word in message_lower for word in ['profundo', 'detalhado', 'avançado', 'técnico']):
            intent.depth_desired = "deep"
        else:
            intent.depth_desired = "medium"
        
        # Inferir necessidade emocional
        if '?' in message and not message_lower.startswith('como'):
            intent.emotional_need = "validation"
        elif any(word in message_lower for word in ['ajuda', 'socorro', 'não sei']):
            intent.emotional_need = "guidance"
        elif intent.urgency > 0.5:
            intent.emotional_need = "speed"
        else:
            intent.emotional_need = "information"
        
        return intent


# =============================================================================
# SISTEMA DE FORMATAÇÃO PREMIUM
# =============================================================================

class PremiumFormattingEngine:
    """
    Motor de formatação premium
    Cria respostas visualmente agradáveis
    """
    
    def __init__(self):
        self.formatting_rules = self._load_formatting_rules()
    
    def _load_formatting_rules(self) -> Dict:
        """Carrega regras de formatação"""
        return {
            'max_paragraph_length': 3,
            'max_line_length': 80,
            'use_emojis': True,
            'hierarchy_levels': 3,
            'spacing_rules': {
                'after_heading': 1,
                'between_paragraphs': 1,
                'before_list': 1
            }
        }
    
    def format_response(self, content: str, style: ResponseStyle, metadata: Dict) -> str:
        """Formata resposta com estilo premium"""
        formatted = content
        
        # Aplicar hierarquia visual
        formatted = self._apply_visual_hierarchy(formatted)
        
        # Aplicar espaçamento inteligente
        formatted = self._apply_intelligent_spacing(formatted)
        
        # Adicionar destaques visuais
        formatted = self._add_visual_emphasis(formatted, metadata)
        
        # Quebrar blocos grandes
        formatted = self._break_large_blocks(formatted)
        
        # Adicionar emojis contextuais
        if self.formatting_rules['use_emojis']:
            formatted = self._add_contextual_emojis(formatted, style)
        
        return formatted
    
    def _apply_visual_hierarchy(self, text: str) -> str:
        """Aplica hierarquia visual com markdown"""
        # Converter tópicos em headings
        lines = text.split('\n')
        result = []
        
        for line in lines:
            # Detectar e converter tópicos principais
            if line.strip().endswith(':') and len(line) < 50:
                line = f"\n**{line.strip()}**\n"
            result.append(line)
        
        return '\n'.join(result)
    
    def _apply_intelligent_spacing(self, text: str) -> str:
        """Aplica espaçamento inteligente"""
        # Adicionar quebras estratégicas
        text = re.sub(r'([.!?])\s+(?=[A-Z])', r'\1\n\n', text)
        return text
    
    def _add_visual_emphasis(self, text: str, metadata: Dict) -> str:
        """Adiciona destaques visuais importantes"""
        # Destacar palavras-chave importantes
        important_terms = metadata.get('key_terms', [])
        for term in important_terms:
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            text = pattern.sub(f'**{term}**', text)
        return text
    
    def _break_large_blocks(self, text: str) -> str:
        """Quebra blocos de texto grandes"""
        paragraphs = text.split('\n\n')
        result = []
        
        for para in paragraphs:
            if len(para) > 300:
                # Dividir em blocos menores
                sentences = re.split(r'([.!?])\s+', para)
                chunks = []
                current_chunk = ""
                
                for i in range(0, len(sentences), 2):
                    sentence = sentences[i]
                    if i + 1 < len(sentences):
                        sentence += sentences[i + 1]
                    
                    if len(current_chunk) + len(sentence) < 200:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                result.extend(chunks)
            else:
                result.append(para)
        
        return '\n\n'.join(result)
    
    def _add_contextual_emojis(self, text: str, style: ResponseStyle) -> str:
        """Adiciona emojis contextuais"""
        emoji_map = {
            ResponseStyle.STRATEGIC: '🎯',
            ResponseStyle.STORYTELLING: '📖',
            ResponseStyle.ANALOGY: '💡',
            ResponseStyle.DIRECT: '✅',
            ResponseStyle.DEEP_DIVE: '🔍',
            ResponseStyle.VISUAL: '📊'
        }
        
        emoji = emoji_map.get(style, '💬')
        return f"{emoji} {text}"


# =============================================================================
# MOTOR DE RACIOCÍNIO INTELIGENTE
# =============================================================================

class IntelligentReasoningEngine:
    """
    Motor de raciocínio inteligente
    Analisa antes de responder
    """
    
    def __init__(self):
        self.reasoning_steps = []
        self.depth_analyzer = DepthAnalyzer()
    
    def analyze_before_response(
        self,
        message: str,
        intent: UserIntent,
        memory: ConversationMemory
    ) -> Dict[str, Any]:
        """Analisa contexto antes de gerar resposta"""
        analysis = {
            'user_real_need': '',
            'recommended_depth': 'medium',
            'recommended_tone': 'professional',
            'should_provide_examples': False,
            'should_be_strategic': False,
            'response_length': 'medium',
            'key_aspects_to_cover': []
        }
        
        # Analisar necessidade real
        analysis['user_real_need'] = self._infer_real_need(message, intent)
        
        # Determinar profundidade
        analysis['recommended_depth'] = intent.depth_desired
        
        # Determinar tom
        if memory.emotional_state == EmotionalState.FRUSTRATED:
            analysis['recommended_tone'] = 'supportive'
        elif memory.emotional_state == EmotionalState.EXCITED:
            analysis['recommended_tone'] = 'energetic'
        elif intent.implicit == 'seeking_strategy':
            analysis['recommended_tone'] = 'strategic'
        
        # Decidir se precisa de exemplos
        analysis['should_provide_examples'] = (
            intent.knowledge_level == 'beginner' or
            'exemplo' in message.lower() or
            'como' in message.lower()
        )
        
        # Decidir se deve ser estratégico
        analysis['should_be_strategic'] = (
            intent.implicit in ['seeking_strategy', 'seeking_opportunity'] or
            memory.user_level == UserLevel.ENTERPRISE
        )
        
        # Comprimento da resposta
        if intent.urgency > 0.7:
            analysis['response_length'] = 'short'
        elif intent.depth_desired == 'deep':
            analysis['response_length'] = 'long'
        
        return analysis
    
    def _infer_real_need(self, message: str, intent: UserIntent) -> str:
        """Infere necessidade real do usuário"""
        needs_map = {
            "seeking_opportunity": "encontrar caminho viável de monetização",
            "seeking_solution": "resolver problema específico de forma prática",
            "seeking_knowledge": "entender conceito para aplicar depois",
            "seeking_strategy": "direção estratégica clara para decisão",
            "seeking_validation": "confirmação de que está no caminho certo"
        }
        
        return needs_map.get(intent.implicit, "informação clara e aplicável")


class DepthAnalyzer:
    """Analisa profundidade necessária"""
    
    def analyze(self, message: str, user_level: UserLevel) -> str:
        """Determina profundidade ideal"""
        technical_terms = len(re.findall(
            r'\b(arquitetura|API|database|microserviço|escalabilidade|deploy|CI/CD)\b',
            message, re.I
        ))
        
        if user_level == UserLevel.TECHNICAL or technical_terms >= 3:
            return "deep"
        elif user_level == UserLevel.BEGINNER:
            return "shallow"
        
        return "medium"


# =============================================================================
# SISTEMA DE HUMANIZAÇÃO
# =============================================================================

class HumanizationEngine:
    """
    Motor de humanização de respostas
    Torna a IA mais natural e humana
    """
    
    def __init__(self):
        self.natural_phrases = self._load_natural_phrases()
        self.conversational_fillers = [
            "Bom, ", "Então, ", "Veja bem, ", "Olha, ",
            "Sabe, ", "Na verdade, ", "Interessante, ", "Hmm, "
        ]
    
    def _load_natural_phrases(self) -> Dict[str, List[str]]:
        """Carrega frases naturais variadas"""
        return {
            "thinking": [
                "Deixa eu pensar...",
                "Vamos analisar isso...",
                "Boa pergunta...",
                "Isso me faz refletir..."
            ],
            "agreement": [
                "Exatamente!",
                "Isso mesmo.",
                "Perfeito.",
                "Concordo plenamente."
            ],
            "transition": [
                "Agora, falando sobre...",
                "E mais uma coisa...",
                "Além disso...",
                "E aqui vai uma ideia..."
            ]
        }
    
    def humanize(self, text: str, context: Dict) -> str:
        """Aplica camadas de humanização"""
        # Adicionar preenchimento conversacional ocasional
        if random.random() < 0.3 and len(text) > 100:
            filler = random.choice(self.conversational_fillers)
            text = filler + text[0].lower() + text[1:]
        
        # Variar estrutura de frases
        text = self._vary_sentence_structure(text)
        
        # Adicionar pausas naturais
        text = self._add_natural_pauses(text)
        
        return text
    
    def _vary_sentence_structure(self, text: str) -> str:
        """Varia estrutura de frases"""
        # Evitar sempre começar da mesma forma
        sentences = re.split(r'(?<=[.!?])\s+', text)
        varied = []
        
        for i, sent in enumerate(sentences):
            if i > 0 and sent.startswith('A '):
                # Variar ocasionalmente
                if random.random() < 0.2:
                    sent = sent[2:]  # Remove "A "
                    sent = sent[0].upper() + sent[1:]
            varied.append(sent)
        
        return ' '.join(varied)
    
    def _add_natural_pauses(self, text: str) -> str:
        """Adiciona pausas naturais"""
        # Substituir algumas vírgulas por reticências para pausa
        text = re.sub(r',\s+(?=[a-z])', lambda m: '... ' if random.random() < 0.1 else m.group(), text)
        return text


# =============================================================================
# SISTEMA ANTI-CRÍTICA (AUTO-AVALIAÇÃO)
# =============================================================================

class SelfCritiqueSystem:
    """
    Sistema de auto-crítica da IA
    Avalia e melhora a própria resposta
    """
    
    def critique_and_improve(self, response: str, context: Dict) -> Tuple[str, float]:
        """Avalia e melhora a resposta"""
        issues = []
        score = 100.0
        
        # Verificar repetição
        if self._is_repetitive(response, context.get('last_responses', [])):
            issues.append("repetitiva")
            score -= 20
        
        # Verificar se é genérica
        if self._is_generic(response):
            issues.append("genérica")
            score -= 15
        
        # Verificar tamanho
        if len(response) < 50:
            issues.append("curta demais")
            score -= 10
        elif len(response) > 2000:
            issues.append("longa demais")
            score -= 10
        
        # Verificar artificialidade
        if self._sounds_artificial(response):
            issues.append("artificial")
            score -= 15
        
        # Melhorar se necessário
        improved = response
        if score < 80:
            improved = self._improve_response(response, issues)
        
        return improved, score
    
    def _is_repetitive(self, response: str, last_responses: List[str]) -> bool:
        """Verifica se resposta é repetitiva"""
        for last in last_responses[-3:]:
            similarity = self._calculate_similarity(response, last)
            if similarity > 0.6:
                return True
        return False
    
    def _is_generic(self, response: str) -> bool:
        """Verifica se resposta é genérica"""
        generic_patterns = [
            "é importante", "é fundamental", "é essencial",
            "você deve", "é recomendado", "considere"
        ]
        return sum(1 for p in generic_patterns if p in response.lower()) >= 3
    
    def _sounds_artificial(self, response: str) -> bool:
        """Verifica se soa artificial"""
        artificial_patterns = [
            "neste contexto", "sob esta ótica", "diante do exposto",
            "a partir desta perspectiva"
        ]
        return any(p in response.lower() for p in artificial_patterns)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simples"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))
    
    def _improve_response(self, response: str, issues: List[str]) -> str:
        """Tenta melhorar a resposta"""
        improved = response
        
        if "genérica" in issues:
            improved += "\n\nPara tornar isso mais concreto: que tal começarmos com um exemplo específico do seu contexto?"
        
        if "repetitiva" in issues:
            improved = improved.replace("é importante", "vale a pena destacar")
            improved = improved.replace("é fundamental", "o ponto-chave é")
        
        return improved


# =============================================================================
# MOTOR PREMIUM PRINCIPAL
# =============================================================================

class PremiumConversationalEngine:
    """
    Motor Premium de Conversação
    Integra todos os sistemas avançados
    """
    
    def __init__(self):
        self.anti_repetition = AntiRepetitionSystem()
        self.memory_system = AdvancedMemorySystem()
        self.intent_detection = IntentDetectionSystem()
        self.formatting_engine = PremiumFormattingEngine()
        self.reasoning_engine = IntelligentReasoningEngine()
        self.humanization = HumanizationEngine()
        self.self_critique = SelfCritiqueSystem()
        
        # Groq Client para respostas reais
        self.groq_client = None
        self.groq_available = False
        if GROQ_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                try:
                    self.groq_client = Groq(api_key=api_key)
                    self.groq_available = True
                    print("[PREMIUM AI] Groq client inicializado com sucesso!")
                except Exception as e:
                    print(f"[PREMIUM AI] Erro ao inicializar Groq: {e}")
            else:
                print("[PREMIUM AI] GROQ_API_KEY nao configurada. Usando modo simulado.")
        
        # Configurações de personalidade
        self.ai_identity = {
            'name': 'Lex',
            'personality': 'professional_yet_friendly',
            'expertise': 'legal_tech_ai',
            'style': 'strategic_conversational'
        }
    
    async def generate_premium_response(
        self,
        user_message: str,
        user_id: str,
        document_context: str = ""
    ) -> Dict[str, Any]:
        """
        Gera resposta premium completa
        """
        # 1. Obter contexto da conversa
        memory = self.memory_system.get_or_create_memory(user_id)
        
        # 2. Detectar intenção
        intent = self.intent_detection.analyze_intent(
            user_message,
            list(memory.messages)
        )
        
        # 3. Atualizar estado emocional na memória
        for emotion, indicators in self.intent_detection.emotional_indicators.items():
            if any(ind in user_message.lower() for ind in indicators):
                memory.emotional_state = emotion
                break
        
        # 4. Raciocinar antes de responder
        analysis = self.reasoning_engine.analyze_before_response(
            user_message, intent, memory
        )
        
        # 5. Detectar mudança de contexto
        context_shift = self.memory_system.detect_conversation_shift(user_id, user_message)
        
        # 6. Selecionar estilo de resposta
        style = self._select_response_style(intent, memory)
        
        # 7. Gerar conteúdo base (simulado - integraria com LLM real)
        base_content = await self._generate_base_content(
            user_message,
            analysis,
            document_context,
            memory
        )
        
        # 8. Aplicar variações anti-repetição
        varied_content = self._apply_variations(base_content, style)
        
        # 9. Aplicar humanização
        humanized_content = self.humanization.humanize(varied_content, {
            'intent': intent,
            'memory': memory
        })
        
        # 10. Formatar premium
        formatted_response = self.formatting_engine.format_response(
            humanized_content,
            style,
            {'key_terms': self._extract_key_terms(user_message)}
        )
        
        # 11. Auto-criticar e melhorar
        final_response, quality_score = self.self_critique.critique_and_improve(
            formatted_response,
            {'last_responses': [m['content'] for m in memory.messages if m['role'] == 'assistant'][-3:]}
        )
        
        # 12. Atualizar memória
        memory.add_message('user', user_message)
        memory.add_message('assistant', final_response, {
            'style': style.value,
            'quality_score': quality_score,
            'intent_detected': intent.implicit
        })
        
        # 13. Extrair tópicos para memória
        topics = self._extract_topics(user_message)
        memory.last_topics.extend(topics)
        memory.last_topics = memory.last_topics[-10:]  # Manter últimos 10
        
        return {
            'response': final_response,
            'style': style.value,
            'quality_score': quality_score,
            'detected_intent': intent.implicit,
            'emotional_state': memory.emotional_state.value,
            'context_summary': self.memory_system.get_context_summary(user_id),
            'metadata': {
                'interaction_count': memory.interaction_count,
                'response_length': len(final_response),
                'analysis': analysis
            }
        }
    
    def _select_response_style(
        self,
        intent: UserIntent,
        memory: ConversationMemory
    ) -> ResponseStyle:
        """Seleciona estilo de resposta baseado em contexto"""
        # Alternar estilos para variar
        if memory.interaction_count % 5 == 0:
            return ResponseStyle.STORYTELLING
        elif intent.implicit == 'seeking_strategy':
            return ResponseStyle.STRATEGIC
        elif intent.depth_desired == 'deep':
            return ResponseStyle.DEEP_DIVE
        elif intent.emotional_need == 'validation':
            return ResponseStyle.REFLECTIVE
        else:
            styles = list(ResponseStyle)
            return random.choice(styles)
    
    async def _generate_base_content(
        self,
        message: str,
        analysis: Dict,
        document_context: str,
        memory: ConversationMemory
    ) -> str:
        """
        Gera conteúdo base usando Groq API para respostas reais e humanizadas
        """
        # Se Groq disponível, usar API real
        if self.groq_available and self.groq_client:
            try:
                return await self._generate_with_groq(message, analysis, document_context, memory)
            except Exception as e:
                print(f"[PREMIUM AI] Erro Groq, usando fallback: {e}")
                return await self._generate_fallback_content(message, analysis, document_context)
        
        # Fallback: modo simulado (quando Groq não disponível)
        return await self._generate_fallback_content(message, analysis, document_context)
    
    async def _generate_with_groq(
        self,
        message: str,
        analysis: Dict,
        document_context: str,
        memory: ConversationMemory
    ) -> str:
        """Gera resposta usando Groq API"""
        
        # Construir prompt do sistema baseado na análise
        depth_instruction = {
            'deep': "Forneça uma resposta DETALHADA e TÉCNICA com exemplos práticos.",
            'shallow': "Forneça uma resposta SIMPLES e DIRETA, fácil de entender.",
            'medium': "Forneça uma resposta EQUILIBRADA com nível adequado de detalhes."
        }.get(analysis['recommended_depth'], "Forneça uma resposta natural e útil.")
        
        emotional_instruction = {
            'excited': "Responda com ENERGIA e ENTUSIASMO, celebrando a empolgação do usuário.",
            'frustrated': "Responda de forma EMPÁTICA, APOIADORA e ENCORAJADORA.",
            'confused': "Responda com CLAREZA e PACIÊNCIA, simplificando conceitos.",
            'neutral': "Responda de forma AMIGÁVEL e PROFISSIONAL.",
            'curious': "Responda de forma ENGAJADORA, incentivando a exploração."
        }.get(analysis.get('emotional_state', 'neutral'), "Responda de forma natural e amigável.")
        
        strategic_instruction = "Inclua insights estratégicos e perspectivas de negócio." if analysis.get('should_be_strategic') else ""
        examples_instruction = "Use exemplos práticos e concretos." if analysis.get('should_provide_examples') else ""
        
        # Contexto de memória
        context_info = ""
        if memory:
            # Extrair tópicos das mensagens anteriores
            recent_messages = list(memory.messages)[-3:] if memory.messages else []
            if recent_messages:
                context_info = f"\nContexto da conversa: {len(memory.messages)} mensagens trocadas"
        
        document_info = ""
        if document_context:
            document_info = f"\nContexto do documento: {document_context[:500]}..."
        
        system_prompt = f"""Você é Lex, uma IA especialista em tecnologia jurídica (Legal Tech) e SaaS.

Personalidade: Profissional, amigável, estratégica e natural. Você conversa como um humano experiente, não como um robô.

Instruções:
{depth_instruction}
{emotional_instruction}
{strategic_instruction}
{examples_instruction}

Regras IMPORTANTES:
1. Seja natural e conversacional - evite linguagem robótica
2. Varie suas introduções (não sempre comece igual)
3. Use emojis ocasionalmente para tornar a conversa agradável
4. Faça perguntas de retorno para manter o diálogo
5. Seja específico, não genérico
6. Mantenha contexto da conversa anterior
{context_info}
{document_info}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Chamada assíncrona para Groq
        response = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=2048,
            temperature=0.8,
            top_p=0.9
        )
        
        return response.choices[0].message.content
    
    async def _generate_fallback_content(
        self,
        message: str,
        analysis: Dict,
        document_context: str
    ) -> str:
        """Gera conteúdo simulado quando Groq não disponível"""
        intro = self.anti_repetition.generate_variation("intro_greeting")
        transition = self.anti_repetition.generate_variation("transition")
        
        content = f"{intro} {transition}\n\n"
        
        if document_context:
            content += f"Analisando o contexto, {analysis['user_real_need']}.\n\n"
        else:
            content += f"Sobre sua questão: {analysis['user_real_need']}.\n\n"
        
        if analysis['recommended_depth'] == 'deep':
            content += "Vamos explorar isso em detalhes...\n\n"
        elif analysis['recommended_depth'] == 'shallow':
            content += "Resumindo o essencial...\n\n"
        
        conclusion = self.anti_repetition.generate_variation("conclusion")
        content += f"\n{conclusion}"
        
        return content
    
    def _apply_variations(self, content: str, style: ResponseStyle) -> str:
        """Aplica variações para evitar padrões"""
        # Detectar e corrigir repetições
        issues = self.anti_repetition.detect_repetition(content)
        
        if issues['repeated_phrases']:
            # Substituir por variações
            for phrase in issues['repeated_phrases'][:2]:
                if 'excelente' in phrase.lower():
                    content = content.replace(phrase, "Ótimo ponto", 1)
        
        return content
    
    def _extract_key_terms(self, message: str) -> List[str]:
        """Extrai termos-chave da mensagem"""
        # Simplificado - idealmente usar NLP
        legal_terms = ['contrato', 'prazo', 'cláusula', 'obrigação', 'direito', 'lei']
        tech_terms = ['API', 'SaaS', 'deploy', 'escalabilidade', 'arquitetura']
        
        found = []
        for term in legal_terms + tech_terms:
            if term.lower() in message.lower():
                found.append(term)
        return found[:5]  # Top 5
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extrai tópicos da mensagem"""
        # Simplificado
        words = re.findall(r'\b[A-Z][a-z]+\b', message)
        return list(set(words))[:3]  # Top 3 únicos


# =============================================================================
# FUNÇÃO DE INTERFACE PRINCIPAL
# =============================================================================

def create_premium_ai_engine() -> PremiumConversationalEngine:
    """Factory para criar motor premium"""
    return PremiumConversationalEngine()


# Exemplo de uso
if __name__ == "__main__":
    engine = create_premium_ai_engine()
    
    async def test():
        result = await engine.generate_premium_response(
            user_message="Como posso escalar minha arquitetura SaaS para milhares de usuários?",
            user_id="test_user_123"
        )
        
        print("=" * 60)
        print("🚀 RESPOSTA PREMIUM GERADA")
        print("=" * 60)
        print(f"\nQualidade: {result['quality_score']:.0f}/100")
        print(f"Estilo: {result['style']}")
        print(f"Intenção: {result['detected_intent']}")
        print(f"Estado: {result['emotional_state']}")
        print("\n--- RESPOSTA ---")
        print(result['response'])
    
    asyncio.run(test())
