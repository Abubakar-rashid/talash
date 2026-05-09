"""
Topic Clustering & Diversity Analysis (CS 417 Spec 3.6 & 3.7 Advanced)

Analyzes publication topic diversity and co-author collaboration patterns:
- Groups publications into thematic clusters
- Calculates topic diversity score
- Analyzes collaboration network density
- Identifies research breadth vs. depth

Returns quantitative metrics for research profile assessment.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any


def _calculate_entropy(distribution: list[float]) -> float:
    """Calculate Shannon entropy for a probability distribution."""
    entropy = 0.0
    for p in distribution:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _group_publications_by_domain(publications: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group publications by identified research domain."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    
    for pub in publications:
        domains = pub.get("research_domains", [])
        if domains:
            for domain in domains:
                grouped[domain].append(pub)
        else:
            # If no domain identified, group as 'Other'
            grouped["Other"].append(pub)
    
    return grouped


def _calculate_topic_diversity_score(grouped_pubs: dict[str, list[dict[str, Any]]]) -> float:
    """
    Calculate topic diversity score (0-100).
    
    Based on Shannon entropy of publication distribution across domains.
    - Score ~0: All papers in one domain (highly focused)
    - Score ~100: Papers evenly distributed across many domains (highly interdisciplinary)
    """
    total_pubs = sum(len(pubs) for pubs in grouped_pubs.values())
    if total_pubs == 0:
        return 0.0
    
    # Calculate probability distribution
    distribution = [len(pubs) / total_pubs for pubs in grouped_pubs.values()]
    
    # Calculate entropy (0 = low diversity, log2(num_domains) = max diversity)
    entropy = _calculate_entropy(distribution)
    max_entropy = math.log2(len(grouped_pubs)) if len(grouped_pubs) > 1 else 1.0
    
    # Normalize to 0-100 scale
    diversity_score = (entropy / max_entropy * 100) if max_entropy > 0 else 0.0
    return round(diversity_score, 1)


def _build_coauthor_network(publications: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build collaboration network from co-authorship data.
    
    Returns network statistics: size, density, collaboration patterns.
    """
    coauthor_graph: dict[str, set[str]] = defaultdict(set)
    collaboration_strength: dict[tuple[str, str], int] = Counter()
    
    for pub in publications:
        authors = pub.get("authors", [])
        
        # Build edges between all author pairs (co-authorship)
        for i, author1 in enumerate(authors):
            for author2 in authors[i + 1 :]:
                # Normalize author representation
                a1, a2 = (author1.lower(), author2.lower())
                if a1 != a2:
                    coauthor_graph[a1].add(a2)
                    coauthor_graph[a2].add(a1)
                    # Track collaboration strength (number of joint papers)
                    key = tuple(sorted([a1, a2]))
                    collaboration_strength[key] += 1
    
    # Calculate network metrics
    num_nodes = len(coauthor_graph)
    
    if num_nodes <= 1:
        return {
            "network_size": num_nodes,
            "network_density": 0.0,
            "avg_degree": 0.0,
            "collaboration_patterns": "minimal",
            "unique_collaborators": 0,
            "strong_collaborations": [],
        }
    
    # Calculate edges
    num_edges = sum(len(neighbors) for neighbors in coauthor_graph.values()) / 2
    
    # Calculate density: actual_edges / possible_edges
    possible_edges = num_nodes * (num_nodes - 1) / 2
    density = (num_edges / possible_edges) if possible_edges > 0 else 0.0
    
    # Average degree
    avg_degree = 2 * num_edges / num_nodes if num_nodes > 0 else 0.0
    
    # Identify strong collaborations (3+ joint papers)
    strong_collabs = [
        {
            "collaborators": list(collab),
            "joint_papers": count,
        }
        for collab, count in collaboration_strength.items()
        if count >= 3
    ]
    
    # Determine collaboration pattern
    if density > 0.3:
        pattern = "tightly_knit_group"
    elif density > 0.1:
        pattern = "moderate_collaboration"
    elif avg_degree > 2:
        pattern = "distributed_network"
    else:
        pattern = "mostly_independent"
    
    return {
        "network_size": num_nodes,
        "network_density": round(density, 3),
        "avg_degree": round(avg_degree, 2),
        "collaboration_patterns": pattern,
        "unique_collaborators": num_nodes,
        "strong_collaborations": strong_collabs[:10],  # Top 10
    }


