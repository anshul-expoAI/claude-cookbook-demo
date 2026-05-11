from __future__ import annotations


class CodeCollisionError(Exception):
    """Raised when a generated short code already exists in the DB."""


class CodeGenerationExhausted(Exception):
    """Raised when the retry budget for code generation is exhausted."""
