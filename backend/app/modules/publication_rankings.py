from __future__ import annotations

import os
import re
from typing import Any

import requests

from app.modules.qs_ranking_matcher import get_qs_ranking


def _safe_request_json(url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return None
        payload = response.json()
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _extract_journal_title(publication: dict[str, Any]) -> str | None:
    for key in ("journal", "venue", "source", "publisher"):
        value = publication.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    title = publication.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


def _extract_issn(publication: dict[str, Any]) -> str | None:
    for key in ("issn", "issn_print", "issn_online", "identifier"):
        value = publication.get(key)
        if isinstance(value, str):
            match = re.search(r"\b\d{4}-\d{3}[\dXx]\b", value)
            if match:
                return match.group(0)
    return None


def _infer_conference_tier(publication: dict[str, Any]) -> str | None:
    text = " ".join(str(publication.get(key, "")) for key in ("title", "venue", "source", "journal")).lower()
    if any(token in text for token in ["a*", "star", "top conference", "sigir", "kdd", "cvpr", "neurips", "icml", "iccv", "eccv"]):
        return "A*"
    if any(token in text for token in ["scopus", "ieee", "acm", "springer"]):
        return "Indexed"
    return None


def _infer_quartile(qs_rank: int | None, api_payload: dict[str, Any] | None = None) -> str | None:
    if api_payload:
        quartile = api_payload.get("quartile") or api_payload.get("journal_quartile")
        if isinstance(quartile, str) and quartile.strip():
            return quartile.strip().upper()
    if qs_rank is None:
        return None
    if qs_rank <= 100:
        return "Q1"
    if qs_rank <= 250:
        return "Q2"
    if qs_rank <= 500:
        return "Q3"
    return "Q4"


def enrich_publication_rankings(publications: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Optional enrichment for publication and venue quality.

    Uses lightweight local heuristics first and only tries external APIs when
    corresponding environment variables are present.
    """
    ranked_publications: list[dict[str, Any]] = []
    api_hits = {"scopus": 0, "wos": 0, "core": 0}

    scopus_key = os.getenv("SCOPUS_API_KEY")
    wos_key = os.getenv("WOS_API_KEY")
    core_key = os.getenv("CORE_API_KEY")

    for publication in publications:
        enriched = dict(publication)
        venue_name = _extract_journal_title(publication)
        issn = _extract_issn(publication)

        if venue_name:
            qs_name, qs_rank = get_qs_ranking(venue_name)
            enriched["qs_lookup"] = {"name": qs_name, "rank": qs_rank}
            enriched["journal_quality"] = {
                "venue_name": qs_name,
                "qs_rank": qs_rank,
                "quartile": _infer_quartile(qs_rank),
                "issn": issn,
                "journal_legitimacy": "verified_title_match" if qs_rank else "unverified_title_match",
            }

        if venue_name and scopus_key:
            payload = _safe_request_json(
                "https://api.elsevier.com/content/serial/title",
                headers={"X-ELS-APIKey": scopus_key},
                params={"title": venue_name},
            )
            if payload:
                api_hits["scopus"] += 1
                enriched["scopus_lookup"] = payload
                enriched.setdefault("journal_quality", {})["quartile"] = _infer_quartile(
                    enriched.get("qs_lookup", {}).get("rank"),
                    payload,
                )
                enriched.setdefault("journal_quality", {})["scopus_indexed"] = True

        if venue_name and wos_key:
            payload = _safe_request_json(
                "https://api.clarivate.com/api/wos",
                headers={"X-ApiKey": wos_key},
                params={"query": venue_name},
            )
            if payload:
                api_hits["wos"] += 1
                enriched["wos_lookup"] = payload
                enriched.setdefault("journal_quality", {})["wos_indexed"] = True

        if venue_name and core_key:
            payload = _safe_request_json(
                "https://api.core.ac.uk/v3/search/works",
                headers={"Authorization": f"Bearer {core_key}"},
                params={"q": venue_name},
            )
            if payload:
                api_hits["core"] += 1
                enriched["core_lookup"] = payload
                enriched.setdefault("conference_quality", {})["core_indexed"] = True

        conference_tier = _infer_conference_tier(publication)
        if conference_tier:
            enriched["conference_quality"] = {
                **enriched.get("conference_quality", {}),
                "tier": conference_tier,
                "indexing_status": enriched.get("conference_quality", {}).get("core_indexed", False),
            }

        ranked_publications.append(enriched)

    journal_titles = [item for item in (_extract_journal_title(pub) for pub in ranked_publications) if item]
    return {
        "ranked_publications": ranked_publications,
        "api_hits": api_hits,
        "external_api_enabled": any([scopus_key, wos_key, core_key]),
        "journal_titles_checked": len(journal_titles),
        "notes": (
            "External ranking APIs were queried where credentials were available."
            if any(api_hits.values())
            else "No external ranking credentials were available; local ranking heuristics were used."
        ),
    }