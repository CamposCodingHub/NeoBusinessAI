# 📖 LexScan IA - Guia do Desenvolvedor

**Documentação técnica completa para desenvolvedores**

---

## 🏗️ Arquitetura do Sistema

```
LexScan IA
├── 📁 backend/                    # API e Processamento
│   ├── 📁 ai/                     # Inteligência Artificial
│   │   ├── lexscan_engine.py      # Motor principal de processamento
│   │   ├── engine.py              # Motor alternativo (NeoBusinessAI)
│   │   ├── groq_client.py         # Cliente Groq API
│   │   ├── prompts.py             # Prompts jurídicos
│   │   ├── brain.py               # Classificador de documentos
│   │   ├── memory.py              # Gerenciamento de sessões
│   │   └── vector_store.py        # Armazenamento de vetores
│   │
│   ├── 📁 tools/                  # Ferramentas e Utilitários
│   │   ├── ocr_real.py            # OCR com Tesseract
│   │   ├── ocr_processor.py       # Processamento OCR
│   │   ├── notifications.py       # Sistema de notificações email
│   │   ├── pdf_generator.py       # Geração de relatórios PDF
│   │   ├── stripe_manager.py      # Integração com Stripe
│   │   └── web_search.py          # Busca web (opcional)
│   │
│   ├── main.py                    # FastAPI - Endpoints principais
│   └── requirements.txt           # Dependências Python
│
├── 📁 frontend/                   # Interface do Usuário
│   ├── 📁 src/
│   │   ├── 📁 app/                # Páginas Next.js
│   │   │   ├── page.tsx           # Landing page
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx       # Dashboard principal
│   │   │   ├── chat/
│   │   │   │   └── page.tsx       # Chat com IA
│   │   │   ├── pricing/
│   │   │   │   └── page.tsx       # Planos e preços
│   │   │   ├── login/
│   │   │   │   └── page.tsx       # Autenticação
│   │   │   └── globals.css        # Estilos globais
│   │   │
│   │   ├── 📁 components/         # Componentes React
│   │   │   ├── Sidebar.tsx        # Navegação lateral
│   │   │   ├── DeadlineCalendar.tsx # Calendário de prazos
│   │   │   └── ProtectedRoute.tsx # Proteção de rotas
│   │   │
│   │   ├── 📁 contexts/           # Contextos React
│   │   │   └── AuthContext.tsx    # Contexto de autenticação
│   │   │
│   │   └── 📁 lib/                # Utilitários
│   │       └── firebase.ts        # Configuração Firebase
│   │
│   ├── package.json               # Dependências Node.js
│   └── next.config.js             # Configuração Next.js
│
├── 📄 README.md                   # Documentação geral
├── 📄 README_DEVELOPER.md         # Este arquivo
└── 📄 .env.example                # Variáveis de ambiente
```

---

## 🚀 Configuração do Ambiente de Desenvolvimento

### 1. Pré-requisitos

- **Python** 3.10+
- **Node.js** 18+
- **Tesseract OCR** v5.5.0
- **Git**

### 2. Instalação Completa

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/lexscan-ia.git
cd lexscan-ia

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves

# 3. Instale o backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 4. Instale o Tesseract OCR
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# 5. Instale o frontend
cd ../frontend
npm install

# 6. Inicie os servidores
# Terminal 1 - Backend
cd ../backend
python main.py

# Terminal 2 - Frontend
cd ../frontend
npm run dev
```

---

## 📋 Variáveis de Ambiente

### Backend (.env)

```env
# Groq API (Obrigatório)
GROQ_API_KEY=gsk_sua_chave_aqui

# Firebase (Obrigatório)
FIREBASE_PROJECT_ID=seu-projeto
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@...

# SMTP (Opcional - para notificações)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app

# Stripe (Opcional - para pagamentos)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Configurações
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=50MB
```

### Frontend (.env.local)

```env
# Firebase (Obrigatório)
NEXT_PUBLIC_FIREBASE_API_KEY=sua_chave
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=seu-projeto.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=seu-projeto
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=seu-projeto.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔧 Guia de Desenvolvimento

### Estrutura de Commits

```
tipo(escopo): descrição

[opcional] corpo da mensagem

[opcional] footer
```

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (sem mudança de código)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção

**Exemplo:**
```
feat(ocr): adicionar suporte a múltiplos idiomas

Implementa detecção automática de idioma no OCR
e seleciona o melhor modelo Tesseract.

Closes #123
```

### Padrões de Código

#### Python (Backend)

```python
"""
Docstring com descrição do módulo/função.
"""

from typing import Dict, List, Optional
from datetime import datetime

# Constantes em UPPER_CASE
MAX_DOCUMENTS = 50
DEFAULT_TIMEOUT = 30

# Classes em PascalCase
class DocumentProcessor:
    """
    Processa documentos jurídicos.
    
    Attributes:
        engine: Motor de IA
        max_size: Tamanho máximo de arquivo
    """
    
    def __init__(self, engine: AIEngine, max_size: int = 50):
        """Inicializa o processador."""
        self.engine = engine
        self.max_size = max_size
    
    def process(self, document: bytes) -> Dict:
        """
        Processa um documento.
        
        Args:
            document: Bytes do arquivo
            
        Returns:
            Dicionário com resultado do processamento
            
        Raises:
            ValueError: Se documento for inválido
        """
        if not document:
            raise ValueError("Documento vazio")
        
        # Processamento...
        return {"success": True, "data": {}}

# Funções em snake_case
def extract_deadlines(text: str) -> List[Dict]:
    """Extrai prazos de um texto."""
    pass
```

#### TypeScript (Frontend)

