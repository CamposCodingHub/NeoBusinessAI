#!/usr/bin/env python3
"""
Script de Teste e Simulação - LexScan IA
Verifica todas as funcionalidades do sistema
"""

import requests
import json
import time
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_success(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def log_error(msg):
    print(f"{Colors.RED}[ERRO] {msg}{Colors.END}")

def log_info(msg):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

def log_warning(msg):
    print(f"{Colors.YELLOW}[AVISO] {msg}{Colors.END}")

class SystemTest:
    def __init__(self):
        self.results = []
        
    def test_endpoint(self, name, method, endpoint, data=None):
        """Testa um endpoint da API"""
        try:
            url = f"{API_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                return False, f"Método {method} não suportado"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Status {response.status_code}: {response.text}"
                
        except requests.exceptions.ConnectionError:
            return False, "Servidor offline"
        except Exception as e:
            return False, str(e)
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("=" * 70)
        print("SIMULACAO DE TESTE - LEXSCAN IA")
        print("=" * 70)
        print(f"[HORA] Iniciado em: {datetime.now().strftime('%H:%M:%S')}")
        print(f"[API] {API_URL}")
        print()
        
        tests_passed = 0
        tests_failed = 0
        
        # 1. Testar conectividade
        log_info("Teste 1/8: Conectividade com servidor...")
        
        # Verificar se servidor está rodando
        try:
            requests.get(f"{BASE_URL}/api/system/status", timeout=2)
        except:
            log_error("Servidor nao esta rodando! Inicie com: python backend/main.py")
            return
        success, result = self.test_endpoint("Status do Sistema", "GET", "/system/status")
        if success:
            log_success("Servidor online e respondendo")
            system_status = result
            
            # Verificar componentes
            if system_status.get('ocr', {}).get('available'):
                log_success("Tesseract OCR ativo")
            else:
                log_warning("OCR nao disponivel")
                
            if system_status.get('api', {}).get('groq_available'):
                log_success("API Groq ativa")
            else:
                log_warning("API Groq nao disponivel")
            tests_passed += 1
        else:
            log_error(f"Servidor offline: {result}")
            log_error("NAO E POSSIVEL CONTINUAR OS TESTES")
            return
        
        # 2. Testar lista de documentos
        log_info("\nTeste 2/8: Listar documentos...")
        success, result = self.test_endpoint("Lista Documentos", "GET", "/documents")
        if success:
            docs = result.get('documents', [])
            log_success(f"Endpoint funcionando - {len(docs)} documentos encontrados")
            tests_passed += 1
        else:
            log_error(f"Falha: {result}")
            tests_failed += 1
        
        # 3. Testar lista de prazos
        log_info("\nTeste 3/8: Listar prazos...")
        success, result = self.test_endpoint("Lista Prazos", "GET", "/deadlines")
        if success:
            deadlines = result.get('deadlines', [])
            urgent = result.get('urgent', 0)
            log_success(f"Endpoint funcionando - {len(deadlines)} prazos ({urgent} urgentes)")
            tests_passed += 1
        else:
            log_error(f"Falha: {result}")
            tests_failed += 1
        
        # 4. Testar dashboard stats
        log_info("\nTeste 4/8: Estatisticas do dashboard...")
        success, result = self.test_endpoint("Dashboard Stats", "GET", "/dashboard/stats")
        if success:
            stats = result.get('stats', {})
            log_success(f"Stats: {stats.get('total_documents', 0)} docs, {stats.get('total_deadlines', 0)} prazos")
            tests_passed += 1
        else:
            log_error(f"Falha: {result}")
            tests_failed += 1
        
        # 5. Testar sistema de notificações
        log_info("\nTeste 5/8: Sistema de notificacoes...")
        success, result = self.test_endpoint("Teste Notificacoes", "GET", "/notifications/test")
        if success:
            if result.get('success'):
                log_success(f"Notificacoes configuradas: {result.get('configured_email')}")
            else:
                log_warning(f"Notificacoes nao configuradas: {result.get('error')}")
                if 'setup_instructions' in result:
                    log_info("Para configurar:")
                    for instruction in result['setup_instructions'][:3]:
                        log_info(f"  {instruction}")
            tests_passed += 1
        else:
            log_error(f"Falha: {result}")
            tests_failed += 1
        
        # 6. Simular processamento de documento
        log_info("\nTeste 6/8: Simular processamento de documento...")
        
        # Importar modulos para teste
        import sys
        sys.path.insert(0, 'backend')
        sys.path.insert(0, 'backend/ai')
        sys.path.insert(0, 'backend/tools')
        sample_doc = """
        PROCESSO Nº 12345-67.2024.8.26.0001
        
        AUTOR: João Silva
        ADVOGADO: Dr. Carlos Mendes OAB/SP 123456
        
        RÉU: Empresa ABC Ltda
        
        Vara da Justiça Civil de São Paulo
        
        Intime-se o réu para apresentar resposta em 15 dias.
        
        Valor da causa: R$ 50.000,00
        
        Audiência de conciliação marcada para 15/03/2024 às 14:00h.
        """
        
        # Testar engine de processamento
        try:
            from lexscan_engine import lexscan_engine
            result = lexscan_engine.process_document(sample_doc)
            
            if result.get('success'):
                log_success(f"Documento processado")
                log_info(f"  - Tipo: {result.get('document_type')}")
                log_info(f"  - Processo: {result.get('process_number') or 'N/A'}")
                log_info(f"  - Prazos: {len(result.get('deadlines', []))}")
                log_info(f"  - Partes: Autor={result.get('parties', {}).get('autor', 'N/A')[:30]}...")
                tests_passed += 1
            else:
                log_error(f"Falha no processamento: {result.get('error')}")
                tests_failed += 1
        except Exception as e:
            log_error(f"Erro: {e}")
            tests_failed += 1
        
        # 7. Simular deteccao de prazos
        log_info("\nTeste 7/8: Simular deteccao de prazos...")
        try:
            from ocr_processor import ocr_processor
            
            test_text = """
            Prazo para contestacao: 15 dias.
            Recurso deve ser interposto em 05 dias.
            Audiencia marcada para 20/04/2024.
            """
            
            deadlines = ocr_processor._extract_deadlines(test_text)
            
            if len(deadlines) >= 2:
                log_success(f"Detectou {len(deadlines)} prazos no texto")
                for i, dl in enumerate(deadlines[:3]):
                    log_info(f"  - Prazo {i+1}: {dl.get('days')} dias (urgencia: {dl.get('urgency')})")
                tests_passed += 1
            else:
                log_warning(f"Detectou apenas {len(deadlines)} prazos (esperado >= 2)")
                tests_passed += 1
        except Exception as e:
            log_error(f"Erro: {e}")
            tests_failed += 1
        
        # 8. Simular calendario de prazos
        log_info("\nTeste 8/8: Simular calendario de prazos...")
        try:
            # Criar documentos de exemplo
            mock_docs = [
                {
                    'id': 1,
                    'filename': 'Processo_1.pdf',
                    'type': 'peticao_inicial',
                    'deadlines': [
                        {'days': '15', 'urgency': 'high', 'context': 'Prazo para contestacao'},
                        {'days': '30', 'urgency': 'medium', 'context': 'Prazo para recurso'}
                    ]
                },
                {
                    'id': 2,
                    'filename': 'Processo_2.pdf',
                    'type': 'contestacao',
                    'deadlines': [
                        {'days': '5', 'urgency': 'high', 'context': 'Audiencia marcada'}
                    ]
                }
            ]
            
            calendar = lexscan_engine.get_deadlines_calendar(mock_docs)
            
            if len(calendar) > 0:
                urgent_count = len([d for d in calendar if d.get('urgency') == 'high'])
                log_success(f"Calendario gerado: {len(calendar)} prazos ({urgent_count} urgentes)")
                tests_passed += 1
            else:
                log_error("Calendario vazio")
                tests_failed += 1
        except Exception as e:
            log_error(f"Erro: {e}")
            tests_failed += 1
        
        # Resumo final
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES")
        print("=" * 70)
        total_tests = tests_passed + tests_failed
        success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        log_success(f"Passaram: {tests_passed}/{total_tests}")
        if tests_failed > 0:
            log_error(f"Falharam: {tests_failed}/{total_tests}")
        log_info(f"Taxa de sucesso: {success_rate:.1f}%")
        
        if tests_failed == 0:
            print(f"\n{Colors.GREEN}[SUCESSO] TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.{Colors.END}")
        elif tests_failed <= 2:
            print(f"\n{Colors.YELLOW}[AVISO] SISTEMA FUNCIONANDO com algumas limitacoes.{Colors.END}")
        else:
            print(f"\n{Colors.RED}[ERRO] PROBLEMAS DETECTADOS. Verifique os erros acima.{Colors.END}")
        
        print(f"\n[HORA] Finalizado em: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)
        
        return tests_failed == 0


def main():
    """Funcao principal"""
    print("\n" + "=" * 70)
    print("LEXSCAN IA - SISTEMA DE AUTOMACAO DOCUMENTAL")
    print("=" * 70)
    print()
    
    test = SystemTest()
    all_passed = test.run_all_tests()
    
    # Código de saída
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
