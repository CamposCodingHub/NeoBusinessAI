"""
Storage Service
===============
Serviço de armazenamento seguro com R2/S3 e URLs temporárias.
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import uuid
import os

from core.config import settings


class StorageService:
    """Serviço de armazenamento com R2/S3"""
    
    def __init__(self):
        # Configurar cliente S3 (R2 ou AWS S3)
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.STORAGE_ENDPOINT,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=settings.STORAGE_REGION
        )
        self.bucket = settings.STORAGE_BUCKET
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        tenant_id: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, str]:
        """
        Upload de arquivo para storage privado.
        
        Args:
            file_content: Conteúdo do arquivo
            filename: Nome do arquivo
            tenant_id: ID do tenant (para isolamento)
            content_type: MIME type
            
        Returns:
            Tuple[storage_key, file_url]
        """
        # Gerar storage key isolado por tenant
        safe_filename = self._sanitize_filename(filename)
        storage_key = f"tenants/{tenant_id}/{uuid.uuid4()}/{safe_filename}"
        
        try:
            # Upload com ACL privado
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=file_content,
                ContentType=content_type,
                ACL='private'  # Sem acesso público
            )
            
            # URL temporária (não usada no upload, mas gerada sob demanda)
            file_url = f"s3://{self.bucket}/{storage_key}"
            
            return storage_key, file_url
            
        except ClientError as e:
            raise Exception(f"Erro ao fazer upload: {e}")
    
    def generate_presigned_url(
        self,
        storage_key: str,
        expiration_seconds: int = 3600
    ) -> str:
        """
        Gera URL temporária para download seguro.
        
        Args:
            storage_key: Chave do arquivo no storage
            expiration_seconds: Tempo de expiração em segundos
            
        Returns:
            URL temporária assinada
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key
                },
                ExpiresIn=expiration_seconds
            )
            return url
            
        except ClientError as e:
            raise Exception(f"Erro ao gerar URL: {e}")
    
    def delete_file(self, storage_key: str) -> bool:
        """
        Deleta arquivo do storage.
        
        Args:
            storage_key: Chave do arquivo
            
        Returns:
            True se deletado com sucesso
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=storage_key
            )
            return True
            
        except ClientError as e:
            print(f"Erro ao deletar arquivo: {e}")
            return False
    
    def get_file_metadata(self, storage_key: str) -> dict:
        """
        Obtém metadados do arquivo.
        
        Args:
            storage_key: Chave do arquivo
            
        Returns:
            Dict com metadados
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=storage_key
            )
            
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "metadata": response.get("Metadata", {})
            }
            
        except ClientError as e:
            raise Exception(f"Erro ao obter metadados: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza nome de arquivo.
        
        Args:
            filename: Nome original
            
        Returns:
            Nome sanitizado
        """
        # Remover path traversal
        filename = os.path.basename(filename)
        
        # Remover caracteres perigosos
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Limitar tamanho
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
        
        return filename
    
    def check_file_safety(self, file_content: bytes, filename: str) -> bool:
        """
        Verifica segurança do arquivo (anti-vírus básico).
        
        Args:
            file_content: Conteúdo do arquivo
            filename: Nome do arquivo
            
        Returns:
            True se seguro, False se suspeito
        """
        # Verificar extensões perigosas
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.scr', '.pif',
            '.com', '.vbs', '.js', '.jar', '.app'
        ]
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in dangerous_extensions:
            return False
        
        # Verificar tamanho máximo (50MB)
        if len(file_content) > 50 * 1024 * 1024:
            return False
        
        # TODO: Integrar com anti-vírus real (ClamAV, etc)
        
        return True


# Singleton instance
storage_service = StorageService()
