# Overnight 2026-09-11 — Local scalability scaffolding (Docker + Alembic)

Data: 11 de setembro de 2026

## Objetivo

Deixar o monorepo com uma base **production-minded** para rodar localmente com Postgres + Redis + API (e web opcional), sem depender de venv commitado, e com Alembic pronto para evoluir o schema além de `create_all`.

## O que foi entregue

### 1. `docker-compose.yml` (raiz)

- **postgres:15** — volume `postgres_data`, healthcheck `pg_isready`, env configurável
- **redis:7-alpine** — AOF + volume `redis_data`, healthcheck `PING`
- **api** — build `backend/Dockerfile`, depende de Postgres/Redis healthy, env `DATABASE_URL` / `REDIS_URL` / `SECRET_KEY` / CORS / AI passthrough
- **web** (profile `web`) — build `frontend/Dockerfile`, opcional; não sobe no `compose up` padrão

### 2. `backend/Dockerfile`

- Base `python:3.11-slim`
- Instala deps **enxutas** via pip (FastAPI, uvicorn, SQLAlchemy, psycopg2-binary, redis, pydantic-settings, alembic, etc.)
- **Não** usa o `requirements.txt` completo (contém torch/transformers — inviável para imagem de API)
- Copia só código da app (venv excluído por `.dockerignore`)
- `EXPOSE 8000` + `CMD uvicorn main:app --host 0.0.0.0 --port 8000`

### 3. `frontend/Dockerfile`

- Multi-stage Next.js 14 (`deps` → `builder` → `runner`)
- Requer `output: 'standalone'` em `next.config.js` (adicionado)
- `EXPOSE 3000` / `node server.js`

### 4. `.dockerignore`

- `backend/.dockerignore` — venv, caches, testes, `.env`
- `frontend/.dockerignore` — `node_modules`, `.next`, e2e

### 5. Alembic

- `backend/alembic.ini`
- `backend/alembic/env.py` — importa `Base` de `database.py` e URL de `config.settings`
- `backend/alembic/versions/001_initial_stub.py` — baseline no-op
- `backend/scripts/init_alembic.py` — documentação/guia impresso

### 6. Docs

- `DEPLOY_LOCAL_DOCKER.md` — guia curto de uso
- este relatório

## Como validar

```bash
docker compose up --build
# API: http://localhost:8000/docs

docker compose --profile web up --build
# Web: http://localhost:3000

docker compose exec api alembic upgrade head
```

## Riscos / próximos passos

1. **Autogenerate Alembic** — `database.py` tem muitos modelos; a primeira revision real pode ser grande. Revisar SQL antes de `upgrade`.
2. **Deps da API** — pacotes de LLM cloud/local (groq, openai, ollama HTTP ok via httpx; torch não). Adicionar ao Dockerfile conforme necessidade.
3. **Segredos** — defaults do Compose são só para lab; staging/prod devem injetar `SECRET_KEY` forte e senhas fortes.
4. **Healthcheck da API** — usa `/docs`; se docs forem desabilitados em produção, trocar por `/health` quando existir.
5. **Não commitado** — scaffolding criado sob demanda overnight; revisão humana antes de merge.

## Arquivos tocados

- `docker-compose.yml` (novo)
- `backend/Dockerfile` (novo)
- `backend/.dockerignore` (novo)
- `frontend/Dockerfile` (novo)
- `frontend/.dockerignore` (novo)
- `frontend/next.config.js` (`output: 'standalone'`)
- `backend/alembic.ini` (novo)
- `backend/alembic/env.py` (novo)
- `backend/alembic/script.py.mako` (novo)
- `backend/alembic/versions/001_initial_stub.py` (novo)
- `backend/scripts/init_alembic.py` (novo)
- `DEPLOY_LOCAL_DOCKER.md` (novo)
- `relatorios_melhorias/OVERNIGHT_20260911_SCALE.md` (novo)
