"""
chat_parser.py — Rule-based NLP parser for PGFinder chatbot.
Extracts structured search criteria from natural language user messages.
"""

import re

# ─── College aliases → canonical names ─────────────────────────────────────────
COLLEGE_ALIASES = {
    # Nirma University
    "nirma":           "Nirma University",
    "nirma university":"Nirma University",
    "nirma uni":       "Nirma University",

    # PDPU / PDEU
    "pdpu":            "PDPU",
    "pdeu":            "PDPU",
    "pdeu university": "PDPU",
    "pdpu university": "PDPU",
    "pandit deendayal":"PDPU",

    # Gujarat University
    "gujarat university":   "Gujarat University",
    "gujarat uni":          "Gujarat University",
    "gu":                   "Gujarat University",

    # CEPT University
    "cept":            "CEPT University",
    "cept university": "CEPT University",
    "cept uni":        "CEPT University",

    # Ahmedabad University
    "ahmedabad university": "Ahmedabad University",
    "ahmedabad uni":        "Ahmedabad University",
    "au":                   "Ahmedabad University",

    # LDRP Institute
    "ldrp":            "LDRP Institute",
    "ldrp institute":  "LDRP Institute",

    # ADIT College
    "adit":            "ADIT College",
    "adit college":    "ADIT College",

    # CVM University
    "cvm":             "CVM University",
    "cvm university":  "CVM University",
    "cvm uni":         "CVM University",

    # Anand Agricultural University
    "anand agricultural":     "Anand Agricultural Uni",
    "anand agricultural uni": "Anand Agricultural Uni",
    "aau":                    "Anand Agricultural Uni",
    "agricultural":           "Anand Agricultural Uni",

    # SRICT Institute
    "srict":           "SRICT Institute",
    "srict institute": "SRICT Institute",

    # Anand Engineering College
    "anand engineering":         "Anand Engineering College",
    "anand engineering college": "Anand Engineering College",
    "aec":                       "Anand Engineering College",
}

# ─── Amenity keywords ─────────────────────────────────────────────────────────
AMENITY_KEYWORDS = {
    "ac":        "AC",
    "a/c":       "AC",
    "a.c":       "AC",
    "a.c.":      "AC",
    "air conditioning": "AC",
    "air conditioner":  "AC",
    "wifi":      "wifi",
    "wi-fi":     "wifi",
    "wi fi":     "wifi",
    "internet":  "wifi",
    "food":      "food",
    "meals":     "food",
    "mess":      "food",
    "tiffin":    "food",
    "breakfast": "food",
    "lunch":     "food",
    "dinner":    "food",
    "laundry":   "laundry",
    "washing":   "laundry",
    "gym":       "gym",
    "gymnasium": "gym",
    "fitness":   "gym",
    "parking":   "parking",
    "bike parking":  "parking",
    "car parking":   "parking",
}

# ─── Room sharing keywords ─────────────────────────────────────────────────────
ROOM_SHARING_KEYWORDS = {
    "single":    "single",
    "single sharing":  "single",
    "1 sharing": "single",
    "one sharing": "single",
    "private":   "single",
    "double":    "double",
    "double sharing":  "double",
    "2 sharing": "double",
    "two sharing": "double",
    "twin":      "double",
    "triple":    "triple",
    "triple sharing":  "triple",
    "3 sharing": "triple",
    "three sharing": "triple",
}

# ─── Gender keywords ──────────────────────────────────────────────────────────
GENDER_KEYWORDS = {
    "boys":     "Boys",
    "boy":      "Boys",
    "male":     "Boys",
    "men":      "Boys",
    "man":      "Boys",
    "gents":    "Boys",
    "girls":    "Girls",
    "girl":     "Girls",
    "female":   "Girls",
    "women":    "Girls",
    "woman":    "Girls",
    "ladies":   "Girls",
    "unisex":   "Unisex",
    "coed":     "Unisex",
    "co-ed":    "Unisex",
    "mixed":    "Unisex",
    "any gender": "Unisex",
}


def parse(message: str) -> dict:
    """
    Parse a natural language message and extract structured PG search criteria.

    Returns:
        {
            "college":      str or None,
            "max_budget":   int or None,
            "room_sharing": str or None,   ("single", "double", "triple")
            "amenities":    list[str],
            "gender":       str or None     ("Boys", "Girls", "Unisex")
        }
    """
    text = message.strip()
    text_lower = text.lower()

    result = {
        "college":      _extract_college(text_lower),
        "max_budget":   _extract_budget(text_lower),
        "room_sharing": _extract_room_sharing(text_lower),
        "amenities":    _extract_amenities(text_lower),
        "gender":       _extract_gender(text_lower),
    }

    return result


