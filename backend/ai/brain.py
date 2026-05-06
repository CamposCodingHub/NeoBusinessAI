from tools.web_search import web_search, should_search_web

class Brain:
    def needs_web(self, user_input):
        """
        Decide se precisa buscar na internet
        Usa algoritmo avancado de deteccao
        """
        return should_search_web(user_input)

    def get_context(self, user_input):
        """
        Busca informacoes na web quando necessario
        Retorna resultados formatados para a IA usar
        """
        if self.needs_web(user_input):
            print("[WEB] Buscando informacoes atualizadas na internet...")
            search_results = web_search(user_input, num_results=3)
            
            # Formata para o LLM entender melhor
            if search_results and not search_results.startswith("["):
                return f"""Informacoes encontradas na web (use apenas se relevante):

{search_results}

Baseie sua resposta nestas informacoes quando apropriado, mas mantenha seu tom conversacional."""
            else:
                return ""

        return ""