from transformers import pipeline
import os
from ai.brain import Brain
from ai.memory import Memory
from ai.vector_store import VectorStore
from ai.groq_client import get_groq_client
from ai.prompts import get_full_system_prompt, get_random_transicao

class NeoBusinessAI:
    def __init__(self):
        print("[INFO] Inicializando NeoBusiness AI...")
        
        # 🚀 TENTA API GROQ PRIMEIRO (mais rápida)
        self.groq = get_groq_client()
        self.use_api = self.groq is not None and self.groq.available
        
        if self.use_api:
            print("[OK] Usando Groq API - respostas em ~500ms!")
            self.model = None  # Não carrega modelo local
        else:
            print("[INFO] Groq não disponível, carregando modelo local...")
            try:
                self.model = pipeline(
                    "text-generation",
                    model="microsoft/Phi-3-mini-4k-instruct",
                    device_map="auto"
                )
                print("[OK] Modelo local carregado (modo lento)")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar modelo: {e}")
                raise RuntimeError("Falha ao inicializar IA. Verifique memória.")

        # 🧠 módulos
        self.brain = Brain()
        self.memory = Memory()
        self.vector_store = None
        self.vector_store_loaded = False
        self.rag_enabled = os.getenv("ENABLE_LOCAL_RAG", "true").lower() in {"1", "true", "yes", "on"}

        mode = "API GROQ" if self.use_api else "Local"
        print(f"[OK] NeoBusiness AI pronta! Modo: {mode}\n")

    def _ensure_vector_store(self):
        if not self.rag_enabled or self.vector_store_loaded:
            return

        try:
            self.vector_store = VectorStore()
            self.vector_store.load_pdfs()
            self.vector_store_loaded = True
            print("[OK] Base vetorial carregada sob demanda.")
        except Exception as e:
            self.rag_enabled = False
            print(f"[AVISO] RAG desativado neste runtime: {e}")

    def ask(self, user_input: str):
        try:
            # 📚 memória para contexto da conversa
            history = self.memory.get_last()[-3:]
            memory_text = "\n".join(
                f"Usuario: {h[0]}\nIA: {h[1]}" for h in history
            ) if history else ""

            # 📄 busca RAG (conhecimento específico)
            knowledge = ""
            if len(user_input) > 10:
                try:
                    self._ensure_vector_store()
                    if self.vector_store is not None:
                        knowledge = self.vector_store.search(user_input, top_k=2)
                except Exception:
                    knowledge = ""

            # 🎯 Prompt do sistema DINÂMICO (varia a cada conversa)
            system_prompt = get_full_system_prompt()
            
            # 🧠 Contexto enriquecido
            context = ""
            if memory_text:
                context += f"Contexto da conversa anterior:\n{memory_text}\n\n"
            if knowledge:
                context += f"Informacoes relevantes:\n{knowledge}\n\n"

            # 🚀 USA GROQ API (rápida e inteligente)
            if self.use_api:
                # Mensagem otimizada para caber no limite de tokens
                user_message = f"Pergunta: {user_input}\n\nResponda com formatação markdown e quebras de linha reais entre cada elemento."
                
                full_prompt = f"{system_prompt}\n\n{context}{user_message}"
                final = self.groq.generate_fast(full_prompt, system_prompt)
            else:
                # 🐌 MODO LOCAL (fallback)
                prompt = f"""{system_prompt}

{context}

Pergunta: {user_input}

Responda como um consultor amigavel e experiente:"""
                response = self.model(
                    prompt,
                    max_new_tokens=1024,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1,
                    return_full_text=False
                )
                final = response[0]["generated_text"].strip()

            # 🧹 Limpeza e salvamento
            final = final.replace("</ASSISTANT>", "").strip()
            self.memory.save(user_input, final)
            
            return final

        except Exception as e:
            print(f"[ERRO] {e}")
            # Fallback para API se local falhou
            if not self.use_api and self.groq and self.groq.available:
                print("[FALLBACK] Usando API...")
                system_prompt = get_full_system_prompt()
                return self.groq.generate_fast(user_input, system_prompt)
            return "Ops, algo deu errado! Pode tentar de novo? Estou aqui para ajudar! 😊"
