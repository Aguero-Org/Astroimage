import pytest

from astroimage.hub.candidate_token import (
    InvalidCandidateTokenError,
    read_candidate_token,
    sign_candidate_token,
)
from astroimage.hub.progress import moving_average_bytes_per_second, progress_ratio


def test_signed_token_roundtrip() -> None:
    payload = {"data_uri": "mast:HST/product/a.fits", "product_filename": "a.fits"}
    token = sign_candidate_token(payload, "secret")
    assert read_candidate_token(token, "secret")["data_uri"] == payload["data_uri"]


def test_signed_token_rejects_tampering() -> None:
    token = sign_candidate_token({"data_uri": "mast:HST/product/a.fits"}, "secret")
    with pytest.raises(InvalidCandidateTokenError):
        read_candidate_token(token + "x", "secret")


def test_progress_is_ratio_when_total_is_known() -> None:
    assert progress_ratio(25, 100) == 0.25
    assert progress_ratio(10, None) is None


def test_speed_uses_a_window_not_a_single_chunk() -> None:
    samples = [(0.0, 0), (1.0, 100), (2.0, 300), (6.0, 300)]
    speed = moving_average_bytes_per_second(samples, now=6.0, window_seconds=5.0)
    assert speed == 40.0
