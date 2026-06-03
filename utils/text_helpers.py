"""Text processing helper functions."""

import re
import pandas as pd
from typing import Optional


def extract_employer_base_name(employer_name: str) -> str:
    """
    Extract base organization name by removing legal forms and extra text.

    Args:
        employer_name: Raw employer name

    Returns:
        Cleaned base name
    """
    if not employer_name or pd.isna(employer_name):
        return ""

    name = str(employer_name)

    # Remove legal forms
    patterns = [
        (r'ООО\s*"?([^"]+)"?', r"\1"),
        (r'АО\s*"?([^"]+)"?', r"\1"),
        (r'ПАО\s*"?([^"]+)"?', r"\1"),
        (r"ИП\s*", ""),
        (r'МБОУ\s*"?([^"]+)"?', r"\1"),
        (r'МБДОУ\s*"?([^"]+)"?', r"\1"),
        (r'ОГБУЗ\s*"?([^"]+)"?', r"\1"),
    ]

    for pattern, repl in patterns:
        name = re.sub(pattern, repl, name)

    return name.strip('"').strip()


def extract_city_from_address(address: str) -> Optional[str]:
    """
    Extract city name from address string.

    Args:
        address: Full address string

    Returns:
        City name or None
    """
    if pd.isna(address):
        return None

    address_str = str(address)

    cities = [
        "Белгород",
        "Старый Оскол",
        "Губкин",
        "Шебекино",
        "Алексеевка",
        "Валуйки",
        "Новый Оскол",
        "Строитель",
        "Бирюч",
        "Грайворон",
        "Короча",
        "Ракитное",
        "Чернянка",
    ]

    # Direct match
    for city in cities:
        if re.search(r"\b" + re.escape(city) + r"\b", address_str, re.IGNORECASE):
            return city

    # Pattern match: "г. Белгород"
    match = re.search(
        r"г\.?\s*([А-Яа-яЁё][А-Яа-яЁё\s-]+?)(?:,|$| улица| проспект| переулок)",
        address_str,
    )
    if match:
        city = match.group(1).strip()
        for c in cities:
            if c.lower() == city.lower():
                return c
        if (
            2 < len(city) < 20
            and "область" not in city.lower()
            and "район" not in city.lower()
        ):
            return city

    return None


def match_names(name1: str, name2: str, threshold: float = 0.6) -> bool:
    """
    Check if two names match using partial containment.

    Args:
        name1: First name
        name2: Second name
        threshold: Not used (kept for API compatibility)

    Returns:
        True if names match
    """
    if pd.isna(name1) or pd.isna(name2):
        return False

    base1 = extract_employer_base_name(name1).lower()
    base2 = extract_employer_base_name(name2).lower()

    if not base1 or not base2:
        return False

    # Exact match
    if base1 == base2:
        return True

    # Partial match (longer contains shorter)
    if len(base1) > 3 and base1 in base2:
        return True
    if len(base2) > 3 and base2 in base1:
        return True

    return False
