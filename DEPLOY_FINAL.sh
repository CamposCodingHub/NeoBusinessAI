#!/bin/bash
# 🚀 DEPLOY FINAL - LEXSCAN IA
# Script de deploy para produção (Linux/Mac)

echo "🚀 INICIANDO DEPLOY FINAL - LEXSCAN IA"
echo "=========================================="

# 1. Verificar variáveis de ambiente
echo "✅ Verificando variáveis de ambiente..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL não configurada!"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL não configurada!"
    exit 1
fi

# 2. Testar conexão com banco
echo "✅ Testando conexão PostgreSQL..."
cd backend
python -c "from database import engine; engine.connect()" || exit 1

# 3. Aplicar migrações
echo "✅ Aplicando migrações..."
python -c "from database import init_db; init_db()" || exit 1

# 4. Criar índices otimizados
echo "✅ Criando índices otimizados..."
python database_optimizations.py || exit 1

# 5. Iniciar backend
echo "✅ Iniciando backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 &
BACKEND_PID=$!

# 6. Iniciar Celery workers
echo "✅ Iniciando Celery workers..."
celery -A tasks worker --loglevel=info --concurrency=4 &
CELERY_PID=$!

# 7. Iniciar Celery beat
echo "✅ Iniciando Celery beat..."
celery -A tasks beat --loglevel=info &
BEAT_PID=$!

# 8. Health check
echo "⏳ Aguardando serviços iniciarem..."
sleep 5

echo "✅ Health check..."
curl -f http://localhost:8000/api/health || {
    echo "❌ Health check falhou!"
    kill $BACKEND_PID $CELERY_PID $BEAT_PID
    exit 1
}

echo ""
echo "=========================================="
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "=========================================="
echo ""
echo "🔗 Endpoints disponíveis:"
echo "  • Health: http://localhost:8000/api/health"
echo "  • API: http://localhost:8000/api"
echo "  • Docs: http://localhost:8000/docs"
echo ""
echo "📊 Monitoramento:"
echo "  • Backend PID: $BACKEND_PID"
echo "  • Celery PID: $CELERY_PID"
echo "  • Beat PID: $BEAT_PID"
echo ""
echo "🚀 Sistema LexScan IA está ONLINE!"
echo ""
echo "Para parar: kill $BACKEND_PID $CELERY_PID $BEAT_PID"
