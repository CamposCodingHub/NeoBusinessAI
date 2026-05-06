#!/usr/bin/env python3
"""
Script de Migração: SQLite → PostgreSQL
Transfere todos os dados do banco SQLite para PostgreSQL
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Document, Notification, ActivityLog, SubscriptionHistory, Deadline, WhatsAppConfig, ChatMessage, NotificationQueue, Client, Invoice

def migrate_data():
    print("🔄 Iniciando migração SQLite → PostgreSQL...")
    
    # Conexão SQLite (origem)
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lexscan.db')
    sqlite_url = f"sqlite:///{sqlite_path}"
    sqlite_engine = create_engine(sqlite_url)
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # Conexão PostgreSQL (destino)
    postgres_url = os.getenv('DATABASE_URL')
    if not postgres_url or 'postgresql' not in postgres_url:
        print("❌ ERRO: DATABASE_URL não configurada para PostgreSQL")
        print("Configure a variável DATABASE_URL no arquivo .env")
        return False
    
    postgres_engine = create_engine(postgres_url)
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgresSession()
    
    # Criar tabelas no PostgreSQL
    print("📦 Criando tabelas no PostgreSQL...")
    Base.metadata.create_all(bind=postgres_engine)
    
    # Mapeamento de modelos e ordem de migração (respeitando FKs)
    models = [
        User,
        Document,
        Notification,
        ActivityLog,
        SubscriptionHistory,
        Deadline,
        WhatsAppConfig,
        ChatMessage,
        NotificationQueue,
        Client,
        Invoice,
    ]
    
    total_records = 0
    
    for model in models:
        table_name = model.__tablename__
        print(f"\n📤 Migrando {table_name}...")
        
        # Buscar dados do SQLite
        records = sqlite_session.query(model).all()
        count = len(records)
        
        if count == 0:
            print(f"   ⚪ {table_name}: 0 registros (pulando)")
            continue
        
        print(f"   📝 {table_name}: {count} registros encontrados")
        
        # Inserir no PostgreSQL
        for i, record in enumerate(records):
            # Converter para dict e remover o ID para auto-incremento
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                record_dict[column.name] = value
            
            # Criar novo registro
            new_record = model(**record_dict)
            postgres_session.add(new_record)
            
            if (i + 1) % 100 == 0:
                postgres_session.commit()
                print(f"   ⏳ {table_name}: {i + 1}/{count}...")
        
        postgres_session.commit()
        total_records += count
        print(f"   ✅ {table_name}: {count} registros migrados")
    
    sqlite_session.close()
    postgres_session.close()
    
    print(f"\n🎉 Migração concluída!")
    print(f"📊 Total de registros migrados: {total_records}")
    print(f"\n⚠️ IMPORTANTE:")
    print(f"   1. Verifique se os dados foram migrados corretamente")
    print(f"   2. Atualize DATABASE_URL no .env para apontar para PostgreSQL")
    print(f"   3. Faça backup do SQLite antes de deletar")
    
    return True

if __name__ == "__main__":
    try:
        success = migrate_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO durante migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
