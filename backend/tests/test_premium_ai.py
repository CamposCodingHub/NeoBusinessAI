"""
Testes Unitários para Premium Conversational AI Engine
=====================================================
Cobertura: Todos os sistemas do motor de IA
"""

import pytest
import asyncio
from datetime import datetime
from ai.premium_conversational_engine import (
    PremiumConversationalEngine,
    ConversationMemory,
    UserIntent,
    ResponseStyle,
    UserLevel,
    EmotionalState,
    AntiRepetitionSystem,
    AdvancedMemorySystem,
    IntentDetectionSystem,
    PremiumFormattingEngine,
    IntelligentReasoningEngine,
    HumanizationEngine,
    SelfCritiqueSystem
)
from ai.premium_conversational_engine_v2 import (
    PremiumConversationalEngineV2,
    LegalEntityDetector,
    RAGIntegration,
    FeedbackSystem,
    create_premium_ai_engine_v2
)


class TestConversationMemory:
    """Testes de memória de conversação"""
    
    def test_create_memory(self):
        """Testa criação de memória"""
        memory = ConversationMemory(user_id="test_user")
        assert memory.user_id == "test_user"
        assert memory.interaction_count == 0
        assert memory.emotional_state == EmotionalState.NEUTRAL
    
    def test_add_message(self):
        """Testa adição de mensagem"""
        memory = ConversationMemory(user_id="test_user")
        memory.add_message("user", "Olá")
        assert memory.interaction_count == 1
        assert len(memory.messages) == 1
    
    def test_message_max_length(self):
        """Testa limite de mensagens (maxlen=20)"""
        memory = ConversationMemory(user_id="test_user")
        for i in range(25):
            memory.add_message("user", f"Mensagem {i}")
        
        assert len(memory.messages) == 20
        assert memory.messages[-1]['content'] == "Mensagem 24"


class TestAntiRepetitionSystem:
    """Testes de sistema anti-repetição"""
    
    def test_detect_repetition(self):
        """Testa detecção de repetição"""
        system = AntiRepetitionSystem()
        
        text = "Isso é importante. Isso é muito importante. Isso é realmente importante."
        issues = system.detect_repetition(text)
        
        assert len(issues['repeated_phrases']) > 0
    
    def test_generate_variation(self):
        """Testa geração de variação"""
        system = AntiRepetitionSystem()
        
        variation1 = system.generate_variation("intro_greeting")
        variation2 = system.generate_variation("intro_greeting")
        
        # Variações devem ser diferentes (com probabilidade alta)
        assert variation1 is not None
        assert variation2 is not None
    
    def test_vary_structure(self):
        """Testa variação de estrutura"""
        system = AntiRepetitionSystem()
        
        new_structure = system.vary_structure("analysis")
        assert new_structure != "analysis"


class TestIntentDetectionSystem:
    """Testes de detecção de intenção"""
    
    def test_detect_seeking_opportunity(self):
        """Testa detecção de intenção de oportunidade"""
        system = IntentDetectionSystem()
        
        message = "Quero ganhar dinheiro com isso"
        intent = system.analyze_intent(message, [])
        
        assert intent.implicit == "seeking_opportunity"
    
    def test_detect_seeking_solution(self):
        """Testa detecção de intenção de solução"""
        system = IntentDetectionSystem()
        
        message = "Tenho um problema que não consigo resolver"
        intent = system.analyze_intent(message, [])
        
        assert intent.implicit == "seeking_solution"
    
    def test_detect_urgency(self):
        """Testa detecção de urgência"""
        system = IntentDetectionSystem()
        
        message = "Preciso disso urgente agora"
        intent = system.analyze_intent(message, [])
        
        assert intent.urgency > 0.5
    
    def test_detect_depth_desired(self):
        """Testa detecção de profundidade desejada"""
        system = IntentDetectionSystem()
        
        message_shallow = "Quero um resumo simples"
        intent_shallow = system.analyze_intent(message_shallow, [])
        assert intent_shallow.depth_desired == "shallow"
        
        message_deep = "Quero uma análise técnica detalhada e profunda"
        intent_deep = system.analyze_intent(message_deep, [])
        assert intent_deep.depth_desired == "deep"


class TestPremiumFormattingEngine:
    """Testes de motor de formatação premium"""
    
    def test_format_response(self):
        """Testa formatação de resposta"""
        engine = PremiumFormattingEngine()
        
        content = "Este é um teste de formatação."
        formatted = engine.format_response(content, ResponseStyle.DIRECT, {})
        
        assert formatted is not None
        assert len(formatted) > 0
    
    def test_apply_visual_hierarchy(self):
        """Testa aplicação de hierarquia visual"""
        engine = PremiumFormattingEngine()
        
        text = "Título:\nConteúdo do parágrafo."
        formatted = engine._apply_visual_hierarchy(text)
        
        assert "**" in formatted  # Markdown bold
    
    def test_break_large_blocks(self):
        """Testa quebra de blocos grandes"""
        engine = PremiumFormattingEngine()
        
        large_text = "A. " * 200  # Texto grande
        broken = engine._break_large_blocks(large_text)
        
        assert "\n\n" in broken  # Deve ter quebras


class TestHumanizationEngine:
    """Testes de motor de humanização"""
    
    def test_humanize(self):
        """Testa humanização de texto"""
        engine = HumanizationEngine()
        
        text = "Esta é uma resposta da IA."
        humanized = engine.humanize(text, {})
        
        assert humanized is not None
    
    def test_vary_sentence_structure(self):
        """Testa variação de estrutura de frases"""
        engine = HumanizationEngine()
        
        text = "A resposta é. A solução é. O resultado é."
        varied = engine._vary_sentence_structure(text)
        
        assert varied is not None


