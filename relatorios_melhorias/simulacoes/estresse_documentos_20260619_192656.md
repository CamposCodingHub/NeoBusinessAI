# Estresse extremo de documentos

- Resultado: 8/8 cenarios aprovados
- API: http://127.0.0.1:8000

| Cenario | Tamanho | Upload | Analise | Resultado |
|---|---:|---:|---:|---|
| large_txt | 12582620 | 200 | 202 | APROVADO |
| large_pdf | 227764 | 200 | 202 | APROVADO |
| large_docx | 94394 | 200 | 202 | APROVADO |
| large_rtf | 5242726 | 200 | 202 | APROVADO |
| official_irpf | 4751936 | 200 | 202 | APROVADO |
| page_limit_pdf | 455793 | 200 | 202 | APROVADO |
| oversized | 53477376 | 413 | - | APROVADO |
| disguised | 19 | 400 | - | APROVADO |
