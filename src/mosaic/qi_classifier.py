from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    family: str
    confidence: float
    evidence: str


_FAMILY_PATTERNS = {
    "location": re.compile(r"(?:zip|postal|location|address|city|region|country)", re.I),
    "date_of_birth": re.compile(r"(?:date.?of.?birth|birth.?date|dob)", re.I),
    "demographic": re.compile(r"(?:gender|sex|race|ethnicity|marital|household|age)", re.I),
    "occupation": re.compile(r"(?:occupation|job.?title|employer|profession)", re.I),
    "health": re.compile(r"(?:diagnos|condition|medication|patient|health)", re.I),
    "financial": re.compile(r"(?:income|salary|account|credit|payment|financial)", re.I),
    "device": re.compile(r"(?:device|ip.?address|user.?agent|cookie|advertising.?id)", re.I),
    "temporal": re.compile(r"(?:timestamp|event.?time|created.?at|updated.?at|date)", re.I),
}


def _family(value: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    for family, pattern in _FAMILY_PATTERNS.items():
        if family == normalized or pattern.search(normalized):
            return family
    return None


def classify_column(
    name: str,
    data_type: str,
    *,
    glossary_terms: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
) -> Classification | None:
    """Classify a quasi-identifier using ranked, inspectable catalog evidence."""
    for term in glossary_terms:
        if family := _family(term):
            return Classification(family, 1.0, f"DataHub glossary term: {term}")
    for tag in tags:
        if family := _family(tag):
            return Classification(family, 0.9, f"DataHub tag: {tag}")
    if family := _family(name):
        typed = bool(re.search(r"(?:date|time|char|text|int|number)", data_type, re.I))
        if typed:
            return Classification(family, 0.75, f"schema type {data_type} + name pattern {name}")
        return Classification(family, 0.55, f"name pattern: {name}")
    return None
