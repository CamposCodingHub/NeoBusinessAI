# 🔍 MÓDULO 1: PESQUISA JURISPRUDENCIAL POR IA

## Visão Geral
Sistema inteligente de pesquisa de jurisprudência com busca em linguagem natural, análise de tendências por IA e geração de trechos formatados.

## Funcionalidades
- Busca em STJ, STF, TJSP, TRFs por tema ou linguagem natural
- Filtros: tribunal, data, resultado, relevância
- IA identifica jurisprudência dominante
- Trechos prontos para peças (formatados ABNT/OAB)
- Dashboard de tendências

## Modelos de Dados
```python
class JurisprudenciaSource:
    # Fontes (STJ, STF, TJSP, etc)
    court_code, court_name, court_type
    scraper_config, api_endpoint, api_auth_type
    is_active, last_sync_at, sync_frequency_hours
    total_decisions

class JurisprudenciaDecision:
    # Acórdãos armazenados
    process_number, decision_number, title
    summary, full_text, court, court_chamber
    decision_date, decision_type, result
    subject_matter, legal_tags, relevance_score
    dominant_tendency, source_url, pdf_url
    embedding_vector, search_vector

class JurisprudenciaSearchHistory:
    # Histórico de pesquisas
    user_id, query_text, query_type
    filters_applied, results_count
    ai_summary, dominant_tendency_detected
    suggested_citations

class JurisprudenciaSnippet:
    # Trechos salvos
    user_id, decision_id, snippet_text
    snippet_context, formatted_citation
    citation_style, tags, folder_name
    usage_count

class JurisprudenciaTendencyReport:
    # Relatórios de tendência
    user_id, court_analyzed, subject_matter
    date_from, date_to, total_decisions_analyzed
    favorable_count, unfavorable_count, partial_count
    tendency_conclusion, confidence_score
    recommended_strategy
```

## Rotas API
```python
GET  /jurisprudencia/sources           # Listar tribunais
POST /jurisprudencia/search            # Busca básica
POST /jurisprudencia/search/ai-analysis # Análise completa IA
GET  /jurisprudencia/snippets          # Meus trechos
POST /jurisprudencia/snippets/save     # Salvar trecho
GET  /jurisprudencia/history           # Histórico
POST /jurisprudencia/reports/tendency  # Relatório tendência
```

## Frontend (/dashboard/jurisprudencia)
- Tabs: Pesquisar | Análise IA | Meus Trechos | Histórico | Relatórios
- Search box com linguagem natural
- Filtros: tribunais (checkboxes), período, resultado
- Cards de resultados com relevância %
- Botões: Salvar Trecho, Copiar Citação, Ver Original
- Dashboard IA: estatísticas, tendência, trechos recomendados

## Roadmap 12 Semanas
```
Semana 1-2:  Modelos + Migração banco
Semana 3-4:  Scraper STJ + STF
Semana 5-6:  Backend completo + IA
Semana 7-8:  Frontend
Semana 9-10: TJSP + TRF3
Semana 11-12: Sync automático + Polimento
```

## Custo Operacional Mensal
- VPS scraping: R$ 200
- Storage S3: R$ 150 (crescendo)
- API Groq IA: R$ 300-500
- **Total: ~R$ 650-850/mês**

## Estimativa Desenvolvimento
- 3 devs backend × 8 semanas = 24 semanas-pessoa
- 2 devs frontend × 4 semanas = 8 semanas-pessoa
- **Total: ~R$ 180.000**

