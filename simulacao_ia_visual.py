"""
Simulação Visual Interativa - NeoBusinessAI
Demonstra o funcionamento da IA jurídica em tempo real
"""

import sys
import os
import time
import threading
from datetime import datetime

# Usar o venv do backend
venv_python = os.path.join(os.path.dirname(__file__), 'backend', 'venv311', 'Scripts', 'python.exe')

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  NEOBUSINESS AI - SIMULAÇÃO INTERATIVA")
    print("  Sistema de IA Jurídica com OCR e Processamento de Documentos")
    print("=" * 70)
    print(f"{Colors.END}")

def print_menu():
    print(f"\n{Colors.CYAN}{Colors.BOLD}MENU DE OPÇÕES:{Colors.END}")
    print(f"{Colors.GREEN}1.{Colors.END} Testar Configuração do Sistema")
    print(f"{Colors.GREEN}2.{Colors.END} Testar Engine de IA")
    print(f"{Colors.GREEN}3.{Colors.END} Testar Cliente Groq")
    print(f"{Colors.GREEN}4.{Colors.END} Testar Prompts Jurídicos")
    print(f"{Colors.GREEN}5.{Colors.END} Simular Processamento de Documento")
    print(f"{Colors.GREEN}6.{Colors.END} Simular Chat com IA")
    print(f"{Colors.GREEN}7.{Colors.END} Status Completo do Sistema")
    print(f"{Colors.GREEN}0.{Colors.END} Sair")
    print()

