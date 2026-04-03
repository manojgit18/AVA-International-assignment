# backend/services/vendor_normalizer.py

import re

# Common suffixes to remove for normalization
SUFFIXES = [
    "ltd", "limited", "llc", "inc", "incorporated",
    "corp", "corporation", "co", "company", "pvt",
    "private", "plc", "group", "holdings", "enterprises",
    "solutions", "services", "technologies", "tech"
]

def normalize_vendor(name: str) -> str:
    """
    Normalizes vendor names for consistent grouping.

    Examples:
    "ACME CORP LTD."  → "Acme Corp"
    "acme corporation" → "Acme Corp"
    "VERTEX OFFICE SUPPLIES INC" → "Vertex Office Supplies"
    """
    if not name:
        return name

    # Step 1: lowercase
    normalized = name.lower().strip()

    # Step 2: remove punctuation except spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Step 3: remove common suffixes
    words = normalized.split()
    words = [w for w in words if w not in SUFFIXES]

    # Step 4: title case
    normalized = " ".join(words).title().strip()

    return normalized if normalized else name