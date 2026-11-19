"""Image quality assessment, validation, and defect-preserving preprocessing for edge industrial inspection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class QualityGateConfig:
    """Configurable thresholds for pre-inference quality validation."""
    enabled: bool = True
    min_width: int = 320
    min_height: int = 320
    blur_laplacian_threshold: float = 65.0
    min_mean_brightness: float = 35.0
    max_mean_brightness: float = 235.0
    max_glare_pixel_ratio: float = 0.12
    can_presence_threshold: float = 0.12


@dataclass
class QualityCheckResult:
    """Detailed result of pre-inference quality evaluation."""
    is_valid: bool
    passed_quality_gate: bool
    reasons: List[str] = field(default_factory=list)
    blur_score: float = 0.0
    mean_brightness: float = 0.0
    glare_ratio: float = 0.0
    contrast_score: float = 0.0
    width: int = 0
    height: int = 0
    color_channels: int = 0
    suggested_action: str = "PROCEED"  # "PROCEED", "REVIEW_POOR_QUALITY", "REJECT_CORRUPT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_laplacian_variance(gray: np.ndarray) -> float:
    """Computes Laplacian variance as a measure of sharpness/focus."""
    if gray.size == 0:
        return 0.0
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(laplacian.var())
    return round(variance, 2)


def compute_exposure_metrics(gray: np.ndarray) -> Tuple[float, float]:
    """Computes mean brightness and specular reflection/glare ratio.

    Metal cans easily produce intense specular highlights under improper illumination.
    """
    if gray.size == 0:
        return 0.0, 0.0
    mean_val = float(np.mean(gray))
    # Count pixels that are completely saturated (glare)
    glare_pixels = np.count_nonzero(gray >= 250)
    glare_ratio = float(glare_pixels / gray.size)
    return round(mean_val, 2), round(glare_ratio, 4)


def verify_can_presence(gray: np.ndarray, threshold: float = 0.12) -> Tuple[bool, float]:
    """Checks whether a can is present in the field of view versus an empty conveyor."""
    if gray.size == 0:
        return False, 0.0
    # Standard deviation of pixel intensities reflects scene contrast/texture
    norm_std = float(np.std(gray) / 255.0)
    return norm_std >= threshold, round(norm_std, 3)


def validate_image_quality(
    image: np.ndarray,
    config: Optional[QualityGateConfig] = None,
) -> QualityCheckResult:
    """Validates an incoming camera frame or uploaded image against industrial quality criteria.

    Fails safely: if an image is corrupt, blurry, or overexposed, marks for REVIEW/FAIL
    rather than allowing an undetected defect to pass downstream.
    """
    cfg = config or QualityGateConfig()

    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return QualityCheckResult(
            is_valid=False,
            passed_quality_gate=False,
            reasons=["IMAGE_CORRUPTED_OR_EMPTY"],
            suggested_action="REJECT_CORRUPT",
        )

    # Inspect dimensions
    if len(image.shape) == 2:
        h, w = image.shape
        c = 1
        gray = image
    elif len(image.shape) == 3:
        h, w, c = image.shape
        if c == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY if image.flags.c_contiguous else cv2.COLOR_RGBA2GRAY)
        elif c == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image[:, :, 0]
    else:
        return QualityCheckResult(
            is_valid=False,
            passed_quality_gate=False,
            reasons=["INVALID_DIMENSIONS"],
            suggested_action="REJECT_CORRUPT",
        )

    reasons: List[str] = []
    if h < cfg.min_height or w < cfg.min_width:
        reasons.append(f"RESOLUTION_TOO_LOW ({w}x{h} < {cfg.min_width}x{cfg.min_height})")

    if not cfg.enabled:
        return QualityCheckResult(
            is_valid=True,
            passed_quality_gate=True,
            reasons=[],
            width=w,
            height=h,
            color_channels=c,
            suggested_action="PROCEED",
        )

    blur_score = compute_laplacian_variance(gray)
    mean_brightness, glare_ratio = compute_exposure_metrics(gray)
    can_present, contrast_score = verify_can_presence(gray, cfg.can_presence_threshold)

    if blur_score < cfg.blur_laplacian_threshold:
        reasons.append(f"BLURRY_IMAGE (score={blur_score} < {cfg.blur_laplacian_threshold})")

    if mean_brightness < cfg.min_mean_brightness:
        reasons.append(f"UNDEREXPOSED_IMAGE (brightness={mean_brightness} < {cfg.min_mean_brightness})")
    elif mean_brightness > cfg.max_mean_brightness:
        reasons.append(f"OVEREXPOSED_IMAGE (brightness={mean_brightness} > {cfg.max_mean_brightness})")

    if glare_ratio > cfg.max_glare_pixel_ratio:
        reasons.append(f"EXCESSIVE_GLARE (ratio={glare_ratio:.2%} > {cfg.max_glare_pixel_ratio:.2%})")

    if not can_present:
        reasons.append(f"NO_CAN_IN_FIELD_OF_VIEW (contrast={contrast_score} < {cfg.can_presence_threshold})")

    passed = len(reasons) == 0
    suggested_action = "PROCEED" if passed else "REVIEW_POOR_QUALITY"

    return QualityCheckResult(
        is_valid=True,
        passed_quality_gate=passed,
        reasons=reasons,
        blur_score=blur_score,
        mean_brightness=mean_brightness,
        glare_ratio=glare_ratio,
        contrast_score=contrast_score,
        width=w,
        height=h,
        color_channels=c,
        suggested_action=suggested_action,
    )


def letterbox_preprocess(
    image: np.ndarray,
    target_shape: Tuple[int, int] = (320, 320),
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
    fill_color: int = 114,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Preserves aspect ratio using letterbox padding to prevent artificial can deformation.

    A circular or cylindrical can stretched non-uniformly would distort ovality and seam geometry.
    Returns:
        tensor: float32 array shaped (1, 3, target_h, target_w) normalized.
        transform_meta: scale, pad_x, pad_y for mapping boxes back to original coordinates.
    """
    if len(image.shape) == 2:
        img_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        img_rgb = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    else:
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    orig_h, orig_w = img_rgb.shape[:2]
    target_w, target_h = target_shape

    scale = min(target_w / orig_w, target_h / orig_h)
    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))

    # Bilinear resize
    resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Pad to target shape
    pad_x = (target_w - new_w) / 2.0
    pad_y = (target_h - new_h) / 2.0
    top = int(round(pad_y - 0.1))
    bottom = int(round(target_h - new_h - top))
    left = int(round(pad_x - 0.1))
    right = int(round(target_w - new_w - left))

    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=(fill_color, fill_color, fill_color)
    )

    # Normalize float32: (padded / 255 - mean) / std
    tensor = padded.astype(np.float32) / 255.0
    mean_arr = np.array(mean, dtype=np.float32)
    std_arr = np.array(std, dtype=np.float32)
    tensor = (tensor - mean_arr) / std_arr

    # Transpose to (1, 3, H, W)
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = np.expand_dims(tensor, axis=0)

    meta = {
        "orig_width": orig_w,
        "orig_height": orig_h,
        "target_width": target_w,
        "target_height": target_h,
        "scale": scale,
        "pad_left": left,
        "pad_top": top,
        "pad_right": right,
        "pad_bottom": bottom,
    }

    return tensor, meta


def unletterbox_bbox(
    box: Tuple[float, float, float, float],
    meta: Dict[str, Any],
) -> Tuple[int, int, int, int]:
    """Projects bounding box from letterbox coordinates back to original image coordinates."""
    x1, y1, x2, y2 = box
    pad_left = meta["pad_left"]
    pad_top = meta["pad_top"]
    scale = meta["scale"]
    orig_w = meta["orig_width"]
    orig_h = meta["orig_height"]

    orig_x1 = max(0, min(orig_w, int(round((x1 - pad_left) / scale))))
    orig_y1 = max(0, min(orig_h, int(round((y1 - pad_top) / scale))))
    orig_x2 = max(0, min(orig_w, int(round((x2 - pad_left) / scale))))
    orig_y2 = max(0, min(orig_h, int(round((y2 - pad_top) / scale))))

    return orig_x1, orig_y1, orig_x2, orig_y2