```typescript
// Interfaces em PascalCase
interface Document {
  id: number;
  filename: string;
  type: DocumentType;
  createdAt: Date;
}

// Enums em PascalCase
enum DocumentType {
  PETICAO_INICIAL = 'peticao_inicial',
  CONTESTACAO = 'contestacao',
  RECURSO = 'recurso',
}

// Componentes em PascalCase
export function DocumentCard({ document }: { document: Document }) {
  // Hooks no topo
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  // Handlers
  const handleClick = useCallback(() => {
    router.push(`/documents/${document.id}`);
  }, [document.id, router]);
  
  // Render
  return (
    <div className="document-card" onClick={handleClick}>
      <h3>{document.filename}</h3>
      <span>{document.type}</span>
    </div>
  );
}

// Funções auxiliares em camelCase
const formatDate = (date: Date): string => {
  return date.toLocaleDateString('pt-BR');
};
```

---

## 🧪 Testes

### Backend

```bash
# Executar todos os testes
cd backend
python -m pytest

# Testes específicos
python -m pytest tests/test_ocr.py -v
python -m pytest tests/test_engine.py -v

# Cobertura
python -m pytest --cov=ai --cov=tools --cov-report=html
```

### Frontend

```bash
# Executar testes
cd frontend
npm test

# Modo watch
npm test -- --watch

# Cobertura
npm test -- --coverage
```

### Testes de Integração

```bash
# Script completo
cd lexscan-ia
python test_completo_final.py
```

---

## 📚 API Endpoints

### Documentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/documents/upload` | Upload e processamento |
| GET | `/api/documents` | Listar documentos |
| GET | `/api/documents/{id}` | Obter documento |
| GET | `/api/documents/{id}/report` | Exportar PDF |
| POST | `/api/documents/{id}/chat` | Chat contextual |
| DELETE | `/api/documents/{id}` | Remover documento |

### Dashboard

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/dashboard` | Estatísticas |
| GET | `/api/deadlines` | Lista de prazos |
| GET | `/api/calendar` | Calendário de prazos |
| GET | `/api/reports/dashboard` | Relatório PDF |

### Pagamentos (Stripe)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/plans` | Listar planos |
| POST | `/api/checkout/create` | Criar checkout |
| GET | `/api/subscription/status` | Status assinatura |
| POST | `/api/subscription/cancel` | Cancelar |
| POST | `/api/webhook/stripe` | Webhook Stripe |

### Notificações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/notifications/test` | Testar SMTP |
| POST | `/api/notifications/send` | Enviar email |
| POST | `/api/notifications/check-deadlines` | Verificar prazos |

---

## 🐛 Debugging

### Backend

```python
# Adicionar logs
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message", exc_info=True)
```

### Frontend

```typescript
// React DevTools
// Extensão do Chrome para debug de componentes

// Console logs estratégicos
console.log('[Component] State:', state);
console.log('[API] Response:', data);
console.error('[Error] Details:', error);
```

---

## 🚀 Deploy

### Preparação

```bash
# 1. Testar localmente
python test_completo_final.py

# 2. Verificar variáveis de ambiente
cat .env | grep -v "^#" | grep -v "^$"

# 3. Build do frontend
cd frontend
npm run build

# 4. Testar build
npm start
```

### Deploy Backend (Railway/Render)

```bash
# Railway
railway login
railway init
railway up

# Render
# Conectar repositório Git
# Configurar variáveis de ambiente
# Deploy automático
```

### Deploy Frontend (Vercel)

```bash
# Vercel CLI
npm i -g vercel
vercel login
vercel

# Configurações
# - Framework: Next.js
# - Build: npm run build
# - Output: .next
```

### Docker (Opcional)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

```bash
# Build
docker build -t lexscan-backend .

# Run
docker run -p 8000:8000 --env-file .env lexscan-backend
```

---

## 📊 Monitoramento

### Logs

```bash
# Backend
tail -f backend/logs/app.log

# Frontend (navegador)
# Console do desenvolvedor
```

### Métricas

```python
# Adicionar métricas
from prometheus_client import Counter, Histogram

upload_counter = Counter('document_uploads_total', 'Total de uploads')
processing_time = Histogram('document_processing_seconds', 'Tempo de processamento')

@upload_counter.count_exceptions()
@processing_time.time()
def process_document():
    pass
```

---

## 🔐 Segurança

### Checklist

- [ ] Variáveis sensíveis em `.env`
- [ ] `.env` no `.gitignore`
- [ ] HTTPS em produção
- [ ] Headers de segurança (CSP, HSTS)
- [ ] Rate limiting
- [ ] Validação de inputs
- [ ] Sanitização de outputs
- [ ] Logs sem dados sensíveis

### Headers Recomendados

```python
# FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["lexscan.ai", "*.lexscan.ai"]
)
```

---

## 🤝 Contribuindo

### Fluxo de Trabalho

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Faça as alterações
4. Commit: `git commit -m "feat: descrição"`
5. Push: `git push origin feature/nova-funcionalidade`
6. Abra um Pull Request

### Code Review

- Testes passando
- Documentação atualizada
- Sem conflitos
- Aprovação de 2 revisores

---

## 📞 Suporte para Desenvolvedores

- 📧 **Email:** dev@lexscan.com.br
- 💬 **Discord:** [discord.gg/lexscan](https://discord.gg/lexscan)
- 📚 **Wiki:** [wiki.lexscan.com.br](https://wiki.lexscan.com.br)

---

## 📝 Changelog

### v1.0.0 (2024-05-02)
- ✅ MVP completo
- ✅ OCR com Tesseract
- ✅ IA com Groq
- ✅ Calendário de prazos
- ✅ Sistema de pagamentos Stripe
- ✅ Exportação PDF

---

**Desenvolvido com ❤️ pela equipe LexScan IA**
