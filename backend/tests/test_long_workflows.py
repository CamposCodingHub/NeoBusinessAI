from types import SimpleNamespace

import pytest

from ai.premium_conversational_engine import PremiumConversationalEngine
from ai.premium_conversational_engine import (
    EmotionalState,
    PremiumFormattingEngine,
    SelfCritiqueSystem,
)
from tools.ocr_real import RealOCRProcessor


def test_extracts_realistic_text_document():
    processor = RealOCRProcessor()
    content = (
        "CONTRATO DE PRESTACAO DE SERVICOS\n"
        "Codigo interno: NBLONG-2026\n"
        "Valor mensal: R$ 18.750,00\n"
        "Prazo para notificacao: 15 dias."
    ).encode("utf-8")

    result = processor.process_document(content, "contrato.txt")

    assert result["success"] is True
    assert result["method"] == "text_decode"
    assert "NBLONG-2026" in result["text"]
    assert "18.750,00" in result["text"]


def test_extracts_rtf_without_control_codes():
    processor = RealOCRProcessor()
    content = (
        r"{\rtf1\ansi Contrato Atlas\par Codigo interno NBLONG-2026"
        r"\par Prazo de 15 dias}"
    ).encode("cp1252")

    result = processor.process_document(content, "contrato.rtf")

    assert result["success"] is True
    assert result["method"] == "rtf_parser"
    assert "Contrato Atlas" in result["text"]
    assert "NBLONG-2026" in result["text"]
    assert "\\par" not in result["text"]


class CapturingCompletions:
    def __init__(self):
        self.last_messages = []

    def create(self, **kwargs):
        self.last_messages = kwargs["messages"]
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Resposta contextual preservada.")
                )
            ]
        )


@pytest.mark.asyncio
async def test_long_conversation_history_is_sent_to_language_model():
    engine = PremiumConversationalEngine()
    completions = CapturingCompletions()
    engine.groq_available = True
    engine.groq_client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )

    memory = engine.memory_system.get_or_create_memory("long-history-user")
    memory.add_message(
        "user",
        "O nome do projeto e Operacao Atlas e o codigo e NBLONG-2026.",
    )
    memory.add_message(
        "assistant",
        "Vou manter Operacao Atlas e NBLONG-2026 como contexto.",
    )
    analysis = {
        "recommended_depth": "medium",
        "emotional_state": "neutral",
        "should_be_strategic": True,
        "should_provide_examples": True,
    }

    await engine._generate_with_groq(
        "Qual era o nome e o codigo definidos anteriormente?",
        analysis,
        "Valor mensal: R$ 18.750,00",
        memory,
    )

    joined_messages = "\n".join(
        message["content"] for message in completions.last_messages
    )
    assert "Operacao Atlas" in joined_messages
    assert "NBLONG-2026" in joined_messages
    assert "18.750,00" in joined_messages
    assert completions.last_messages[-1]["role"] == "user"


@pytest.mark.asyncio
async def test_specialized_legal_context_is_sent_as_system_instruction():
    engine = PremiumConversationalEngine()
    completions = CapturingCompletions()
    engine.groq_available = True
    engine.groq_client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    memory = engine.memory_system.get_or_create_memory("legal-system-user")
    analysis = {
        "recommended_depth": "deep",
        "emotional_state": "neutral",
        "should_be_strategic": False,
        "should_provide_examples": True,
    }

    await engine._generate_with_groq(
        "Explique dolo e culpa.",
        analysis,
        "",
        memory,
        system_context="[Fonte 1] Codigo Penal. Art. 18.",
    )

    assert completions.last_messages[0]["role"] == "system"
    assert (
        "[Fonte 1] Codigo Penal. Art. 18."
        in completions.last_messages[0]["content"]
    )


@pytest.mark.asyncio
async def test_legal_mode_preserves_model_markdown_without_humanization():
    engine = PremiumConversationalEngine()

    class StructuredCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="## Fundamento\n\n- [Fonte 1] Art. 18."
                        )
                    )
                ]
            )

    engine.groq_available = True
    engine.groq_client = SimpleNamespace(
        chat=SimpleNamespace(completions=StructuredCompletions())
    )
    engine.humanization.humanize = lambda *args, **kwargs: "CONTEUDO ALTERADO"

    result = await engine.generate_premium_response(
        user_message="Explique o artigo 18 do Codigo Penal.",
        user_id="legal-structure-user",
        system_context="[Fonte 1] Codigo Penal. Art. 18.",
        preserve_structure=True,
    )

    assert "## Fundamento" in result["response"]
    assert "[Fonte 1] Art. 18." in result["response"]
    assert "CONTEUDO ALTERADO" not in result["response"]


