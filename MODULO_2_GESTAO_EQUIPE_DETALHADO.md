# 👥 MÓDULO 2: GESTÃO DE EQUIPE E TAREFAS (TeamFlow)
## Especificação Técnica Completa

---

## 1. VISÃO GERAL

Sistema completo de gestão interna do escritório de advocacia, permitindo cadastro de colaboradores com diferentes perfis, atribuição de tarefas por processo, acompanhamento de produtividade e painel gerencial com indicadores de desempenho.

---

## 2. HIERARQUIA DE PERFIS

```
🔴 SÓCIO/ADMIN
├── Acesso total ao sistema
├── Cadastro/edição de todos usuários
├── Relatórios financeiros completos
├── Configurações do escritório
└── Auditoria de logs

🟠 SÓCIO (minoritário)
├── Acesso a processos e clientes
├── Cadastro de advogados/estagiários
├── Relatórios de sua equipe
└── Não pode excluir sócios

🟡 ADVOGADO SÊNIOR
├── Processos próprios e supervisionados
├── Cadastro de estagiários
├── Tarefas para si e equipe
└── Relatórios de produtividade

🟢 ADVOGADO
├── Processos atribuídos
├── Tarefas próprias
├── Cadastro limitado de clientes
└── Dashboard pessoal

🔵 ESTAGIÁRIO
├── Tarefas atribuídas (não cria)
├── Visualização read-only processos
├── Upload de documentos (para revisão)
└── Sem acesso financeiro

⚪ ASSISTENTE/SECRETÁRIA
├── Agendamento de compromissos
├── Confirmação de audiências
├── Atendimento telefônico
└── Sem acesso documentos sigilosos
```

---

## 3. MODELOS DE DADOS (SQLAlchemy)

```python
# database.py - Adicionar após NotificationQueue

class TeamMember(Base):
    """Membros da equipe do escritório"""
    __tablename__ = 'team_members'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Informações profissionais
    oab_number = Column(String(20), unique=True)
    oab_state = Column(String(2))  # SP, RJ, MG
    specialization = Column(String(255))
    
    # Perfil no escritório
    role = Column(String(50), nullable=False)
    # Roles: socio_admin, socio, advogado_senior, advogado, estagiario, assistente
    department = Column(String(100))  # Trabalhista, Previdenciário, etc
    
    # Hierarquia
    supervisor_id = Column(Integer, ForeignKey('team_members.id'))
    
    # Configurações de trabalho
    work_hours_per_day = Column(Integer, default=8)
    work_days_per_week = Column(Integer, default=5)
    
    # Limitações
    max_active_cases = Column(Integer, default=50)
    can_create_cases = Column(Boolean, default=True)
    can_access_financial = Column(Boolean, default=False)
    can_manage_team = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    hired_at = Column(DateTime, default=datetime.utcnow)
    fired_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Tarefas atribuídas"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Vínculos
    assignee_id = Column(Integer, ForeignKey('team_members.id'), nullable=False)
    assigner_id = Column(Integer, ForeignKey('team_members.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('deadlines.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    # Detalhes
    title = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # prazo, documento, reuniao, pesquisa
    
    # Prioridade
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    urgency_reason = Column(String(255))
    
    # Prazos
    due_date = Column(DateTime, nullable=False)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    
    # Status
    status = Column(String(50), default='pending')
    # pending, in_progress, blocked, completed, cancelled
    completion_percentage = Column(Integer, default=0)
    
    # Histórico
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    blocked_at = Column(DateTime)
    blocked_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskComment(Base):
    """Comentários em tarefas"""
    __tablename__ = 'task_comments'
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('team_members.id'), nullable=False)
    
    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default='general')
    # general, update, block, completion, escalation
    
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamPerformanceMetric(Base):
    """Métricas de performance"""
    __tablename__ = 'team_performance_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey('team_members.id'), nullable=False)
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    tasks_completed = Column(Integer, default=0)
    tasks_pending = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    
    total_hours_logged = Column(Float, default=0)
    cases_handled = Column(Integer, default=0)
    cases_without_movement_days = Column(Integer, default=0)
    client_response_time_avg_hours = Column(Float)
    
    overall_score = Column(Integer)  # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 4. ROTAS BACKEND (routes/team_routes.py)

### 4.1 Gestão de Membros
```python
@router.get("/members")
async def list_team_members(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Lista membros com filtros por permissão"""
    pass

@router.post("/members")
async def create_team_member(
    member_data: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cadastra novo membro (sócios)"""
    pass

@router.get("/members/{member_id}")
async def get_member_details(
    member_id: int,
    db: Session = Depends(get_db)
):
    """Detalhes + métricas do membro"""
    pass

@router.get("/members/{member_id}/subordinates")
async def get_subordinates(member_id: int):
    """Lista subordinados (para gestores)"""
    pass
```

### 4.2 Gestão de Tarefas
```python
@router.get("/tasks")
async def list_tasks(
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
):
    """Lista tarefas com filtros por permissão"""
    pass

@router.post("/tasks")
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks
):
    """Cria tarefa e notifica responsável"""
    pass

