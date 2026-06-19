"""Pesquisa juridica atual em feeds e sitemaps de autoridades oficiais."""

from __future__ import annotations

import concurrent.futures
import html
import re
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

import requests

from services.official_legal_sources_service import (
    PlainTextHTMLParser,
    official_legal_sources,
)


REALTIME_MARKERS = (
    "tempo real",
    "na internet",
    "pesquise na web",
    "pesquise online",
    "atualizado",
    "atualizada",
    "atualizacao recente",
    "atualização recente",
    "mudanca recente",
    "mudança recente",
    "ultimas noticias",
    "últimas notícias",
    "ultimas decisoes",
    "últimas decisões",
    "vigente hoje",
    "publicado hoje",
    "publicada hoje",
    "deste ano",
    "em 2026",
)

STOPWORDS = {
    "sobre",
    "quais",
    "qual",
    "como",
    "para",
    "pela",
    "pelo",
    "uma",
    "das",
    "dos",
    "com",
    "sem",
    "mais",
    "tempo",
    "real",
    "internet",
    "pesquise",
    "online",
    "atualizado",
    "atualizada",
    "hoje",
}

OFFICIAL_CHANNELS = (
    {
        "authority": "Receita Federal",
        "domain": "www.gov.br",
        "scope": "/receitafederal/",
        "rss": (
            "https://www.gov.br/receitafederal/pt-br/assuntos/noticias/RSS",
        ),
        "sitemaps": (
            "https://www.gov.br/receitafederal/pt-br/sitemap.xml",
        ),
    },
    {
        "authority": "Ministerio da Fazenda",
        "domain": "www.gov.br",
        "scope": "/fazenda/",
        "rss": (),
        "sitemaps": (
            "https://www.gov.br/fazenda/pt-br/sitemap.xml",
        ),
    },
    {
        "authority": "Autoridade Nacional de Protecao de Dados",
        "domain": "www.gov.br",
        "scope": "/anpd/",
        "rss": (),
        "sitemaps": (),
    },
    {
        "authority": "Ministerio do Trabalho e Emprego",
        "domain": "www.gov.br",
        "scope": "/trabalho-e-emprego/",
        "rss": (),
        "sitemaps": (
            "https://www.gov.br/trabalho-e-emprego/pt-br/sitemap.xml",
        ),
    },
    {
        "authority": "Conselho Nacional de Justica",
        "domain": "www.cnj.jus.br",
        "scope": "/",
        "rss": (),
        "sitemaps": ("https://www.cnj.jus.br/sitemap_index.xml",),
    },
)


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


def query_terms(query: str) -> List[str]:
    return list(
        dict.fromkeys(
            term
            for term in re.findall(r"[a-z0-9]+", normalize(query))
            if len(term) >= 4 and term not in STOPWORDS
        )
    )[:14]


@dataclass
class RealtimeOfficialSource:
    title: str
    url: str
    authority: str
    domain: str
    excerpt: str
    published_at: str | None
    updated_at: str | None
    retrieved_at: str
    score: float
    source_kind: str