def _identify_collaboration_types(publications: list[dict[str, Any]]) -> dict[str, int]:
    """Categorize collaborations by type (internal, external, interdisciplinary, etc.)."""
    collaboration_types = Counter()
    
    for pub in publications:
        authors = pub.get("authors", [])
        num_authors = len(authors)
        
        # Categorize by team size
        if num_authors == 1:
            collaboration_types["solo_authored"] += 1
        elif num_authors == 2:
            collaboration_types["pairwise_collaboration"] += 1
        elif num_authors <= 5:
            collaboration_types["small_team"] += 1
        else:
            collaboration_types["large_team"] += 1
    
    return dict(collaboration_types)


def analyze_research_diversity(publications: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Comprehensive research diversity analysis.
    
    Includes topic variability, co-author patterns, and collaboration metrics.
    """
    if not publications:
        return {
            "total_publications": 0,
            "topic_diversity_score": 0,
            "topic_focus_interpretation": "no_publications",
            "domains_covered": [],
            "coauthor_network": {
                "network_size": 0,
                "network_density": 0.0,
                "unique_collaborators": 0,
                "collaboration_patterns": "no_data",
            },
            "collaboration_types": {},
            "research_profile_assessment": "Insufficient publication data for diversity analysis.",
        }
    
    # Analyze topic distribution
    grouped_pubs = _group_publications_by_domain(publications)
    diversity_score = _calculate_topic_diversity_score(grouped_pubs)
    
    # Categorize diversity
    if diversity_score >= 70:
        diversity_interpretation = "highly_interdisciplinary"
        assessment = (
            "Research spans multiple diverse domains, indicating broad expertise and adaptability "
            "across different research areas."
        )
    elif diversity_score >= 50:
        diversity_interpretation = "moderately_diverse"
        assessment = (
            "Research covers several related and some distinct domains, showing balanced depth and breadth."
        )
    elif diversity_score >= 30:
        diversity_interpretation = "focused_with_extensions"
        assessment = (
            "Primary research focus on one main domain with occasional publications in adjacent areas."
        )
    else:
        diversity_interpretation = "highly_specialized"
        assessment = "Research is highly specialized and focused in one narrow domain."
    
    # Analyze co-author network
    coauthor_network = _build_coauthor_network(publications)
    
    # Analyze collaboration types
    collab_types = _identify_collaboration_types(publications)
    
    # Determine if research shows depth or breadth
    avg_pubs_per_domain = len(publications) / len(grouped_pubs) if grouped_pubs else 0
    if len(grouped_pubs) == 1 and avg_pubs_per_domain > 5:
        focus_type = "deep_specialist"
    elif len(grouped_pubs) >= 5 and avg_pubs_per_domain < 3:
        focus_type = "broad_interdisciplinary"
    else:
        focus_type = "balanced"
    
    return {
        "total_publications": len(publications),
        "topic_diversity_score": diversity_score,
        "topic_focus_interpretation": diversity_interpretation,
        "focus_type": focus_type,
        "domains_covered": list(grouped_pubs.keys()),
        "domain_distribution": {
            domain: {
                "count": len(pubs),
                "percentage": round(len(pubs) / len(publications) * 100, 1),
            }
            for domain, pubs in grouped_pubs.items()
        },
        "coauthor_network": coauthor_network,
        "collaboration_types": collab_types,
        "research_profile_assessment": assessment,
        "top_collaboration_area": (
            max(grouped_pubs.keys(), key=lambda k: len(grouped_pubs[k]))
            if grouped_pubs
            else "None"
        ),
    }
