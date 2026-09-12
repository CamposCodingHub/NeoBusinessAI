# Deploy local com Docker

Stack mínima para escalar localmente: **Postgres 15**, **Redis 7**, **API** (FastAPI) e, opcionalmente, **web** (Next.js).

## Pré-requisitos

- Docker Desktop / Docker Engine + Compose v2
- Portas livres: `5432`, `6379`, `8000` (e `3000` se subir o frontend)

## Subir infra + API

Na raiz do repositório:

```bash
docker compose up --build
```

Sobe `postgres`, `redis` e `api`. Healthchecks garantem que a API só sobe após Postgres/Redis saudáveis.

API: http://localhost:8000/docs

## Frontend (opcional)

O serviço `web` usa o profile `web` (não sobe por padrão):

```bash
docker compose --profile web up --build
```

Web: http://localhost:3000

Sem Docker no frontend, continue com `npm run dev` em `frontend/` apontando para a API em `:8000`.

## Variáveis de ambiente

Compose já define defaults seguros para desenvolvimento. Sobrescreva via shell ou um `.env` na raiz:

| Variável | Default | Notas |
|----------|---------|--------|
| `POSTGRES_USER` | `neobusiness` | |
| `POSTGRES_PASSWORD` | `neobusiness_local_dev` | Troque fora de lab |
| `POSTGRES_DB` | `neobusiness_ai` | |
| `DATABASE_URL` | `postgresql://neobusiness:...@postgres:5432/...` | Host interno = `postgres` |
| `REDIS_URL` | `redis://redis:6379/0` | Host interno = `redis` |
| `SECRET_KEY` | local docker secret (≥32 chars) | Obrigatório forte em staging/prod |
| `CORS_ORIGINS` | `http://localhost:3000,...` | |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Browser → API no host |
| `LOCAL_AI_BASE_URL` | `http://host.docker.internal:11434/v1` | Ollama no host (Windows/Mac) |

Credenciais de IA/Firebase/Stripe: passe as mesmas vars do `backend/.env.example` no ambiente do Compose se precisar.

## Migrações (Alembic)

```bash
# Dentro do container
docker compose exec api alembic upgrade head

# Ou no host (venv + DATABASE_URL apontando para localhost:5432)
cd backend
alembic upgrade head
python scripts/init_alembic.py   # imprime o guia rápido
```

Baseline: `001_initial_stub` é no-op. Gere a primeira sync real com `alembic revision --autogenerate` e revise o SQL.

## Volumes

- `postgres_data` — dados Postgres persistentes
- `redis_data` — AOF Redis

Reset local: `docker compose down -v` (apaga volumes).

## Notas de produção local

- A imagem da API **não** instala `torch`/`transformers` do `requirements.txt` (imagem enxuta). Estenda o `backend/Dockerfile` se precisar desses pacotes no container.
- Frontend usa `output: 'standalone'` no Next.js para o multi-stage build.
- Para IA soberana local, rode Ollama no host; a API no Docker alcança via `host.docker.internal`.
- Não commite `.env` com segredos reais.
