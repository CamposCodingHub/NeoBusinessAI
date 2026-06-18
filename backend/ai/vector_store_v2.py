"""
Vector Database Avançado para RAG
=================================
Suporta: Pinecone, Weaviate, FAISS local
Features: Chunking inteligente, metadados ricos, busca híbrida
"""

import os
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Chunk de documento com metadados"""
    id: str
    text: str
    document_id: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class VectorStoreV2:
    """
    Vector Database V2 para RAG
    Suporta múltiplos backends: Pinecone, Weaviate, FAISS
    """
    
    def __init__(self, backend: str = "faiss", api_key: Optional[str] = None):
        self.backend = backend
        self.api_key = api_key
        self.chunks: List[DocumentChunk] = []
        self.index = None
        self.embedding_model = None
        
        # Inicializar backend
        if backend == "pinecone":
            self._init_pinecone()
        elif backend == "weaviate":
            self._init_weaviate()
        else:
            self._init_faiss()
        
        logger.info(f"✅ Vector Store V2 inicializado com backend: {backend}")
    
    def _init_pinecone(self):
        """Inicializa Pinecone"""
        try:
            import pinecone
            pinecone.init(api_key=self.api_key)
            self.index_name = "neobusiness-docs"
            
            # Criar índice se não existir
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=384,
                    metric="cosine",
                    metadata_config={"indexed": ["document_id", "chunk_type"]}
                )
            
            self.index = pinecone.Index(self.index_name)
            logger.info("✅ Pinecone inicializado")
        except ImportError:
            logger.warning("Pinecone não instalado, usando FAISS local")
            self._init_faiss()
        except Exception as e:
            logger.warning(f"Pinecone falhou: {e}, usando FAISS local")
            self._init_faiss()
    
    def _init_weaviate(self):
        """Inicializa Weaviate"""
        try:
            import weaviate
            self.client = weaviate.Client(
                url=os.getenv("WEAVIATE_URL", "http://localhost:8080")
            )
            logger.info("✅ Weaviate inicializado")
        except ImportError:
            logger.warning("Weaviate não instalado, usando FAISS local")
            self._init_faiss()
        except Exception as e:
            logger.warning(f"Weaviate falhou: {e}, usando FAISS local")
            self._init_faiss()
    
    def _init_faiss(self):
        """Inicializa FAISS local"""
        try:
            import faiss
            import numpy as np
            self.index = faiss.IndexFlatL2(384)
            logger.info("✅ FAISS local inicializado")
        except ImportError:
            logger.error("FAISS não instalado. Execute: pip install faiss-cpu")
    
    def _init_embedding_model(self):
        """Inicializa modelo de embeddings"""
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
            except ImportError:
                logger.error("sentence-transformers não instalado")
    
    def chunk_document(
        self,
        text: str,
        document_id: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[DocumentChunk]:
        """
        Chunking inteligente de documento
        Divide em chunks com overlap mantendo contexto
        """
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_text = " ".join(words[i:i + chunk_size])
            
            chunk_id = hashlib.md5(
                f"{document_id}_{i}".encode()
            ).hexdigest()
            
            chunk = DocumentChunk(
                id=chunk_id,
                text=chunk_text,
                document_id=document_id,
                chunk_index=i // (chunk_size - overlap),
                metadata={
                    "chunk_type": "text",
                    "word_count": len(chunk_text.split()),
                    "char_count": len(chunk_text)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def add_document(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> List[str]:
        """
        Adiciona documento ao vector store
        Retorna IDs dos chunks criados
        """
        self._init_embedding_model()
        
        # Chunk documento
        chunks = self.chunk_document(text, document_id)
        
        # Adicionar metadados adicionais
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)
        
        # Gerar embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_model.encode(texts)
        
        # Adicionar ao backend
        chunk_ids = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding.tolist()
            chunk_ids.append(chunk.id)
            
            if self.backend == "pinecone":
                self._add_to_pinecone(chunk, embedding)
            elif self.backend == "weaviate":
                self._add_to_weaviate(chunk, embedding)
            else:
                self._add_to_faiss(chunk, embedding)
        
        self.chunks.extend(chunks)
        logger.info(f"✅ Documento {document_id} adicionado com {len(chunks)} chunks")
        
        return chunk_ids
    
    def _add_to_pinecone(self, chunk: DocumentChunk, embedding):
        """Adiciona chunk ao Pinecone"""
        import numpy as np
        self.index.upsert(
            vectors=[(
                chunk.id,
                embedding.tolist(),
                {
                    "text": chunk.text[:1000],  # Pinecone limit
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata
                }
            )]
        )
    
    def _add_to_weaviate(self, chunk: DocumentChunk, embedding):
        """Adiciona chunk ao Weaviate"""
        self.client.data_object.create(
            data_object={
                "text": chunk.text,
                "documentId": chunk.document_id,
                "chunkIndex": chunk.chunk_index,
                "metadata": chunk.metadata
            },
            class_name="DocumentChunk",
            vector=embedding.tolist()
        )
    
    def _add_to_faiss(self, chunk: DocumentChunk, embedding):
        """Adiciona chunk ao FAISS"""
        import numpy as np
        self.index.add(np.array([embedding]).astype("float32"))
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca chunks similares
        """
        self._init_embedding_model()
        
        # Gerar embedding da query
        query_embedding = self.embedding_model.encode([query])
        
        # Buscar no backend
        if self.backend == "pinecone":
            return self._search_pinecone(query_embedding, top_k, filters)
        elif self.backend == "weaviate":
            return self._search_weaviate(query_embedding, top_k, filters)
        else:
            return self._search_faiss(query_embedding, top_k)
    
    def _search_pinecone(
        self,
        embedding,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Busca no Pinecone"""
        import numpy as np
        
        results = self.index.query(
            vector=embedding.tolist(),
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )
        
        return [
            {
                "id": match.id,
                "text": match.metadata.get("text", ""),
                "document_id": match.metadata.get("document_id"),
                "score": match.score,
                "metadata": match.metadata
            }
            for match in results.matches
        ]
    
    def _search_weaviate(
        self,
        embedding,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Busca no Weaviate"""
        results = self.client.query.get(
            "DocumentChunk",
            top_k,
            vector=embedding.tolist()
        )
        
        return [
            {
                "id": result.uuid,
                "text": result.properties["text"],
                "document_id": result.properties["documentId"],
                "metadata": result.properties["metadata"]
            }
            for result in results.objects
        ]
    
    def _search_faiss(self, embedding, top_k: int) -> List[Dict[str, Any]]:
        """Busca no FAISS"""
        import numpy as np
        
        D, I = self.index.search(
            np.array(embedding).astype("float32"),
            top_k
        )
        
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    "id": chunk.id,
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    "score": float(score),
                    "metadata": chunk.metadata
                })
        
        return results
    
    def delete_document(self, document_id: str):
        """Remove todos os chunks de um documento"""
        if self.backend == "pinecone":
            self.index.delete(filter={"document_id": {"$eq": document_id}})
        
        # Remover da memória local
        self.chunks = [c for c in self.chunks if c.document_id != document_id]
        
        logger.info(f"✅ Documento {document_id} removido")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do vector store"""
        return {
            "backend": self.backend,
            "total_chunks": len(self.chunks),
            "total_documents": len(set(c.document_id for c in self.chunks)),
            "index_size": self.index.ntotal if self.index else 0
        }


# Instância global
from config import settings

vector_store = VectorStoreV2(
    backend="faiss",  # Pode ser "pinecone" ou "weaviate" com API key
    api_key=os.getenv("PINECONE_API_KEY")
)
