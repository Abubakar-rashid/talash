from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.modules.preprocessing import extract_publication_records


def _extract_authors_from_line(line: str) -> list[str]:
    """Extract potential author names from a publication line."""
    # Common patterns:
    # "Title by Author1, Author2"
    # "Author1 et al., Title"
    # "Title | Author1 & Author2"
    
    authors = []
    
    # Try to extract names using common separators
    separators = [", ", " and ", " & ", "|", ";"]
    text_without_title_markers = re.sub(r"\b(?:in|published|journal|conference|proceedings)\b", "", line, flags=re.IGNORECASE)
    
    for sep in separators:
        if sep in text_without_title_markers:
            parts = text_without_title_markers.split(sep)
            for part in parts:
                part = part.strip()
                # Check if part looks like author names (has capital letters, reasonable length)
                if part and 3 <= len(part) <= 100 and not any(
                    keyword in part.lower() 
                    for keyword in ["conference", "journal", "proceedings", "volume", "page", "http"]
                ):
                    # Try to extract individual names
                    if " et al" in part.lower():
                        match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)\s+et al", part)
                        if match:
                            authors.append(match.group(1))
                    else:
                        # Extract capitalized sequences that look like names
                        names = re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", part)
                        authors.extend(names)
    
    return list(set(authors))  # Remove duplicates


def _extract_research_domains(raw_text: str) -> list[str]:
    """Identify research domains/areas from publication titles and text."""
    research_domains = {
        "AI/ML": ["machine learning", "deep learning", "neural network", "nlp", "natural language", "computer vision", "ai", "artificial intelligence"],
        "Data Science": ["data mining", "data science", "analytics", "big data", "statistics"],
        "Web/Cloud": ["web", "cloud", "distributed", "microservice", "api", "rest"],
        "Systems": ["operating system", "database", "distributed system", "architecture"],
        "Security": ["security", "cryptography", "encryption", "authentication"],
        "IoT/Embedded": ["iot", "embedded", "raspberry", "arduino", "sensor"],
        "Bioinformatics": ["bioinformatics", "genomics", "dna", "protein"],
        "HCI/UX": ["human computer", "user interface", "ux", "usability"],
    }
    
    detected_domains = []
    lower_text = raw_text.lower()
    
    for domain, keywords in research_domains.items():
        if any(keyword in lower_text for keyword in keywords):
            detected_domains.append(domain)
    
    return detected_domains


def _extract_publication_year_range(publications: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    """Extract earliest and latest publication years."""
    years = [pub.get("year") for pub in publications if pub.get("year")]
    if not years:
        return None, None
    return min(years), max(years)


def _calculate_publication_diversity(publications: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate diversity metrics of publications."""
    types = Counter(pub.get("pub_type", "unknown") for pub in publications)
    venues = Counter(pub.get("quality_note", "").split()[0] for pub in publications if pub.get("quality_note"))
    
    return {
        "type_distribution": dict(types),
        "unique_venue_count": len(venues),
        "most_common_type": types.most_common(1)[0][0] if types else None,
    }


async def analyze_research(raw_text: str) -> dict[str, Any]:
    """
    Complete research profile processing including:
    - Publication extraction and analysis
    - Co-author analysis
    - Research domain identification
    - Publication metrics and trends
    - Research quality assessment
    """
    publications = extract_publication_records(raw_text)
    
    journal_count = sum(1 for pub in publications if pub.get("pub_type") == "journal")
    conference_count = sum(1 for pub in publications if pub.get("pub_type") == "conference")
    other_count = len(publications) - journal_count - conference_count
    
    # Extract and analyze co-authors
    all_authors: list[str] = []
    for pub in publications:
        title = pub.get("title", "")
        authors = _extract_authors_from_line(title)
        pub["extracted_authors"] = authors
        all_authors.extend(authors)
    
    author_frequency = Counter(all_authors)
    unique_coauthors = len(author_frequency)
    most_frequent_coauthors = author_frequency.most_common(5)
    
    # Research domains
    research_domains = _extract_research_domains(raw_text)
    
    # Publication timeline
    earliest_year, latest_year = _extract_publication_year_range(publications)
    publication_span = (latest_year - earliest_year) if earliest_year and latest_year else None
    
    # Publication diversity
    diversity_metrics = _calculate_publication_diversity(publications)
    
    # Calculate research activity score (0-100)
    research_score = min(100, (
        (journal_count * 15) +  # Journals worth more
        (conference_count * 8) +  # Conferences worth less
        (other_count * 3) +  # Other publications
        (unique_coauthors * 2) +  # Collaboration diversity
        (len(research_domains) * 10)  # Domain diversity
    ))
    
    # Identify research productivity trend
    productivity_trend = "increasing" if publication_span and publication_span >= 3 else "stable" if publication_span else "new"
    
    # Co-author analysis
    coauthor_info = {
        "total_unique_coauthors": unique_coauthors,
        "most_frequent_collaborators": [
            {"name": name, "collaboration_count": count} 
            for name, count in most_frequent_coauthors
        ],
        "collaboration_diversity_score": min(100, unique_coauthors * 10),
        "average_coauthors_per_publication": round(len(all_authors) / len(publications), 2) if publications else 0,
    }
    
    return {
        "publications": publications,
        "coauthor_analysis": coauthor_info,
        "research_domains": research_domains,
        "summary": {
            "publications_count": len(publications),
            "journal_count": journal_count,
            "conference_count": conference_count,
            "other_count": other_count,
            "publication_span_years": publication_span,
            "earliest_publication_year": earliest_year,
            "latest_publication_year": latest_year,
            "productivity_trend": productivity_trend,
            "research_score": research_score,
            "is_partial_processing": False,  # Now complete!
        },
        "diversity_metrics": diversity_metrics,
        "research_profile_assessment": {
            "has_publications": len(publications) > 0,
            "publication_focus": diversity_metrics.get("most_common_type"),
            "research_domains": research_domains,
            "collaboration_level": "high" if unique_coauthors > 10 else "moderate" if unique_coauthors > 3 else "limited",
            "research_maturity": "established" if publication_span and publication_span >= 5 else "emerging" if publication_span else "not_yet_established",
        },
    }
