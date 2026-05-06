#!/usr/bin/env python
"""
Script para iniciar o servidor backend
Resolve problema de PATH do uvicorn no Windows
"""

import uvicorn
import sys

if __name__ == "__main__":
    print("🚀 Iniciando NeoBusiness AI Backend...")
    print("="*60)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
