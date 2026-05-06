"""
Script de Backup Automático - PostgreSQL para S3
"""

import os
import subprocess
import boto3
from datetime import datetime, timedelta
from typing import Optional

# Configuração
DB_URL = os.getenv('DATABASE_URL')
S3_BUCKET = os.getenv('S3_BACKUP_BUCKET', 'jurisflow-backups')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

RETENTION_DAYS = 30  # Manter backups por 30 dias

def create_backup() -> Optional[str]:
    """
    Cria backup do PostgreSQL usando pg_dump
    """
    if not DB_URL:
        print("[Backup] ERRO: DATABASE_URL não configurada")
        return None
    
    # Gerar nome do arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"jurisflow_backup_{timestamp}.sql.gz"
    local_path = f"/tmp/{filename}"
    
    try:
        # Executar pg_dump
        print(f"[Backup] Criando backup: {filename}")
        
        # Extrair credenciais do DATABASE_URL
        # Assumindo formato: postgresql://user:pass@host:port/db
        cmd = [
            "pg_dump",
            "--format=custom",
            "--compress=9",
            "-f", local_path,
            DB_URL
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"[Backup] Backup criado: {local_path}")
        return local_path
        
    except subprocess.CalledProcessError as e:
        print(f"[Backup] ERRO ao criar backup: {e.stderr}")
        return None
    except FileNotFoundError:
        print("[Backup] ERRO: pg_dump não encontrado. Instale postgresql-client")
        return None

def upload_to_s3(local_path: str) -> bool:
    """
    Upload do backup para S3
    """
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        print("[Backup] AVISO: Credenciais AWS não configuradas")
        return False
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        
        filename = os.path.basename(local_path)
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        s3_key = f"backups/{date_prefix}/{filename}"
        
        print(f"[Backup] Upload para S3: {s3_key}")
        
        s3.upload_file(
            local_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256'
            }
        )
        
        print(f"[Backup] Upload concluído: s3://{S3_BUCKET}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"[Backup] ERRO no upload: {e}")
        return False

def cleanup_old_backups():
    """
    Remove backups antigos do S3 (mais de RETENTION_DAYS dias)
    """
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        # Listar objetos
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='backups/'
        )
        
        deleted_count = 0
        for obj in response.get('Contents', []):
            if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                s3.delete_object(Bucket=S3_BUCKET, Key=obj['Key'])
                deleted_count += 1
                print(f"[Backup] Deletado: {obj['Key']}")
        
        print(f"[Backup] {deleted_count} backups antigos removidos")
        
    except Exception as e:
        print(f"[Backup] ERRO ao limpar backups antigos: {e}")

def cleanup_local_file(local_path: str):
    """Remove arquivo local após upload"""
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"[Backup] Arquivo local removido: {local_path}")
    except Exception as e:
        print(f"[Backup] ERRO ao remover arquivo local: {e}")

def main():
    """Executa backup completo"""
    print("=" * 50)
    print("[Backup] Iniciando backup automático")
    print(f"[Backup] Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # 1. Criar backup
    local_path = create_backup()
    if not local_path:
        return False
    
    # 2. Upload para S3
    success = upload_to_s3(local_path)
    
    # 3. Limpar arquivo local
    cleanup_local_file(local_path)
    
    # 4. Limpar backups antigos
    cleanup_old_backups()
    
    if success:
        print("[Backup] ✅ Backup concluído com sucesso")
    else:
        print("[Backup] ⚠️ Backup criado mas não enviado para S3")
    
    return success

if __name__ == "__main__":
    main()