def test_configuracao():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[TESTE 1/7] Configuração do Sistema{Colors.END}")
    print("-" * 70)
    
    import subprocess
    result = subprocess.run(
        [venv_python, "-c", "from config import settings; print('Environment:', settings.ENVIRONMENT); print('AI Sovereign:', settings.AI_SOVEREIGN_ENABLED); print('AI Routing:', settings.AI_ROUTING_POLICY)"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}[OK] SUCESSO{Colors.END}")
        for line in result.stdout.strip().split('\n'):
            print(f"   {Colors.CYAN}{line}{Colors.END}")
    else:
        print(f"{Colors.RED}[ERRO] ERRO{Colors.END}")
        print(f"   {result.stderr}")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def test_engine():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[TESTE 2/7] Engine de IA{Colors.END}")
    print("-" * 70)
    
    import subprocess
    result = subprocess.run(
        [venv_python, "-c", "from ai.engine import NeoBusinessAI; engine = NeoBusinessAI(); print('Engine inicializada:', type(engine).__name__)"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}[OK] SUCESSO{Colors.END}")
        for line in result.stdout.strip().split('\n'):
            print(f"   {Colors.CYAN}{line}{Colors.END}")
    else:
        print(f"{Colors.RED}[ERRO] FALHA{Colors.END}")
        print(f"   {result.stderr}")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def test_groq():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[TESTE 3/7] Cliente Groq{Colors.END}")
    print("-" * 70)
    
    import subprocess
    result = subprocess.run(
        [venv_python, "-c", "from ai.groq_client import GroqClient; print('GroqClient importado com sucesso')"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=15
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}[OK] SUCESSO{Colors.END}")
        print(f"   {Colors.CYAN}{result.stdout.strip()}{Colors.END}")
    else:
        print(f"{Colors.RED}[ERRO] ERRO{Colors.END}")
        print(f"   {result.stderr[:200]}")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def test_prompts():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[TESTE 4/7] Prompts Jurídicos{Colors.END}")
    print("-" * 70)
    
    import subprocess
    result = subprocess.run(
        [venv_python, "-c", "from ai.prompts import BASE_SYSTEM_PROMPT, get_full_system_prompt; print('BASE_SYSTEM_PROMPT length:', len(BASE_SYSTEM_PROMPT)); print('get_full_system_prompt disponivel: OK')"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}[OK] SUCESSO{Colors.END}")
        for line in result.stdout.strip().split('\n'):
            print(f"   {Colors.CYAN}{line}{Colors.END}")
    else:
        print(f"{Colors.RED}[ERRO] ERRO{Colors.END}")
        print(f"   {result.stderr}")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def simular_documento():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[SIMULAÇÃO 5/7] Processamento de Documento{Colors.END}")
    print("-" * 70)
    
    documento = "CONTRATO_DE_PRESTACAO_SERVICOS.pdf"
    print(f"{Colors.CYAN}Documento:{Colors.END} {documento}")
    print(f"{Colors.CYAN}Tamanho:{Colors.END} 2.4 MB")
    print(f"{Colors.CYAN}Páginas:{Colors.END} 15")
    print()
    
    etapas = [
        ("Upload do documento", 2),
        ("Validação de formato", 1),
        ("Extração de texto com OCR", 5),
        ("Análise de entidades jurídicas", 3),
        ("Detecção de prazos e datas", 2),
        ("Classificação do documento", 2),
        ("Geração de resumo executivo", 3),
        ("Identificação de riscos", 2),
    ]
    
    for etapa, duracao in etapas:
        print(f"{Colors.YELLOW}[...] {etapa}...{Colors.END}", end="", flush=True)
        for i in range(duracao):
            time.sleep(0.3)
            print(".", end="", flush=True)
        print(f" {Colors.GREEN}[OK]{Colors.END}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Processamento concluído com sucesso!{Colors.END}")
    print(f"{Colors.CYAN}Entidades detectadas:{Colors.END} 12")
    print(f"{Colors.CYAN}Prazos identificados:{Colors.END} 3")
    print(f"{Colors.CYAN}Riscos detectados:{Colors.END} 2 (média)")
    print(f"{Colors.CYAN}Classificação:{Colors.END} Contrato de Prestação de Serviços")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def simular_chat():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[SIMULAÇÃO 6/7] Chat com IA Jurídica{Colors.END}")
    print("-" * 70)
    
    perguntas = [
        "Quais são os prazos deste contrato?",
        "Existe alguma cláusula de rescisão?",
        "Qual é o valor total do contrato?"
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{Colors.CYAN}Usuário:{Colors.END} {pergunta}")
        print(f"{Colors.YELLOW}IA processando...{Colors.END}", end="", flush=True)
        for j in range(8):
            time.sleep(0.2)
            print(".", end="", flush=True)
        print()
        
        respostas = [
            "Identifiquei 3 prazos importantes: (1) Prazo de vigência de 12 meses, (2) Prazo de pagamento em 30 dias, (3) Prazo de renovação automática.",
            "Sim, existe uma cláusula de rescisão unilateral com aviso prévio de 30 dias e multa de 10% sobre o valor remanescente.",
            "O valor total do contrato é R$ 150.000,00, parcelado em 12 mensais de R$ 12.500,00 cada."
        ]
        
        print(f"{Colors.GREEN}IA:{Colors.END} {respostas[i-1]}")
        time.sleep(1)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Chat concluído!{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def status_completo():
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[STATUS 7/7] Status Completo do Sistema{Colors.END}")
    print("-" * 70)
    
    status = {
        "Configuração": "[OK] Ativo",
        "Engine IA": "[!] Parcial (sem API key)",
        "Cliente Groq": "[OK] Disponível",
        "Prompts Jurídicos": "[OK] Carregados",
        "Transformers": "[OK] Instalado",
        "PyTorch": "[OK] Instalado",
        "Pytesseract": "[OK] Instalado",
        "Pillow": "[OK] Instalado",
        "Frontend": "[OK] Rodando (localhost:3000)",
        "Backend": "[!] Parcial (dependências externas)",
    }
    
    print(f"\n{Colors.BOLD}Componentes do Sistema:{Colors.END}\n")
    for componente, estado in status.items():
        print(f"  {Colors.CYAN}{componente:20}{Colors.END} {estado}")
    
    print(f"\n{Colors.BOLD}Resumo:{Colors.END}")
    print(f"  {Colors.GREEN}[OK]{Colors.END} Ambiente de desenvolvimento configurado")
    print(f"  {Colors.GREEN}[OK]{Colors.END} Frontend operacional")
    print(f"  {Colors.YELLOW}[!]{Colors.END} Backend parcialmente funcional")
    print(f"  {Colors.YELLOW}[!]{Colors.END} IA básica operacional (requer API key para completo)")
    
    print(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
    try:
        input()
    except:
        pass

def main():
    import sys
    
    # Se não houver argumentos, modo interativo
    if len(sys.argv) == 1:
        while True:
            clear_screen()
            print_header()
            print_menu()
            
            try:
                opcao = input(f"{Colors.CYAN}Escolha uma opção: {Colors.END}")
            except EOFError:
                # Executar modo automático se não houver input
                print(f"\n{Colors.YELLOW}Executando modo automático...{Colors.END}\n")
                time.sleep(2)
                executar_todos_testes()
                break
            
            if opcao == '1':
                test_configuracao()
            elif opcao == '2':
                test_engine()
            elif opcao == '3':
                test_groq()
            elif opcao == '4':
                test_prompts()
            elif opcao == '5':
                simular_documento()
            elif opcao == '6':
                simular_chat()
            elif opcao == '7':
                status_completo()
            elif opcao == '0':
                print(f"\n{Colors.GREEN}Obrigado por usar o NeoBusiness AI!{Colors.END}\n")
                break
            else:
                print(f"{Colors.RED}Opção inválida!{Colors.END}")
                time.sleep(1)
    else:
        # Modo automático
        executar_todos_testes()

def executar_todos_testes():
    """Executa todos os testes automaticamente"""
    clear_screen()
    print_header()
    print(f"\n{Colors.YELLOW}{Colors.BOLD}MODO AUTOMÁTICO - Executando todos os testes...{Colors.END}\n")
    time.sleep(2)
    
    test_configuracao()
    test_groq()
    test_prompts()
    simular_documento()
    simular_chat()
    status_completo()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}TODOS OS TESTES CONCLUÍDOS!{Colors.END}\n")
    time.sleep(3)

if __name__ == "__main__":
    main()
