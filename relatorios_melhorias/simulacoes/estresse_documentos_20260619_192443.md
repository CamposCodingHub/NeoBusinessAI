# Estresse extremo de documentos

- Resultado: 0/8 cenarios aprovados
- API: http://127.0.0.1:8000

| Cenario | Tamanho | Upload | Analise | Resultado |
|---|---:|---:|---:|---|
| large_txt | 12582620 | 200 | 202 | FALHOU |
| large_pdf | 227764 | 200 | 202 | FALHOU |
| large_docx | 94394 | 200 | 202 | FALHOU |
| large_rtf | 5242726 | 200 | 202 | FALHOU |
| official_irpf | 4751936 | 200 | 202 | FALHOU |
| page_limit_pdf | 455793 | 403 | - | FALHOU |
| oversized | 53477376 | 403 | - | FALHOU |
| disguised | 19 | 403 | - | FALHOU |
