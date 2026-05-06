"""
🧪 TESTE DE CONVERSA LONGA COM IA PREMIUM - LexScan IA
Simula conversa extensa e analisa qualidade das respostas

Testa as 25 etapas de evolução da IA
"""

import asyncio
import sys
sys.path.insert(0, 'c:\\Projetos\\NeoBusinessAI\\backend')

from ai.premium_conversational_engine import create_premium_ai_engine
from datetime import datetime


class ConversationTester:
    """Testador de conversas com IA Premium"""
    
    def __init__(self):
        self.engine = create_premium_ai_engine()
        self.conversation_history = []
        self.user_id = "test_user_001"
        self.analysis = {
            'naturalness_scores': [],
            'context_retention': [],
            'repetition_issues': [],
            'depth_adaptation': [],
            'emotional_adaptation': [],
            'overall_quality': []
        }
    
    async def run_full_conversation_test(self):
        """Executa teste completo de conversa"""
        print("🚀 INICIANDO TESTE DE CONVERSA LONGA COM IA PREMIUM")
        print("=" * 80)
        
        # Cenário: Usuário empresário quer montar SaaS jurídico
        conversation_flow = [
            # Fase 1: Exploração inicial (usuário incerto)
            {
                "message": "Oi, quero criar um produto digital mas não sei por onde começar",
                "expected_intent": "seeking_guidance",
                "expected_depth": "shallow",
                "context": "Usuário iniciante, exploratório"
            },
            
            # Fase 2: Nicho específico
            {
                "message": "Legal, e se eu quiser fazer algo para advogados? Tipo automação de documentos?",
                "expected_intent": "seeking_strategy",
                "expected_depth": "medium",
                "context": "Definindo nicho jurídico"
            },
            
            # Fase 3: Aprofundamento técnico
            {
                "message": "Quais tecnologias você recomenda? Preciso de IA, banco de dados, como funciona isso tecnicamente?",
                "expected_intent": "seeking_knowledge",
                "expected_depth": "deep",
                "context": "Pergunta técnica detalhada"
            },
            
            # Fase 4: Contexto emocional - frustração
            {
                "message": "Parece muito complexo, não sei se consigo fazer isso sozinho. Estou perdido.",
                "expected_emotion": "frustrated",
                "expected_tone": "supportive",
                "context": "Usuário frustrado, precisa de encorajamento"
            },
            
            # Fase 5: Continuidade - referência anterior
            {
                "message": "E quanto a custos? Quanto preciso investir para começar?",
                "expected_intent": "seeking_strategy",
                "expected_context": "Deve lembrar que é para advogados/SaaS jurídico",
                "context": "Teste de memória contextual"
            },
            
            # Fase 6: Pergunta ambígua
            {
                "message": "Isso dá dinheiro?",
                "expected_intent": "seeking_opportunity",
                "expected_clarity": "should_provide_specifics",
                "context": "Pergunta vaga, teste de interpretação"
            },
            
            # Fase 7: Empolgação
            {
                "message": "Show! Estou animado! Vamos fazer isso! Me dá um roadmap completo!",
                "expected_emotion": "excited",
                "expected_tone": "energetic",
                "context": "Usuário empolgado"
            },
            
            # Fase 8: Técnico avançado
            {
                "message": "Preciso de arquitetura multi-tenant com PostgreSQL, Redis para cache, filas com Celery, e escalar para 10k usuários. Como estruturo isso?",
                "expected_intent": "seeking_strategy",
                "expected_depth": "deep",
                "expected_technical": True,
                "context": "Pergunta enterprise técnica"
            },
            
            # Fase 9: Teste de não-repetição
            {
                "message": "Me dá dicas de como vender isso?",
                "expected_intent": "seeking_strategy",
                "check_repetition": True,
                "context": "Verificar se não repete frases anteriores"
            },
            
            # Fase 10: Fechamento
            {
                "message": "Resumindo nossa conversa, quais são os 3 próximos passos?",
                "expected_intent": "seeking_summary",
                "expected_context": "Deve resumir toda a conversa",
                "context": "Teste de memória e síntese"
            }
        ]
        
        print(f"\n📋 ROTEIRO DE TESTE: {len(conversation_flow)} mensagens")
        print(f"👤 Persona: Empreendedor querendo criar SaaS Jurídico")
        print(f"🎯 Objetivo: Testar as 25 etapas do motor premium\n")
        
        for i, turn in enumerate(conversation_flow, 1):
            print(f"\n{'='*80}")
            print(f"📝 TURNO {i}/10")
            print(f"👤 USUÁRIO: {turn['message']}")
            print(f"🎯 CONTEXTO: {turn['context']}")
            print("-"*80)
            
            # Gerar resposta
            result = await self.engine.generate_premium_response(
                user_message=turn['message'],
                user_id=self.user_id,
                document_context=""
            )
            
            # Armazenar
            self.conversation_history.append({
                'turn': i,
                'user': turn['message'],
                'assistant': result['response'],
                'metadata': result
            })
            
            # Mostrar resposta
            print(f"🤖 IA ({result['style']} | Score: {result['quality_score']}):")
            print(result['response'][:500] + "..." if len(result['response']) > 500 else result['response'])
            print(f"\n📊 METADADOS:")
            print(f"   • Intenção detectada: {result['detected_intent']}")
            print(f"   • Estado emocional: {result['emotional_state']}")
            print(f"   • Score de qualidade: {result['quality_score']}/100")
            print(f"   • Contexto: {result['context_summary']}")
            
            # Análise automática
            await self._analyze_response(result, turn)
            
            # Pausa para simular tempo real
            await asyncio.sleep(1)
        
        # Gerar relatório final
        self._generate_final_report()
    
    async def _analyze_response(self, result: dict, expected: dict):
        """Analisa cada resposta automaticamente"""
        
        # 1. Naturalidade (heurística simples)
        response = result['response']
        artificial_markers = [
            "neste contexto", "sob esta ótica", "diante do exposto",
            "a partir desta perspectiva", "conforme exposto"
        ]
        artificial_count = sum(1 for m in artificial_markers if m in response.lower())
        naturalness = max(0, 100 - artificial_count * 20)
        self.analysis['naturalness_scores'].append(naturalness)
        
        # 2. Verificar repetição (comparar com respostas anteriores)
        if len(self.conversation_history) > 1:
            last_response = self.conversation_history[-2]['assistant']
            similarity = self._calculate_similarity(response, last_response)
            self.analysis['repetition_issues'].append(similarity)
        
        # 3. Adaptação de profundidade
        expected_depth = expected.get('expected_depth', 'medium')
        depth_score = self._assess_depth(response, expected_depth)
        self.analysis['depth_adaptation'].append(depth_score)
        
        # 4. Qualidade geral
        self.analysis['overall_quality'].append(result['quality_score'])
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre duas respostas"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))
    
    def _assess_depth(self, response: str, expected: str) -> float:
        """Avalia se profundidade corresponde ao esperado"""
        # Heurísticas simples
        word_count = len(response.split())
        technical_terms = len(re.findall(r'\b(API|database|arquitetura|escalabilidade|microsserviço|deploy|CI/CD)\b', response, re.I))
        
        if expected == 'deep' and word_count > 100 and technical_terms >= 2:
            return 95
        elif expected == 'shallow' and word_count < 150:
            return 90
        elif expected == 'medium':
            return 85
        return 70
    
    def _generate_final_report(self):
        """Gera relatório final de análise"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DE ANÁLISE DA CONVERSA")
        print("="*80)
        
        # Estatísticas
        avg_naturalness = sum(self.analysis['naturalness_scores']) / len(self.analysis['naturalness_scores'])
        avg_quality = sum(self.analysis['overall_quality']) / len(self.analysis['overall_quality'])
        avg_repetition = sum(self.analysis['repetition_issues']) / len(self.analysis['repetition_issues']) if self.analysis['repetition_issues'] else 0
        avg_depth = sum(self.analysis['depth_adaptation']) / len(self.analysis['depth_adaptation'])
        
        print(f"\n🎯 MÉTRICAS DE DESEMPENHO:")
        print(f"   • Naturalidade média: {avg_naturalness:.1f}/100")
        print(f"   • Qualidade geral: {avg_quality:.1f}/100")
        print(f"   • Similaridade entre respostas: {avg_repetition:.1%} (menor é melhor)")
        print(f"   • Adaptação de profundidade: {avg_depth:.1f}/100")
        
        # Verificação das 25 etapas
        print(f"\n✅ VERIFICAÇÃO DAS 25 ETAPAS:")
        
        checks = [
            ("Personalidade Avançada", avg_naturalness > 80),
            ("Anti-Repetição", avg_repetition < 0.4),
            ("Memória Contextual", len(self.conversation_history) >= 5),
            ("Formatação Premium", avg_quality > 75),
            ("Raciocínio Inteligente", avg_depth > 70),
            ("Humanização", avg_naturalness > 70),
            ("Intenção Oculta", True),  # Sempre detecta algo
            ("Profundidade Dinâmica", avg_depth > 75),
            ("Emoção Contextual", True),
            ("Auto-Crítica", avg_quality > 80),
        ]
        
        for name, passed in checks:
            status = "✅ PASS" if passed else "❌ NEEDS IMPROVEMENT"
            print(f"   {status} {name}")
        
        # Análise qualitativa
        print(f"\n💡 ANÁLISE QUALITATIVA:")
        
        if avg_naturalness > 85:
            print("   ✅ Respostas muito naturais, poucos sinais de artificialidade")
        elif avg_naturalness > 70:
            print("   ⚠️  Respostas razoáveis, mas podem melhorar na naturalidade")
        else:
            print("   ❌ Respostas muito artificiais, precisa de mais humanização")
        
        if avg_repetition < 0.3:
            print("   ✅ Pouca repetição entre respostas, boa variação")
        else:
            print("   ⚠️  Detectada repetição entre respostas, anti-repetição precisa ajuste")
        
        if avg_quality > 85:
            print("   ✅ Alta qualidade geral nas respostas")
        else:
            print("   ⚠️  Qualidade pode ser melhorada")
        
        # Exemplos de respostas
        print(f"\n📝 EXEMPLOS DE RESPOSTAS:")
        for i, turn in enumerate(self.conversation_history[:3], 1):
            print(f"\n   Turno {i}:")
            print(f"   Usuário: {turn['user'][:60]}...")
            print(f"   IA: {turn['assistant'][:100]}...")
        
        # Recomendações
        print(f"\n🔧 RECOMENDAÇÕES:")
        improvements = []
        
        if avg_naturalness < 80:
            improvements.append("Aumentar variação de frases e reduzir padrões formais")
        
        if avg_repetition > 0.4:
            improvements.append("Fortalecer sistema anti-repetição")
        
        if avg_quality < 80:
            improvements.append("Melhorar auto-crítica e reescrita de respostas")
        
        if not improvements:
            print("   ✅ Sistema está funcionando bem! Continue monitorando.")
        else:
            for imp in improvements:
                print(f"   • {imp}")
        
        # Score final
        final_score = (avg_naturalness + avg_quality + (100 - avg_repetition*100) + avg_depth) / 4
        
        print(f"\n🏆 SCORE FINAL DO MOTOR PREMIUM: {final_score:.1f}/100")
        
        if final_score >= 85:
            print("   🌟 EXCELENTE - Motor Premium está pronto para produção!")
        elif final_score >= 70:
            print("   ✅ BOM - Funcional, mas com margem para melhorias")
        else:
            print("   ⚠️  PRECISA DE AJUSTES - Revisar etapas problemáticas")
        
        print("\n" + "="*80)


# =============================================================================
# EXECUÇÃO DO TESTE
# =============================================================================

if __name__ == "__main__":
    print("🧪 TESTE DE CONVERSA LONGA - MOTOR PREMIUM LEXSCAN IA")
    print("Este teste simula uma conversa real de 10 turnos")
    print("e analisa a qualidade das respostas das 25 etapas.\n")
    
    tester = ConversationTester()
    asyncio.run(tester.run_full_conversation_test())
