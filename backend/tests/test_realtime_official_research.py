"""Testes da pesquisa web restrita a autoridades oficiais."""

from services.official_realtime_research_service import (
    OfficialRealtimeResearchService,
)


def test_realtime_detection_requires_explicit_current_request():
    assert OfficialRealtimeResearchService.should_research(
        "Pesquise na internet as atualizacoes recentes da Receita Federal."
    )
    assert not OfficialRealtimeResearchService.should_research(
        "Explique o artigo 312 do CPP."
    )


def test_official_sitemap_search_enriches_only_allowed_pages(monkeypatch):
    service = OfficialRealtimeResearchService()
    sitemap = """<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://www.gov.br/receitafederal/pt-br/noticias/reforma-tributaria-2026</loc>
        <lastmod>2026-06-18</lastmod>
      </url>
      <url>
        <loc>https://example.com/conteudo-nao-oficial</loc>
      </url>
    </urlset>
    """
    page = """
    <html><head>
      <title>Orientacoes da Reforma Tributaria 2026</title>
      <meta name="description" content="Novas orientacoes oficiais da CBS." />
    </head><body>
      Publicado em 18/06/2026 14h30
      A Receita Federal publicou novas orientacoes sobre a reforma tributaria,
      CBS, integracao de sistemas e apuracao assistida.
    </body></html>
    """

    def fake_get(url, timeout=18):
        del timeout
        return sitemap if url.endswith("sitemap.xml") else page

    monkeypatch.setattr(service, "_get_text", fake_get)
    monkeypatch.setattr(
        "services.official_realtime_research_service.OFFICIAL_CHANNELS",
        (
            {
                "authority": "Receita Federal",
                "domain": "www.gov.br",
                "scope": "/receitafederal/",
                "rss": (),
                "sitemaps": ("https://www.gov.br/receitafederal/sitemap.xml",),
            },
        ),
    )

    result = service.search(
        "Informacoes atualizadas da reforma tributaria 2026",
        max_results=3,
    )

    assert result["status"] == "verified"
    assert len(result["results"]) == 1
    assert result["results"][0]["authority"] == "Receita Federal"
    assert result["results"][0]["url"].startswith("https://www.gov.br/")
    assert result["results"][0]["published_at"].startswith("2026-06-18")
