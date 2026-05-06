"""
Groq API Client - A API mais rápida do mundo para LLMs
Respostas em ~500ms (vs 5-10s local)
"""

import os
from typing import Optional, List, Dict

class GroqClient:
    """Cliente para API Groq - inferência ultrarrápida"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        
        # Modelos disponíveis (mais rápidos primeiro)
        self.models = {
            "fast": "llama-3.1-8b-instant",      # Mais rápido ~300ms
            "balanced": "llama-3.1-70b-versatile", # Equilibrado ~800ms
            "smart": "mixtral-8x7b-32768",        # Mais inteligente ~1s
        }
        
        self.available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Verifica se a API está configurada"""
        if not self.api_key:
            print("[GROQ] API key nao configurada")
            return False
        
        # Verifica se a chave parece valida (comeca com gsk_)
        if not self.api_key.startswith("gsk_"):
            print("[GROQ] API key invalida")
            return False
        
        print("[GROQ] API key configurada")
        return True
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: str = "",
        model: str = "fast",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Gera resposta usando Groq API
        
        Args:
            prompt: Pergunta do usuário
            system_prompt: Instruções do sistema
            model: 'fast', 'balanced', ou 'smart'
            max_tokens: Máximo de tokens na resposta
            temperature: Criatividade (0.0-1.0)
            stream: Se True, retorna generator para streaming
        
        Returns:
            Resposta em string (ou generator se stream=True)
        """
        if not self.available:
            raise RuntimeError("Groq API não disponível")
        
        import urllib.request
        import json
        import ssl
        
        model_id = self.models.get(model, self.models["fast"])
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        if stream:
            return self._stream_response(req, ctx)
        
        # Resposta completa de uma vez
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]
    
    def _stream_response(self, req, ctx):
        """Generator para streaming de resposta"""
        import urllib.request
        import json
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: '
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except:
                        pass
    
    def generate_fast(self, prompt: str, system_prompt: str = "") -> str:
        """Método rápido - usa modelo mais veloz"""
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model="fast",
            max_tokens=1024,
            temperature=0.7
        )


# Instância global
groq_client: Optional[GroqClient] = None

def get_groq_client() -> Optional[GroqClient]:
    """Retorna instância singleton do cliente Groq"""
    global groq_client
    if groq_client is None:
        groq_client = GroqClient()
    return groq_client


if __name__ == "__main__":
    # Teste rapido
    client = GroqClient()
    if client.available:
        print("\n[Testando Groq API...]")
        response = client.generate_fast(
            "Ola! Quem e voce?",
            "Voce e um assistente amigavel. Responda em portugues."
        )
        print(f"Resposta: {response}")
        print("\n[OK] Groq API funcionando!")
    else:
        print("\n[ERRO] Configure GROQ_API_KEY")
        print("Obtenha em: https://console.groq.com/keys")
