"""
Barcode normalization utilities

Handles various barcode formats:
- UPC-A: 12 digits (North America)
- EAN-13: 13 digits (International, includes UPC-A with leading 0)
- EAN-8: 8 digits (smaller products)
- UPC-E: 6 digits (compressed UPC-A)

The problem: Same product can appear as "722776004623" or "0722776004623"
Solution: Always store and search using multiple normalized forms
"""

from typing import List


def normalize_barcode(barcode: str) -> List[str]:
    """
    Generate all possible normalized forms of a barcode.

    This handles the common issue where:
    - UPC-A codes are 12 digits: "722776004623"
    - EAN-13 codes are 13 digits (UPC-A + leading 0): "0722776004623"
    - Some systems strip leading zeros, others don't

    Args:
        barcode: The barcode string (digits only)

    Returns:
        List of normalized barcode strings to check

    Examples:
        normalize_barcode("722776004623") -> ["722776004623", "0722776004623"]
        normalize_barcode("0722776004623") -> ["0722776004623", "722776004623"]
        normalize_barcode("000006105422") -> ["000006105422", "06105422", "0000006105422", "6105422"]
    """
    if not barcode or not barcode.isdigit():
        return [barcode]

    # Remove any existing leading zeros to get the base
    barcode_stripped = barcode.lstrip('0')

    # If all zeros, return as-is
    if not barcode_stripped:
        return [barcode]

    length = len(barcode)
    variants = []

    # Always include the original
    variants.append(barcode)

    # Always try the stripped version (no leading zeros)
    if barcode_stripped != barcode:
        variants.append(barcode_stripped)

    # Try common barcode lengths
    if length == 12:
        # UPC-A -> add EAN-13 version (with leading 0)
        variants.append('0' + barcode)
    elif length == 13:
        # EAN-13 -> add UPC-A version (strip leading 0 if present)
        if barcode[0] == '0':
            variants.append(barcode[1:])
    elif length == 8:
        # EAN-8 -> try padding to 12 and 13
        variants.append(barcode_stripped.zfill(12))
        variants.append(barcode_stripped.zfill(13))
    elif length < 8:
        # Very short -> try padding to 8, 12, and 13
        variants.append(barcode_stripped.zfill(8))
        variants.append(barcode_stripped.zfill(12))
        variants.append(barcode_stripped.zfill(13))
    elif 8 < length < 12:
        # 9-11 digits -> try padding to 12 and 13
        variants.append(barcode_stripped.zfill(12))
        variants.append(barcode_stripped.zfill(13))
    elif length > 13:
        # Too long -> strip extra leading zeros
        variants.append(barcode_stripped.zfill(13))
        variants.append(barcode_stripped.zfill(12))

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            result.append(v)

    return result


def get_primary_barcode(barcode: str) -> str:
    """
    Get the primary/canonical form of a barcode.

    We use EAN-13 (13 digits) as the canonical form since:
    - It's the international standard
    - It includes UPC-A codes (with leading 0)
    - Open Food Facts uses this format

    Args:
        barcode: The barcode string

    Returns:
        13-digit EAN-13 barcode (zero-padded if needed)
    """
    if not barcode or not barcode.isdigit():
        return barcode

    # Pad to 13 digits
    return barcode.zfill(13)
