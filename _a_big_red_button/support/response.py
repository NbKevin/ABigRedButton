"""
Shorthands for creating JSON response wrappers.

Kevin Ni, kevin.ni@nyu.edu.
"""

from flask import jsonify


def good(**kwargs):
    return jsonify(good=True, result=kwargs)


def bad(reason: str, **kwargs):
    return jsonify(good=False, reason=reason, result=kwargs)
