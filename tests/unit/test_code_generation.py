from __future__ import annotations

import pytest

BASE62 = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
SAMPLES = 10_000


@pytest.mark.unit
def test_generated_codes_are_base62():
    from app.services.shortener import _generate_code
    for _ in range(100):
        code = _generate_code(5)
        assert all(c in BASE62 for c in code), f"Non-base62 char in {code!r}"


@pytest.mark.unit
def test_generated_codes_have_correct_length():
    from app.services.shortener import _generate_code
    for length in (5, 6):
        for _ in range(50):
            code = _generate_code(length)
            assert len(code) == length


@pytest.mark.unit
def test_generated_codes_distribution_sanity():
    """Each base62 character should appear at least once in 10k 5-char codes."""
    from app.services.shortener import _generate_code
    seen = set()
    for _ in range(SAMPLES):
        seen.update(_generate_code(5))
    # With 10k*5=50k draws over 62 chars, P(any char unseen) is negligible
    assert len(seen) == 62, f"Only {len(seen)}/62 chars seen in {SAMPLES} samples"


@pytest.mark.unit
def test_generated_codes_are_not_sequential():
    """Consecutive codes should differ — sanity check against sequential IDs."""
    from app.services.shortener import _generate_code
    codes = [_generate_code(5) for _ in range(20)]
    assert len(set(codes)) > 1, "All codes were identical — CSPRNG broken?"
