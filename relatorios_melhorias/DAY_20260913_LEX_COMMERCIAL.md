# Lex comercial — 13/09/2026

## Objetivo
Elevar a Lex de “contingência crua” para experiência profissional/comercial (online e offline).

## Mudanças
1. **Ollama ligado** + modelos padrão apontando para `llama3.1:8b` (disponível no host)
2. **Addenda de domínio** injetada no system prompt (`professional_domains`)
3. **Contingência** virrou **Memo Lex — briefing fundamentado** (executivo + evidências + checklist)
4. Chat: welcome comercial, prompts úteis, banner de briefing
5. Login: dica de credenciais demo em development

## Validação
- `provider=local-primary` · `model=llama3.1:8b` · `contingency=false`
- Perguntas LGPD / prazos com grounding `official_sources`

## Como manter
```powershell
ollama serve   # se 11434 estiver down
# API com:
# AI_SOVEREIGN_ENABLED=true
# LOCAL_AI_QUICK_MODEL=llama3.1:8b
```