class OfficialRealtimeResearchService:
    def __init__(self, cache_ttl_seconds: int = 600):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._resource_cache: Dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "NeoBusinessAI/1.0 pesquisa-juridica-oficial "
                    "(contato local; sem coleta massiva)"
                ),
                "Accept-Language": "pt-BR,pt;q=0.9",
            }
        )

    @staticmethod
    def should_research(query: str) -> bool:
        normalized = normalize(query)
        return any(normalize(marker) in normalized for marker in REALTIME_MARKERS)

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        cache_key = f"{normalize(query)}:{max_results}"
        with self._lock:
            cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return {**cached[1], "cache_hit": True}

        started = time.perf_counter()
        terms = query_terms(query)
        candidates: List[Dict[str, Any]] = []
        errors = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for channel in OFFICIAL_CHANNELS:
                for rss_url in channel["rss"]:
                    futures.append(
                        executor.submit(
                            self._read_feed,
                            rss_url,
                            channel,
                            terms,
                        )
                    )
                for sitemap_url in channel["sitemaps"]:
                    futures.append(
                        executor.submit(
                            self._read_sitemap,
                            sitemap_url,
                            channel,
                            terms,
                        )
                    )
            for future in concurrent.futures.as_completed(futures):
                try:
                    candidates.extend(future.result())
                except Exception as exc:
                    errors.append(str(exc)[:240])

        candidates.sort(key=lambda item: item["score"], reverse=True)
        unique_candidates = []
        seen_urls = set()
        for candidate in candidates:
            canonical = candidate["url"].split("#", 1)[0].rstrip("/")
            if canonical in seen_urls:
                continue
            seen_urls.add(canonical)
            unique_candidates.append(candidate)
            if len(unique_candidates) >= max(max_results * 3, 12):
                break

        details = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {
                executor.submit(self._enrich_candidate, item, query): item
                for item in unique_candidates
            }
            for future in concurrent.futures.as_completed(future_map):
                try:
                    enriched = future.result()
                    if enriched:
                        details.append(enriched)
                except Exception as exc:
                    errors.append(str(exc)[:240])

        details.sort(key=lambda item: item.score, reverse=True)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "query": query,
            "status": "verified" if details else "no_verified_results",
            "used": bool(details),
            "retrieved_at": retrieved_at,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "cache_hit": False,
            "results": [
                asdict(item) for item in details[:max_results]
            ],
            "errors": list(dict.fromkeys(errors))[:5],
            "policy": (
                "Somente paginas de autoridades oficiais configuradas sao "
                "aceitas; a geracao de texto permanece local."
            ),
        }
        with self._lock:
            self._cache[cache_key] = (time.time(), payload)
        return payload

    def _get_text(self, url: str, timeout: int = 18) -> str:
        cached = self._resource_cache.get(url)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return cached[1]
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        text = response.text
        self._resource_cache[url] = (time.time(), text)
        return text

    def _read_feed(
        self,
        url: str,
        channel: Dict[str, Any],
        terms: List[str],
    ) -> List[Dict[str, Any]]:
        root = ET.fromstring(self._get_text(url))
        candidates = []
        for item in root.iter():
            if item.tag.rsplit("}", 1)[-1].lower() not in {"item", "entry"}:
                continue
            values = self._xml_values(item)
            link = values.get("link") or item.attrib.get("href") or ""
            if not self._allowed_url(link, channel):
                continue
            title = values.get("title") or link
            description = values.get("description") or values.get("summary") or ""
            score = self._score(
                f"{title} {description} {link}",
                terms,
            )
            if score <= 0:
                continue
            candidates.append(
                {
                    "title": title,
                    "url": link,
                    "authority": channel["authority"],
                    "domain": channel["domain"],
                    "snippet": self._clean_html(description),
                    "published_at": self._parse_date(
                        values.get("pubdate")
                        or values.get("published")
                        or values.get("date")
                    ),
                    "updated_at": self._parse_date(values.get("updated")),
                    "score": min(1.0, score + 0.12),
                    "source_kind": "official_feed",
                }
            )
        return candidates

    def _read_sitemap(
        self,
        url: str,
        channel: Dict[str, Any],
        terms: List[str],
        depth: int = 0,
    ) -> List[Dict[str, Any]]:
        root = ET.fromstring(self._get_text(url))
        root_name = root.tag.rsplit("}", 1)[-1].lower()
        if root_name == "sitemapindex" and depth == 0:
            child_urls = [
                values.get("loc", "")
                for child in root
                if (values := self._xml_values(child)).get("loc")
            ][:8]
            results = []
            for child_url in child_urls:
                try:
                    results.extend(
                        self._read_sitemap(
                            child_url,
                            channel,
                            terms,
                            depth=1,
                        )
                    )
                except Exception:
                    continue
            return results

        candidates = []
        for child in root:
            values = self._xml_values(child)
            link = values.get("loc") or ""
            if not self._allowed_url(link, channel):
                continue
            score = self._score(link.replace("-", " ").replace("/", " "), terms)
            if score <= 0:
                continue
            candidates.append(
                {
                    "title": "",
                    "url": link,
                    "authority": channel["authority"],
                    "domain": channel["domain"],
                    "snippet": "",
                    "published_at": None,
                    "updated_at": self._parse_date(values.get("lastmod")),
                    "score": score,
                    "source_kind": "official_sitemap",
                }
            )
        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[:20]

    def _enrich_candidate(
        self,
        candidate: Dict[str, Any],
        query: str,
    ) -> RealtimeOfficialSource | None:
        page = self._get_text(candidate["url"])
        title = self._meta_value(page, "og:title") or self._html_title(page)
        description = (
            self._meta_value(page, "description")
            or self._meta_value(page, "og:description")
            or candidate.get("snippet")
            or ""
        )
        published = (
            self._meta_value(page, "article:published_time")
            or self._meta_value(page, "date")
            or candidate.get("published_at")
        )
        updated = (
            self._meta_value(page, "article:modified_time")
            or self._meta_value(page, "last-modified")
            or candidate.get("updated_at")
        )
        parser = PlainTextHTMLParser()
        parser.feed(page)
        page_text = parser.text()
        published = published or self._visible_date(
            page_text,
            "Publicado em",
        )
        updated = updated or self._visible_date(
            page_text,
            "Atualizado em",
        )
        excerpt = official_legal_sources._extract_relevant_excerpt(
            page_text,
            query,
            max_characters=1600,
        )
        combined = f"{title} {description} {excerpt} {candidate['url']}"
        score = min(
            1.0,
            candidate["score"] * 0.55
            + self._score(combined, query_terms(query)) * 0.45,
        )
        if score < 0.12:
            return None
        return RealtimeOfficialSource(
            title=html.unescape(title or candidate["url"]).strip(),
            url=candidate["url"],
            authority=candidate["authority"],
            domain=candidate["domain"],
            excerpt=(excerpt or description)[:1600].strip(),
            published_at=self._parse_date(published),
            updated_at=self._parse_date(updated),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            score=round(score, 6),
            source_kind=candidate["source_kind"],
        )

    @staticmethod
    def _xml_values(element: ET.Element) -> Dict[str, str]:
        values = {}
        for child in element:
            key = child.tag.rsplit("}", 1)[-1].lower()
            value = "".join(child.itertext()).strip()
            if key == "link" and not value:
                value = child.attrib.get("href", "")
            values[key] = value
        return values

    @staticmethod
    def _allowed_url(url: str, channel: Dict[str, Any]) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and host == channel["domain"]
            and channel["scope"] in parsed.path
        )

    @staticmethod
    def _score(text: str, terms: Iterable[str]) -> float:
        normalized = normalize(text)
        terms = list(terms)
        if not terms:
            return 0.0
        hits = sum(1 for term in terms if term in normalized)
        return min(1.0, hits / max(2, len(terms) * 0.55))

    @staticmethod
    def _clean_html(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()

    @staticmethod
    def _meta_value(page: str, name: str) -> str:
        patterns = (
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\']'
            rf'[^>]+content=["\']([^"\']+)',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+'
            rf'(?:name|property)=["\']{re.escape(name)}["\']',
        )
        for pattern in patterns:
            match = re.search(pattern, page, re.IGNORECASE)
            if match:
                return html.unescape(match.group(1)).strip()
        return ""

    @staticmethod
    def _html_title(page: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
        return (
            html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
            if match
            else ""
        )

    @staticmethod
    def _parse_date(value: str | None) -> str | None:
        if not value:
            return None
        raw = str(value).strip()
        try:
            parsed = parsedate_to_datetime(raw)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
        try:
            return datetime.fromisoformat(
                raw.replace("Z", "+00:00")
            ).astimezone(timezone.utc).isoformat()
        except ValueError:
            return raw[:80]

    @staticmethod
    def _visible_date(text: str, label: str) -> str | None:
        match = re.search(
            rf"{re.escape(label)}\s+"
            r"(\d{2}/\d{2}/\d{4}(?:\s+\d{1,2}h\d{2})?)",
            text,
            re.IGNORECASE,
        )
        if not match:
            return None
        raw = match.group(1)
        for pattern in ("%d/%m/%Y %Hh%M", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw, pattern).replace(
                    tzinfo=timezone.utc
                ).isoformat()
            except ValueError:
                continue
        return raw


official_realtime_research = OfficialRealtimeResearchService()