def _extract_college(text: str) -> str | None:
    """Match college name from text using alias lookup (longest match first)."""
    # Sort aliases by length (longest first) to prefer specific matches
    sorted_aliases = sorted(COLLEGE_ALIASES.keys(), key=len, reverse=True)

    for alias in sorted_aliases:
        # Use word boundary matching for short aliases to avoid false positives
        if len(alias) <= 3:
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text):
                return COLLEGE_ALIASES[alias]
        else:
            if alias in text:
                return COLLEGE_ALIASES[alias]

    return None


def _extract_budget(text: str) -> int | None:
    """
    Extract maximum budget from text.
    Handles patterns like:
      - "under 9500", "below 10000", "max 8000"
      - "budget 7000", "rent 6000"
      - "under 10k", "below 8.5k"
      - "₹9500", "rs 9500", "9500 rs", "9500 rupees"
      - plain numbers like "budget is 7000"
    """
    # Pattern: number with optional k/K multiplier
    num_pattern = r'(\d+(?:\.\d+)?)\s*(?:k|K|thousand)?'

    # Try specific patterns first (more context = more confident)
    budget_patterns = [
        # "under/below/within/max/upto X"
        rf'(?:under|below|within|max|maximum|upto|up\s*to|less\s*than|not?\s*more\s*than|budget\s*(?:of|is)?|rent\s*(?:of|is)?)\s*(?:₹|rs\.?|inr|rupees?)?\s*{num_pattern}',
        # "X rs/rupees budget/rent/max"
        rf'{num_pattern}\s*(?:₹|rs\.?|inr|rupees?)\s*(?:budget|rent|max|maximum|per\s*month|monthly|/\s*(?:mo|month))?',
        # "₹X" or "rs X" standalone
        rf'(?:₹|rs\.?|inr)\s*{num_pattern}',
        # "budget/rent X"
        rf'(?:budget|rent)\s*(?:is|of|:)?\s*(?:₹|rs\.?|inr|rupees?)?\s*{num_pattern}',
        # Fallback: just "X rupees" or "X rs"
        rf'{num_pattern}\s*(?:rupees?|rs\.?)',
    ]

    for pattern in budget_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1) if match.lastindex >= 1 else None
            if num_str:
                value = float(num_str)
                # If "k" or "K" or "thousand" follows the number
                full_match = match.group(0).lower()
                if 'k' in full_match[full_match.find(num_str)+len(num_str):] or 'thousand' in full_match:
                    value *= 1000
                # Reasonable budget range: 1000–100000
                if 500 <= value <= 100000:
                    return int(value)

    # Last resort: look for any standalone large number that could be rent
    standalone = re.findall(r'\b(\d{4,5})\b', text)
    for num in standalone:
        val = int(num)
        if 2000 <= val <= 50000:
            return val

    return None


def _extract_room_sharing(text: str) -> str | None:
    """Extract room sharing type from text."""
    # Sort by length (longest first) to match "double sharing" before "double"
    sorted_keys = sorted(ROOM_SHARING_KEYWORDS.keys(), key=len, reverse=True)

    for keyword in sorted_keys:
        if keyword in text:
            return ROOM_SHARING_KEYWORDS[keyword]

    return None


def _extract_amenities(text: str) -> list:
    """Extract amenity keywords from text, returning unique normalized values."""
    found = set()

    # Sort by length (longest first) to match "air conditioning" before "air"
    sorted_keys = sorted(AMENITY_KEYWORDS.keys(), key=len, reverse=True)

    for keyword in sorted_keys:
        # Use word-boundary matching for short keywords
        if len(keyword) <= 3:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                found.add(AMENITY_KEYWORDS[keyword])
        else:
            if keyword in text:
                found.add(AMENITY_KEYWORDS[keyword])

    return sorted(list(found))


def _extract_gender(text: str) -> str | None:
    """Extract gender preference from text."""
    # Sort by length (longest first)
    sorted_keys = sorted(GENDER_KEYWORDS.keys(), key=len, reverse=True)

    for keyword in sorted_keys:
        # Word-boundary match to avoid partial hits
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            return GENDER_KEYWORDS[keyword]

    return None


# ─── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    test_cases = [
        "Hey! I am joining Nirma next month. Looking for a double sharing room with AC and wifi under 9500 rs",
        "need pg near ADIT college, budget 6000",
        "girls pg with food in anand under 8k",
        "double sharing near pdpu",
        "I'm a boy looking for triple sharing with AC, wifi and food near CVM, max rent 7000",
        "looking for pg near gujarat university below 10k with parking",
    ]

    for msg in test_cases:
        print(f"\nInput: \"{msg}\"")
        print(f"  => {parse(msg)}")
