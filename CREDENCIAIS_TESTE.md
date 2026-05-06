# 🔐 Credenciais de Acesso - Ambiente de Teste

## 🚨 IMPORTANTE: Ambiente de Teste Somente!

**Estas credenciais são APENAS para testes locais. NUNCA use em produção!**

---

## 👤 Contas de Teste Disponíveis

### 🎭 ADMINISTRADOR (Acesso Total)
```
Email:    admin@neobusiness.ai
Senha:    Admin@123456!
Role:     admin
Nível:    Enterprise
```

**Permissões:**
- ✅ Acesso a todos os recursos
- ✅ Gerenciar usuários
- ✅ Ver métricas do sistema
- ✅ Configurações avançadas

---

### 👤 USUÁRIO COMUM (Free)
```
Email:    user@neobusiness.ai
Senha:    User@123456!
Role:     user
Nível:    Free
```

**Permissões:**
- ✅ Upload de documentos (limite: 5)
- ✅ Chat básico
- ✅ Dashboard pessoal
- ❌ Recursos premium
- ❌ Administração

---

### 💎 USUÁRIO PREMIUM
```
Email:    premium@neobusiness.ai
Senha:    Premium@123456!
Role:     premium
Nível:    Premium
```

**Permissões:**
- ✅ Tudo do plano Free +
- ✅ Mais uploads (limite: 50)
- ✅ Análises avançadas
- ✅ Exportação de relatórios
- ✅ Suporte prioritário

---

### 🏢 USUÁRIO ENTERPRISE
```
Email:    enterprise@neobusiness.ai
Senha:    Enterprise@123456!
Role:     enterprise
Nível:    Enterprise
```

**Permissões:**
- ✅ Tudo do plano Premium +
- ✅ Uploads ilimitados
- ✅ Múltiplos usuários
- ✅ API access
- ✅ Customizações
- ❌ Administração de sistema

---

## 🚀 Como Fazer Login

### 1. Backend API (Teste com curl/Postman)

```bash
# Login como Admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@neobusiness.ai",
    "password": "Admin@123456!"
  }'

# Resposta esperada:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer",
#   "user": {
#     "id": 1,
#     "email": "admin@neobusiness.ai",
#     "role": "admin",
#     "plan_tier": "enterprise"
#   }
# }
```

### 2. Usar Token em Requisições Protegidas

```bash
# Acessar endpoint protegido
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer {SEU_ACCESS_TOKEN}"
```

---

## 📝 Endpoints Disponíveis

### Autenticação
| Método | Endpoint | Descrição | Público |
|--------|----------|-----------|---------|
| POST | `/auth/register` | Criar conta | ✅ Sim |
| POST | `/auth/login` | Fazer login | ✅ Sim |
| POST | `/auth/refresh` | Renovar token | ✅ Sim (com refresh token) |
| GET | `/auth/me` | Perfil do usuário | 🔒 Não |
| POST | `/auth/logout` | Logout | 🔒 Não |

### Admin (Requer role: admin)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/auth/admin/users` | Listar todos usuários |
| POST | `/auth/admin/create-admin` | Criar novo admin |
| PATCH | `/auth/admin/users/{id}/role` | Alterar role |

---

## 🛠️ Como Criar os Usuários

Execute o script de seed:

```bash
# Navegue até o backend
cd backend

# Execute o script
python scripts/create_admin.py
```

Saída esperada:
```
============================================================
🔐 NEOBUSINESS AI - CRIAÇÃO DE USUÁRIOS DE TESTE
============================================================

✓ Tabelas verificadas/criadas

============================================================
✅ USUÁRIO ADMINISTRADOR CRIADO COM SUCESSO
============================================================

📧 Email: admin@neobusiness.ai
🔑 Senha: Admin@123456!
👤 Nome: Administrador NeoBusiness
🎭 Role: admin
📊 ID: 1

============================================================
⚠️  IMPORTANTE: Altere a senha após o primeiro login!
============================================================


============================================================
✅ USUÁRIOS DE TESTE CRIADOS
============================================================

🎉 SETUP COMPLETO!

Você pode agora fazer login com:
  • Admin: admin@neobusiness.ai / Admin@123456!
  • User: user@neobusiness.ai / User@123456!
  • Premium: premium@neobusiness.ai / Premium@123456!
  • Enterprise: enterprise@neobusiness.ai / Enterprise@123456!

============================================================
```

---

## 🔒 Segurança

### ⚠️ Atenção
- Estas credenciais são **APENAS para desenvolvimento**
- Senhas seguem padrão forte por padrão
- Tokens expiram em 30 minutos (access) e 7 dias (refresh)
- Rate limiting está ativo (5 tentativas/minuto para login)

### 🔄 Renovação de Token

Quando o access token expirar (401):

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Authorization: Bearer {SEU_REFRESH_TOKEN}"
```

---

## 🐛 Troubleshooting

### Erro: "Email ou senha incorretos"
- Verifique se executou o script `create_admin.py`
- Verifique se o banco de dados está rodando
- Tente recriar: `python scripts/create_admin.py`

### Erro: "Usuário não encontrado"
- O banco pode estar vazio
- Execute o script de seed novamente

### Erro: "Rate limit excedido"
- Aguarde 1 minuto
- Ou reinicie o servidor backend

---

## 📚 Próximos Passos

1. ✅ Execute o script para criar usuários
2. ✅ Teste login com `admin@neobusiness.ai`
3. ✅ Use o token para acessar endpoints protegidos
4. ✅ Teste diferentes roles (user, premium, enterprise, admin)

---

**Última atualização:** 03/05/2026  
**Ambiente:** Desenvolvimento Local  
**Status:** ✅ Pronto para testes
