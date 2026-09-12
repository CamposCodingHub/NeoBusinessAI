# Day — pesquisa mercado PMS BR (profissionalização)

## Concorrentes observados (2026)
- Projuris ADV — ERP jurídico + IA + multi-unidade
- JuriBR — hub lead→prazo→WhatsApp + multi-tenant/LGPD/RBAC
- Juridiq — intimações + WhatsApp cliente + MCP agents
- LinkLei — autônomos, DJEn/CNJ, Asaas PIX
- EbgLex — WhatsApp 24h + servidor dedicado

## Gaps que LexScan já cobre bem
- OCR→Lex→aprovação humana→WhatsApp
- Intake+COI, Matters, Portal, Time→Invoice
- IA soberana + grounding em códigos oficiais
- Trust ledger stub + Orgs multi-tenant MVP (hoje)

## Gaps ainda abertos para nível “enterprise BR”
1. **PIX/Asaas real** + NFS-e (LinkLei já vende isso)
2. **Monitor DJEn/DataJud** contínuo (intimações)
3. **API Meta WhatsApp oficial** + consentimento LGPD
4. **RBAC granular por org** (além de member/admin)
5. **Three-way trust reconciliation** mensal
6. **Assinatura eletrônica** (DocuSign/ClickSign)
7. **BI executivo** (receita por área, aging honorários)

## Prioridade restante até 17:00
- PIX payment stub → provider interface preparada para Asaas
- Playwright smoke CI mínimo
- RBAC org nas rotas críticas (documentos/matters) se der tempo
- Manter Lex afiada: eval + simulador após cada entrega
