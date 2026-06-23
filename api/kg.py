"""Wraps the vendored W9B deterministic NL→Cypher mapper.

The mapper itself is vendored under `w9b_mapper/` and must not be
modified. This module provides the thin function the path operation
calls.
"""
from .w9b_mapper.mapper import map_question
from .w9b_mapper.errors import UnsupportedQueryError  # re-export

# Fallback pattern list surfaced in the 422 detail body when the raised
# UnsupportedQueryError instance does not itself carry a
# `supported_patterns` (or `patterns`) attribute. Keep this in sync with
# the shapes documented in the W9B mapper's reading/spec.
SUPPORTED_PATTERNS = [
    "Find recipes by ingredient",
    "Find recipes by cuisine",
    "Find recipes by technique",
    "Find ingredients used in a recipe",
    "Find techniques used in a recipe",
]


def wrap_kg_query(question: str):
    """Map a natural-language question to (cypher, params).

    Inputs:
        question — natural-language question (non-empty, <= 500 chars).
    Returns:
        Tuple (cypher: str, params: dict) suitable for `session.run`.
    Raises:
        UnsupportedQueryError — if the question does not match any
        supported pattern. The path operation converts this to 422.
    """
    return map_question(question)