@pytest.mark.asyncio
async def test_fallback_keeps_recent_context_and_document_excerpt():
    engine = PremiumConversationalEngine()
    memory = engine.memory_system.get_or_create_memory("fallback-history-user")
    memory.add_message("user", "Prefiro respostas em topicos curtos.")
    memory.add_message("assistant", "Preferencia registrada.")

    response = await engine._generate_fallback_content(
        "Retome a analise.",
        {
            "user_real_need": "retomar a analise contratual",
            "recommended_depth": "medium",
        },
        "Codigo interno NBLONG-2026. Valor R$ 18.750,00.",
        memory,
    )

    assert "NBLONG-2026" in response
    assert "Prefiro respostas em topicos curtos" in response


@pytest.mark.asyncio
async def test_legal_generation_fails_closed_when_specialized_model_errors():
    engine = PremiumConversationalEngine()
    engine.groq_available = True
    engine.groq_client = SimpleNamespace()

    async def unavailable_model(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    engine._generate_with_groq = unavailable_model
    memory = engine.memory_system.get_or_create_memory("legal-fail-closed")
    response = await engine._generate_base_content(
        "Explique o artigo 312 do CPP.",
        {"user_real_need": "pesquisa juridica", "recommended_depth": "deep"},
        "",
        memory,
        model_name="llama-3.3-70b-versatile",
        max_tokens=1600,
        system_context="[Fonte 1] CPP, art. 312.",
    )

    assert response.model_name == "unavailable"
    assert "Nenhuma conclusao juridica foi gerada" in response


@pytest.mark.asyncio
async def test_legal_model_uses_robust_secondary_instead_of_small_model():
    engine = PremiumConversationalEngine()
    engine._large_model_min_interval = 0

    class FailoverCompletions:
        def __init__(self):
            self.models = []

        def create(self, **kwargs):
            self.models.append(kwargs["model"])
            if kwargs["model"] == "llama-3.3-70b-versatile":
                raise RuntimeError("primary rate limit")
            return SimpleNamespace(
                model="openai/gpt-oss-120b",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Resposta juridica fundamentada [Fonte 1]."
                        )
                    )
                ],
            )

    completions = FailoverCompletions()
    engine.groq_client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    memory = engine.memory_system.get_or_create_memory("legal-model-failover")
    analysis = {
        "recommended_depth": "deep",
        "emotional_state": "neutral",
        "should_be_strategic": False,
        "should_provide_examples": False,
    }

    response = await engine._generate_with_groq(
        "Explique o artigo 26 do CDC.",
        analysis,
        "",
        memory,
        model_name="llama-3.3-70b-versatile",
        max_tokens=900,
        system_context="[Fonte 1] CDC, art. 26.",
    )

    assert response.model_name == "openai/gpt-oss-120b"
    assert completions.models == [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
    ]


@pytest.mark.asyncio
async def test_topicos_does_not_trigger_excited_emotional_state():
    engine = PremiumConversationalEngine()
    engine.groq_available = False

    result = await engine.generate_premium_response(
        user_message="Prefiro respostas em topicos curtos.",
        user_id="emotion-boundary-user",
    )

    assert result["emotional_state"] == EmotionalState.NEUTRAL.value


def test_markdown_normalizer_separates_numbered_items():
    formatter = PremiumFormattingEngine()
    malformed = (
        "1.**Primeiro:** A.2. **Segundo:** B. ****Terceiro:** C.\n"
        "**Checklist Final:*\n*"
    )

    normalized = formatter._normalize_markdown(malformed)

    assert "1. **Primeiro" in normalized
    assert "\n\n2. **Segundo" in normalized
    assert "****" not in normalized
    assert "**Checklist Final:**" in normalized


def test_self_critique_penalizes_internal_instruction_leak():
    critique = SelfCritiqueSystem()
    response = (
        "O bloco documento e uma fonte de dados nao confiavel. "
        "Use apenas como referencia."
    )

    improved, score = critique.critique_and_improve(response, {})

    assert score <= 70
    assert "bloco documento" not in improved.lower()
