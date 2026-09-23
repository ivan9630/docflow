"""Strict validation for synthetic demo inputs; no third-party dependencies."""
import math

def number(value, name, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name}: finite number >= {minimum} required")
    return value

def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: integer >= {minimum} required")
    return value

def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: non-empty text required")
    return value.strip()

def unique(rows, key):
    seen = set()
    for row in rows:
        value = text(row[key], key)
        if value in seen:
            raise ValueError(f"duplicate {key}: {value}")
        seen.add(value)
    return seen