@router.get("/tasks/{task_id}")
async def get_task_details(task_id: int):
    """Detalhes + comentários"""
    pass

@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    update_data: TaskUpdate
):
    """Atualiza status/progresso"""
    pass

@router.post("/tasks/{task_id}/comments")
async def add_task_comment(task_id: int, content: str):
    """Adiciona comentário"""
    pass
```

### 4.3 Dashboard Gerencial
```python
@router.get("/dashboard/manager")
async def get_manager_dashboard(
    period_days: int = 30
):
    """
    Painel gerencial com:
    - Total de tarefas
    - Taxa de conclusão
    - Prazos críticos
    - Performance por membro
    - Alertas automáticos
    """
    pass
```

---

## 5. FRONTEND (app/dashboard/team/page.tsx)

### Componentes Principais:

```typescript
// Tabs do módulo
<Tabs>
  <Tab id="dashboard" label="📊 Painel Gerencial" />
  <Tab id="members" label="👥 Equipe" />
  <Tab id="tasks" label="✅ Tarefas" />
  <Tab id="onboarding" label="📚 Onboarding" />
</Tabs>

// Dashboard Tab:
- Cards: Total tarefas, Concluídas, Pendentes, Atrasadas
- Alertas: Membros com performance baixa
- Prazos Críticos: Próximos 3 dias
- Tabela: Produtividade por membro

// Members Tab:
- Grid de cards com membros
- Filtro por role/departamento
- Botão: Adicionar Membro
- Ações: Ver Perfil, Atribuir Tarefa

// Tasks Tab:
- Lista de tarefas com prioridade colorida
- Filtro: status, prioridade, responsável
- Progress bar por tarefa
- Botão: Nova Tarefa

// Onboarding Tab:
- Checklists por tipo de caso
- Base de conhecimento
- Artigos mais lidos
```

---

## 6. PERMISSÕES POR ROTA

```python
PERMISSIONS = {
    # Membros
    "GET /team/members": ["socio", "socio_admin", "advogado_senior"],
    "POST /team/members": ["socio", "socio_admin"],
    "GET /team/members/{id}": ["socio", "socio_admin", "advogado_senior", "self"],
    
    # Tarefas
    "GET /team/tasks": ["all"],  # Filtrado por permissão
    "POST /team/tasks": ["socio", "socio_admin", "advogado_senior"],
    "PATCH /team/tasks/{id}": ["assignee", "socio", "socio_admin"],
    
    # Dashboard
    "GET /team/dashboard/manager": ["socio", "socio_admin", "advogado_senior"],
}
```

---

## 7. MÉTRICAS E INDICADORES

### Calculadas Automaticamente:
1. **Taxa de Conclusão:** tasks_completed / total_tasks × 100
2. **Tempo Médio de Conclusão:** avg(completed_at - started_at)
3. **Tarefas Atrasadas:** count(due_date < now AND status != completed)
4. **Score de Performance:** algoritmo ponderado (0-100)
5. **Processos sem Movimentação:** casos sem atualização > X dias
6. **Tempo Médio de Resposta ao Cliente:** avg(first_response_time)

### Alertas Automáticos:
- Membro com >5 tarefas atrasadas
- Processo sem movimentação >30 dias
- Score de performance <30
- Prazo crítico próximo e responsável não agiu

---

## 8. ROADMAP IMPLEMENTAÇÃO

### Semana 1-2: Modelos e Backend
- Criar modelos SQLAlchemy
- Implementar rotas de membros
- Implementar rotas de tarefas
- Sistema de permissões

### Semana 3-4: Frontend
- Página de gestão de equipe
- Dashboard gerencial
- Lista de tarefas
- Formulários de criação

### Semana 5-6: Integrações
- Notificações WhatsApp/Email
- Dashboard principal (KPIs)
- Relatórios automáticos

### Semana 7-8: Onboarding e Polimento
- Checklists de onboarding
- Base de conhecimento
- Testes e documentação

---

## 9. CUSTOS

### Desenvolvimento:
- 2 devs backend: R$ 18.000 × 2 × 2 meses = R$ 72.000
- 2 devs frontend: R$ 15.000 × 2 × 2 meses = R$ 60.000
- **Total: R$ 132.000**

### Infra (mensal):
- Sem custo adicional (usa infra existente)

---

## 10. PRÓXIMOS PASSOS

1. Aprovar especificação
2. Criar branch `feature/team-management`
3. Implementar modelos de dados
4. Criar rotas backend
5. Desenvolver frontend
6. Integrar com sistema existente
7. Testes e deploy

---

**Status:** Pronto para implementação  
**Prioridade:** ALTA (core do produto)  
**Dependências:** Nenhuma (módulo independente)

