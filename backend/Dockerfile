# NeoBusiness AI API — lean production-minded image (Python 3.11)
# Avoids full requirements.txt (torch/transformers) for a practical API container.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Pragmatic runtime deps — full requirements.txt pulls torch/transformers (multi-GB).
# Extend this list as features are needed in the container.
RUN pip install --upgrade pip \
    && pip install \
        "fastapi>=0.110" \
        "uvicorn[standard]>=0.27" \
        "sqlalchemy>=2.0" \
        "psycopg2-binary>=2.9" \
        "redis>=5.0" \
        "pydantic>=2.0" \
        "pydantic-settings>=2.0" \
        "python-multipart>=0.0.9" \
        "python-dotenv>=1.0" \
        "email-validator>=2.0" \
        "pyjwt>=2.8" \
        "passlib[bcrypt]>=1.7" \
        "bcrypt>=4.0" \
        "httpx>=0.27" \
        "aiofiles>=23.0" \
        "tenacity>=8.0" \
        "alembic>=1.13" \
        "python-jose[cryptography]>=3.3" \
        "bleach>=6.0" \
        "pillow>=10.0" \
        "pypdf>=4.0" \
        "requests>=2.31"

# App code only (venv / caches excluded via .dockerignore)
COPY main.py config.py database.py database_multi_tenant.py database_optimizations.py \
     cache_manager.py celery_config.py metrics.py monitoring.py tasks.py start_server.py \
     alembic.ini ./
COPY alembic ./alembic
COPY api ./api
COPY core ./core
COPY middleware ./middleware
COPY models ./models
COPY routes ./routes
COPY runtime ./runtime
COPY security ./security
COPY services ./services
COPY sil ./sil
COPY sovereign_ai ./sovereign_ai
COPY tools ./tools
COPY utils ./utils
COPY ai ./ai
COPY scripts ./scripts

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
