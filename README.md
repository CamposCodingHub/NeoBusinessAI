# ⚖️ LexScan IA

**Automação Documental Jurídica com OCR + Inteligência Artificial**

Transforme documentos jurídicos em insights acionáveis. Extraia textos automaticamente, detecte prazos processuais e receba alertas em tempo real.

---

## 🚀 O Que Fazemos

- **📄 OCR Inteligente**: Extração automática de texto de PDFs, imagens e documentos escaneados
- **⏰ Detecção de Prazos**: Identificação automática de datas críticas e prazos processuais  
- **🤖 IA Jurídica**: Resumos automáticos, análise de documentos e chat contextual
- **🔔 Alertas Automáticos**: Notificações por email, WhatsApp e SMS
- **💰 Análise de Valores**: Extração de valores da causa e riscos

---

## 💻 Tecnologias

### Backend
- **FastAPI** - API rápida e escalável
- **Tesseract OCR** - Reconhecimento óptico de caracteres
- **Groq API** - Llama 3.1 para análise de documentos
- **Python** - Processamento de dados

### Frontend  
- **Next.js 14** - React framework
- **Firebase** - Autenticação
- **TypeScript** - Tipagem segura

---

## 📊 Planos SaaS

| Plano | Preço | Documentos | Recursos |
|-------|-------|------------|----------|
| **Starter** | R$ 297/mês | 50/mês | OCR básico, 1 usuário |
| **Professional** ⭐ | R$ 897/mês | 200/mês | OCR + IA, detecção de prazos, 5 usuários |
| **Business** | R$ 2.500/mês | Ilimitado | IA treinável, white-label, 20 usuários |

---

## 🛠️ Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-user/lexscan-ia.git
cd lexscan-ia

# Instale dependências backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Instale Tesseract OCR
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# Instale dependências frontend
cd ../frontend
npm install

# Configure variáveis de ambiente
# Crie .env na raiz com GROQ_API_KEY=sua_chave

# Inicie o backend
cd ../backend
python main.py

# Inicie o frontend (novo terminal)
cd ../frontend
npm run dev
```

---

## 📖 Como Usar

### 1. Upload de Documentos
```python
from lexscan_engine import lexscan_engine

# Processar documento
result = lexscan_engine.process_document(texto_extraido)

print(result['document_type'])  # Tipo detectado
print(result['analysis'])       # Análise completa
print(result['deadlines'])      # Prazos encontrados
```

### 2. Chat com Documento
```python
# Perguntar sobre o documento
resposta = lexscan_engine.chat_with_document(
    document_data=result,
    user_question="Qual o prazo para contestação?"
)
```

### 3. Calendário de Prazos
```python
# Gerar calendário de múltiplos documentos
deadlines = lexscan_engine.get_deadlines_calendar(lista_documentos)
```

---

## 🎯 Roadmap

- [x] Landing page profissional
- [x] Sistema OCR com Tesseract
- [x] Engine de análise jurídica
- [ ] Dashboard de documentos (em desenvolvimento)
- [ ] Sistema de upload de arquivos
- [ ] Calendário de prazos interativo
- [ ] Notificações por email/WhatsApp
- [ ] API pública
- [ ] Integrações (PJe, e-SAJ, ERPs)

---

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia nosso [CONTRIBUTING.md](CONTRIBUTING.md) primeiro.

---

## 📄 Licença

Este projeto está licenciado sob [MIT License](LICENSE).

---

## 💬 Suporte

- 📧 Email: suporte@lexscan.com.br
- 💬 WhatsApp: (11) 99999-9999
- 🌐 Website: [www.lexscan.com.br](https://www.lexscan.com.br)

---

⚖️ **LexScan IA** - Revolucionando a advocacia com tecnologia

*Desenvolvido com ❤️ para advogados e escritórios jurídicos*

1. Ativar venv
2. Instalar dependências:
   pip install -r requirements.txt
   python src/main.py