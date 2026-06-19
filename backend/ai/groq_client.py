"""
Groq API Client - Usando biblioteca oficial
API mais rapida do mundo para LLMs
"""

import os
from typing import Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[GROQ] Biblioteca nao instalada. Execute: pip install groq")


def external_ai_allowed() -> bool:
    """Bloqueia provedores externos quando a operacao soberana esta ativa."""
    routing_policy = os.getenv("AI_ROUTING_POLICY", "local_only").strip().lower()
    fallback_enabled = (
        os.getenv("AI_EXTERNAL_FALLBACK_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    return routing_policy != "local_only" and fallback_enabled


class GroqClient:
    """Cliente Groq usando biblioteca oficial"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = None
        self.available = False

        if not external_ai_allowed():
            print("[GROQ] Desabilitada pela politica de IA local.")
            return
        
        if not GROQ_AVAILABLE:
            print("[GROQ] Biblioteca groq nao disponivel")
            return
            
        if not self.api_key:
            print("[GROQ] API key nao configurada")
            return
            
        try:
            self.client = Groq(api_key=self.api_key)
            self.available = True
            print("[GROQ] Cliente inicializado com sucesso")
        except Exception as e:
            print(f"[GROQ] Erro ao inicializar: {e}")
    
    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
        """Gera resposta usando Groq API"""
        if not self.available or not self.client:
            raise RuntimeError("Groq nao disponivel")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Modelo disponivel
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.8,  # Mais criatividade = mais humano
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[GROQ] Erro na geracao: {e}")
            raise
    
    def generate_fast(self, prompt: str, system_prompt: str = "") -> str:
        """Metodo rapido padrao"""
        return self.generate(prompt, system_prompt, max_tokens=1024)


# Instancia global
groq_client: Optional[GroqClient] = None

def get_groq_client() -> Optional[GroqClient]:
    """Retorna instancia singleton"""
    global groq_client
    if groq_client is None:
        groq_client = GroqClient()
    return groq_client
