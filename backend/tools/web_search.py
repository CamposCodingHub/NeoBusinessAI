import requests
import re
from urllib.parse import quote

def web_search(query, num_results=5):
    """
    Busca na web usando DuckDuckGo
    Retorna resultados formatados e limpos
    
    Args:
        query: Termo de busca
        num_results: Numero de resultados (default: 5)
    
    Returns:
        String formatada com titulos, URLs e snippets
    """
    
    try:
        # Codifica a query para URL
        encoded_query = quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        html = response.text
        
        # Extrai resultados usando regex
        results = []
        
        # Pattern para resultados DuckDuckGo
        result_blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.DOTALL | re.IGNORECASE
        )
        
        for i, (link, title, snippet) in enumerate(result_blocks[:num_results], 1):
            # Limpa HTML tags
            title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            
            # Decodifica entidades HTML
            title = title.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&')
            snippet = snippet.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&')
            
            if title and snippet:
                results.append(f"{i}. {title}\n   {snippet}\n   Link: {link}\n")
        
        if not results:
            return "Nenhum resultado encontrado para esta busca."
        
        return "\n".join(results)
        
    except requests.exceptions.Timeout:
        return "[Busca na web: Timeout - demorou muito para responder]"
    except requests.exceptions.RequestException as e:
        return f"[Busca na web: Erro de conexao - {str(e)}]"
    except Exception as e:
        return f"[Busca na web: Erro inesperado - {str(e)}]"


def should_search_web(query):
    """
    Decide se deve buscar na web baseado na pergunta
    
    Retorna True se a pergunta pede:
    - Precos, valores, cotacoes
    - Noticias recentes
    - Dados atualizados
    - Informacoes especificas que mudam com o tempo
    """
    
    web_keywords = [
        # Precos e valores
        "preco", "precos", "valor", "valores", "custo", "custa", "quanto custa",
        "cotacao", "cotação", "dolar", "euro", "bitcoin", "cripto",
        
        # Atualidades
        "noticia", "noticias", "ultimas", "atual", "agora", "hoje",
        "recente", "novidade", "lançamento", "lancamento", "novo",
        
        # Dados especificos
        "previsao", "previsão", "tempo", "clima", "trânsito", "transito",
        "horario", "horário", "funcionamento", "aberto", "fechado",
        
        # Comparacoes
        "melhor", "pior", "versus", "vs", "comparar", "diferenca",
        
        # Pessoas e empresas atuais
        "quem e", "quem é", "o que é", "quando", "onde fica",
        "ceo", "presidente", "don", "fundador",
    ]
    
    query_lower = query.lower()
    
    # Verifica se tem palavras-chave de busca
    has_web_keyword = any(keyword in query_lower for keyword in web_keywords)
    
    # Verifica se parece uma pergunta factual atual
    factual_starters = [
        "qual o preco", "quanto custa", "qual a cotacao",
        "quem é", "quem e", "o que é", "o que e",
        "quando", "onde", "como esta", "como está",
        "novo", "recente", "atual"
    ]
    
    has_factual = any(query_lower.startswith(starter) for starter in factual_starters)
    
    return has_web_keyword or has_factual


if __name__ == "__main__":
    # Teste rapido
    test_query = "preco iphone 15 brasil"
    print(f"Buscando: {test_query}")
    print("=" * 50)
    result = web_search(test_query, num_results=3)
    print(result)
    print("=" * 50)
    print(f"Deveria buscar web? {should_search_web(test_query)}")
