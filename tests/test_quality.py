"""Unit tests for image quality gate and letterbox preprocessing."""

import numpy as np
import pytest
from edge_inspector.quality import (
    QualityGateConfig,
    letterbox_preprocess,
    unletterbox_bbox,
    validate_image_quality,
)


def test_quality_gate_valid_can_frame():
    # Synthetic frame with can-like contrast and adequate size
    img = np.full((480, 640, 3), 120, dtype=np.uint8)
    # Add high-contrast cylinder in center
    img[100:380, 200:440] = 200
    res = validate_image_quality(img)
    assert res.is_valid is True
    assert res.width == 640
    assert res.height == 480


def test_quality_gate_catches_blurry_image():
    # Completely uniform flat gray image has near zero Laplacian variance
    flat_img = np.full((480, 640, 3), 128, dtype=np.uint8)
    cfg = QualityGateConfig(blur_laplacian_threshold=50.0)
    res = validate_image_quality(flat_img, cfg)
    assert res.is_valid is True
    assert res.passed_quality_gate is False
    assert any("BLURRY" in r for r in res.reasons)
    assert res.suggested_action == "REVIEW_POOR_QUALITY"


def test_quality_gate_catches_corrupted_image():
    empty_arr = np.array([])
    res = validate_image_quality(empty_arr)
    assert res.is_valid is False
    assert res.passed_quality_gate is False
    assert res.suggested_action == "REJECT_CORRUPT"


def test_letterbox_preserves_dimensions_and_maps_bbox():
    img = np.full((480, 640, 3), 128, dtype=np.uint8)
    tensor, meta = letterbox_preprocess(img, target_shape=(320, 320))
    assert tensor.shape == (1, 3, 320, 320)
    assert meta["orig_width"] == 640
    assert meta["orig_height"] == 480

    # Test coordinate un-mapping
    letterbox_box = (meta["pad_left"], meta["pad_top"], 320 - meta["pad_right"], 320 - meta["pad_bottom"])
    orig_box = unletterbox_bbox(letterbox_box, meta)
    assert orig_box[0] >= 0
    assert orig_box[1] >= 0
    assert orig_box[2] <= 640
    assert orig_box[3] <= 480
