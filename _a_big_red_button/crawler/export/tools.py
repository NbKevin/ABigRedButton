"""
This module includes useful utilities that make the export
process easier.

Kevin Ni, kevin.ni@nyu.edu.
"""


def is_same_author(a: str, b: str):
    a, b = a.upper(), b.upper()
    a, b = a.strip(), b.strip()
    a, b = a.replace('.', ''), b.replace('.', '')
    return a == b


def normalize_name(a: str):
    return a.upper().strip().replace('.', '').replace(',', '')