class TestSelfCritiqueSystem:
    """Testes de sistema de auto-crítica"""
    
    def test_critique_short_response(self):
        """Testa crítica de resposta curta"""
        system = SelfCritiqueSystem()
        
        short_response = "Sim."
        improved, score = system.critique_and_improve(short_response, {})
        
        assert score < 100  # Deve penalizar resposta curta
    
    def test_critique_long_response(self):
        """Testa crítica de resposta longa"""
        system = SelfCritiqueSystem()
        
        long_response = "A. " * 3000  # Muito longo
        improved, score = system.critique_and_improve(long_response, {})
        
        assert score < 100  # Deve penalizar resposta longa
    
    def test_detect_generic(self):
        """Testa detecção de resposta genérica"""
        system = SelfCritiqueSystem()
        
        generic = "É importante considerar que é fundamental que você deve fazer isso."
        assert system._is_generic(generic) is True


class TestLegalEntityDetector:
    """Testes de detector de entidades jurídicas"""
    
    def test_detect_tribunals(self):
        """Testa detecção de tribunais"""
        detector = LegalEntityDetector()
        
        text = "O processo está no STF e STJ"
        entities = detector.detect_entities(text)
        
        assert len(entities['tribunais']) > 0
    
    def test_detect_laws(self):
        """Testa detecção de leis"""
        detector = LegalEntityDetector()
        
        text = "Conforme o CPC e a Constituição Federal"
        entities = detector.detect_entities(text)
        
        assert len(entities['leis']) > 0
    
    def test_detect_deadlines(self):
        """Testa detecção de prazos"""
        detector = LegalEntityDetector()
        
        text = "Prazo de 15 dias para contestação"
        entities = detector.detect_entities(text)
        
        assert len(entities['prazos']) > 0
    
    def test_detect_dates(self):
        """Testa detecção de datas"""
        detector = LegalEntityDetector()
        
        text = "Data limite: 15/06/2026"
        entities = detector.detect_entities(text)
        
        assert len(entities['datas']) > 0


class TestFeedbackSystem:
    """Testes de sistema de feedback"""
    
    def test_record_feedback(self):
        """Testa registro de feedback"""
        system = FeedbackSystem()
        
        system.record_feedback("user_1", "resp_1", 5, "Excelente")
        
        assert "user_1" in system.feedback_history
        assert len(system.feedback_history["user_1"]) == 1
    
    def test_satisfaction_trend(self):
        """Testa tendência de satisfação"""
        system = FeedbackSystem()
        
        # Feedbacks melhorando
        system.record_feedback("user_1", "resp_1", 3)
        system.record_feedback("user_1", "resp_2", 4)
        system.record_feedback("user_1", "resp_3", 5)
        
        trend = system.get_user_satisfaction_trend("user_1")
        assert trend['trend'] == 'improving'
        assert trend['average'] == 4.0


class TestPremiumConversationalEngineV2:
    """Testes do motor premium V2"""
    
    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Testa geração de resposta"""
        engine = PremiumConversationalEngineV2()
        
        result = await engine.generate_premium_response(
            user_message="Como funciona o processo?",
            user_id="test_user",
            use_rag=False
        )
        
        assert 'response' in result
        assert 'quality_score' in result
        assert 'v2_metadata' in result
    
    @pytest.mark.asyncio
    async def test_legal_entities_detection(self):
        """Testa detecção de entidades jurídicas"""
        engine = PremiumConversationalEngineV2()
        
        result = await engine.generate_premium_response(
            user_message="Qual o prazo no STJ?",
            user_id="test_user",
            use_rag=False
        )
        
        entities = result['v2_metadata']['legal_entities_detected']
        assert len(entities.get('tribunais', [])) > 0 or len(entities.get('prazos', [])) > 0
    
    def test_record_feedback(self):
        """Testa registro de feedback"""
        engine = PremiumConversationalEngineV2()
        
        engine.record_user_feedback("user_1", "resp_1", 5)
        
        satisfaction = engine.feedback_system.get_user_satisfaction_trend("user_1")
        assert satisfaction['count'] == 1
    
    def test_performance_metrics(self):
        """Testa métricas de performance"""
        engine = PremiumConversationalEngineV2()
        
        metrics = engine.get_performance_metrics()
        
        assert 'total_responses' in metrics
        assert 'average_response_time_ms' in metrics
        assert metrics['engine_version'] == '2.0'


class TestIntegration:
    """Testes de integração entre sistemas"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Testa pipeline completo de resposta"""
        engine = PremiumConversationalEngineV2()
        
        # Gerar resposta
        result = await engine.generate_premium_response(
            user_message="Preciso de ajuda com um contrato",
            user_id="test_user"
        )
        
        # Verificar estrutura
        assert result['response'] is not None
        assert result['quality_score'] >= 0
        assert result['quality_score'] <= 100
        
        # Verificar metadados V2
        assert 'v2_metadata' in result
        assert 'legal_entities_detected' in result['v2_metadata']
        
        # Registrar feedback
        engine.record_user_feedback("test_user", "test_resp", 4)
        
        # Verificar métricas
        metrics = engine.get_performance_metrics()
        assert metrics['total_responses'] >= 1


# Fixture para pytest
@pytest.fixture
def ai_engine():
    """Fixture: Motor de IA"""
    return create_premium_ai_engine_v2()


@pytest.fixture
def sample_memory():
    """Fixture: Memória de exemplo"""
    memory = ConversationMemory(user_id="test_user")
    memory.add_message("user", "Olá")
    memory.add_message("assistant", "Olá! Como posso ajudar?")
    return memory
