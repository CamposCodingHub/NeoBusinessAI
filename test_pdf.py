#!/usr/bin/env python3
"""
Teste específico do sistema de PDF - LexScan IA
"""

import sys
import os
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/ai')
sys.path.insert(0, 'backend/tools')

print("=" * 70)
print("TESTE DO SISTEMA DE PDF")
print("=" * 70)

# Teste 1: Importar módulo
print("\n[1/4] Importando PDF Generator...")
try:
    from pdf_generator import pdf_generator
    print("[OK] PDF Generator importado com sucesso!")
except Exception as e:
    print(f"[ERRO] Falha ao importar: {e}")
    sys.exit(1)

# Teste 2: Criar dados de exemplo
print("\n[2/4] Criando dados de teste...")
test_doc = {
    'id': 1,
    'filename': 'Processo_12345.pdf',
    'type': 'peticao_inicial',
    'process_number': '12345-67.2024.8.26.0001',
    'parties': {
        'autor': 'Joao Silva',
        'reu': 'Empresa ABC Ltda',
        'advogado': 'Dr. Carlos Mendes OAB/SP 123456'
    },
    'deadlines': [
        {'days': '15', 'urgency': 'high', 'context': 'Prazo para contestacao'},
        {'days': '30', 'urgency': 'medium', 'context': 'Prazo para recurso'}
    ],
    'values': [{'value': 'R$ 50.000,00', 'context': 'Valor da causa'}],
    'analysis': 'Documento analisado com sucesso.',
    'summary': 'Acao de indenizacao por danos morais.',
    'court': 'Vara da Justica Civil de Sao Paulo',
    'uploaded_at': '2024-01-15T10:30:00',
    'status': 'processed'
}
print("[OK] Dados criados!")

# Teste 3: Gerar relatório de documento
print("\n[3/4] Gerando relatorio de documento...")
try:
    pdf_buffer = pdf_generator.generate_document_report(test_doc)
    pdf_size = len(pdf_buffer.getvalue())
    
    if pdf_size > 1000:
        print(f"[OK] PDF gerado com sucesso!")
        print(f"[INFO] Tamanho: {pdf_size} bytes")
        print(f"[INFO] Arquivo: relatorio_Processo_12345_pdf.pdf")
    else:
        print(f"[AVISO] PDF muito pequeno ({pdf_size} bytes)")
        
except Exception as e:
    print(f"[ERRO] Falha ao gerar PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 4: Gerar relatório de dashboard
print("\n[4/4] Gerando relatorio de dashboard...")
try:
    test_stats = {
        'total_documents': 5,
        'total_deadlines': 8,
        'urgent_deadlines': 2,
        'document_types': {'peticao_inicial': 3, 'contestacao': 2},
        'last_upload': '2024-01-15'
    }
    
    test_docs = [test_doc]
    test_deadlines = [
        {
            'document_id': 1,
            'document_name': 'Processo_12345.pdf',
            'document_type': 'peticao_inicial',
            'deadline': {'days': '15', 'urgency': 'high', 'context': 'Prazo para contestacao'},
            'urgency': 'high'
        }
    ]
    
    pdf_buffer = pdf_generator.generate_dashboard_report(test_stats, test_docs, test_deadlines)
    pdf_size = len(pdf_buffer.getvalue())
    
    if pdf_size > 1000:
        print(f"[OK] Dashboard PDF gerado com sucesso!")
        print(f"[INFO] Tamanho: {pdf_size} bytes")
    else:
        print(f"[AVISO] PDF muito pequeno ({pdf_size} bytes)")
        
except Exception as e:
    print(f"[ERRO] Falha ao gerar dashboard PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("[SUCESSO] SISTEMA DE PDF FUNCIONANDO CORRETAMENTE!")
print("=" * 70)
print("\nEndpoints disponiveis:")
print("  GET /api/documents/{id}/report    - Relatorio de documento")
print("  GET /api/reports/dashboard        - Relatorio geral")
print("\nTeste concluido!")
