# 📧 MÓDULO 4: MARKETING OAB-COMPLIANCE

## Visão Geral
Sistema de marketing e relacionamento conforme Código de Ética da OAB, focado em conteúdo educativo e autoridade jurídica.

## Funcionalidades
- Email marketing educativo (artigos, mudanças legislação)
- Segmentação por área do direito, status cliente
- Sequência automática relacionamento
- Pesquisa satisfação pós-caso
- Funil captação: lead → consulta → proposta → contrato
- Qualificação automática leads por IA

## Restrições OAB Implementadas
- ✅ Apenas conteúdo educativo (proibida publicidade direta)
- ✅ Sem promessas de resultado
- ✅ Sem captação agressiva
- ✅ Sem comparação com outros advogados
- ✅ Auditoria todas comunicações

## Modelos de Dados
```python
class MarketingCampaign:
    user_id, name, description
    campaign_type  # educational, nurture, reengagement
    status, start_date, end_date
    target_segment
    open_rate, click_rate, conversion_rate

class EmailSequence:
    campaign_id, name
    sequence_type  # onboarding, reengagement, post_case
    steps  # [{order, delay_days, subject, template}]
    is_active, trigger_event

class Lead:
    user_id, source  # website, referral, social
    name, email, phone
    interest_area  # trabalhista, previdenciario
    qualification_score  # 0-100 (IA calcula)
    status  # new, contacted, qualified, converted, lost
    created_at, last_contact_at

class ClientSegment:
    user_id, name
    criteria  # {area, status, case_history, revenue}
    member_count

class SatisfactionSurvey:
    case_id, client_id
    sent_at, completed_at
    responses  # JSON com respostas
    nps_score, satisfaction_score
    feedback_text

class OABComplianceLog:
    message_id, content_preview
    compliance_check  # approved, flagged, rejected
    violation_type  # se houver
    reviewed_by, reviewed_at
```

## Rotas API
```python
GET/POST   /marketing/campaigns
GET/POST   /marketing/sequences
POST       /marketing/sequences/trigger
GET        /marketing/funnel/stats
GET/POST   /marketing/leads
POST       /marketing/surveys/send
GET        /marketing/compliance/logs
```

## Frontend
- Dashboard campanhas
- Editor emails (templates OAB-compliant)
- Segmentação visual
- Funil conversão
- Relatório compliance

## Roadmap 6-8 Semanas
```
Semana 1-2: Modelos + Backend
Semana 3-4: Sequências automáticas
Semana 5-6: Frontend + Templates
Semana 7-8: Compliance audit + Testes
```

## Estimativa
- Desenvolvimento: R$ 60.000

