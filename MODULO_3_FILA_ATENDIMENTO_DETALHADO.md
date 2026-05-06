# 💬 MÓDULO 3: FILA DE ATENDIMENTO INTELIGENTE

## Visão Geral
Sistema de fila inteligente para WhatsApp onde chatbot filtra perguntas simples e mensagens complexas entram em fila priorizada para atendimento humano.

## Funcionalidades
- Chatbot responde: andamento, prazos, faturas automaticamente
- Fila priorizada por urgência e tempo de espera
- Classificação automática: urgente, financeiro, processual, geral
- SLA monitoring com alertas
- Dashboard para advogado atender em momento de foco

## Modelos de Dados (extensão WhatsApp)
```python
class ChatQueue:
    message_id, client_id, user_id
    message_content, classification
    priority_score, wait_time_minutes
    sla_deadline, status  # waiting, assigned, resolved
    assigned_to_member_id
    ai_handled, ai_response
    human_required_reason

class ChatClassification:
    message_id, classification_type
    # urgente, financeiro, processual, geral
    confidence_score
    extracted_entities  # prazos, valores, processos
    suggested_response

class SLAMonitor:
    queue_item_id, sla_minutes
    deadline, status  # within_sla, at_risk, breached
    notification_sent
```

## Fluxo de Atendimento
```
Mensagem Cliente
    ↓
[IA Classifica]
    ↓
├─ Simples (andamento/prazo/fatura) → Chatbot responde
└─ Complexo → Entra na Fila
                ↓
        [Priorização]
                ↓
        Dashboard Advogado
                ↓
        Responde quando puder
                ↓
        Marca como resolvido
```

## Rotas API
```python
GET    /whatsapp/queue              # Fila de atendimento
POST   /whatsapp/queue/classify     # Classificar mensagem
GET    /whatsapp/queue/stats        # Estatísticas SLA
POST   /whatsapp/queue/assign       # Atribuir a advogado
POST   /whatsapp/queue/resolve      # Marcar resolvido
POST   /whatsapp/queue/escalate   # Escalar prioridade
```

## Frontend - Dashboard de Atendimento
```
┌─────────────────────────────────────┐
│  📥 Fila de Atendimento (5)         │
├─────────────────────────────────────┤
│ 🔴 Urgente (1)                     │
│ • João Silva - Processo 12345      │
│   "Audiência adiada, quando é?"    │
│   Espera: 45min | SLA: 10min ⚠️    │
│   [Atender Agora]                  │
├─────────────────────────────────────┤
│ 🟡 Financeiro (2)                  │
│ • Maria Souza - Fatura em atraso   │
│ • Empresa ABC - Dúvida honorários  │
├─────────────────────────────────────┤
│ 🔵 Processual (1)                  │
│ • Carlos - Andamento reclamação    │
├─────────────────────────────────────┤
│ ⚪ Geral (1)                        │
│ • Ana - Saudação inicial           │
└─────────────────────────────────────┘
```

## Roadmap 6-8 Semanas
```
Semana 1-2: Modelos + Backend
Semana 3-4: IA Classificação + Chatbot
Semana 5-6: Frontend dashboard
Semana 7-8: SLA monitoring + Testes
```

## Estimativa
- Desenvolvimento: R$ 60.000
- Infra: usa existente

