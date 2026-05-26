"""Computer vision utilities for alignment and registration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple
from .telemetry import profile_time

import cv2
import numpy as np

LOGGER = logging.getLogger(__name__)

MAX_FEATURES = 5000
GOOD_MATCH_PERCENT = 0.15
RANSAC_REPROJ_THRESHOLD = 5.0


def _to_gray(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)


def _compute_keypoints(gray: np.ndarray) -> Tuple[list, np.ndarray]:
    orb = cv2.ORB_create(MAX_FEATURES)
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    return keypoints, descriptors

@profile_time
def align_page_orb(
    scanned_img: np.ndarray,
    master_img: np.ndarray,
    good_match_percent: float = GOOD_MATCH_PERCENT,
    debug_mode: bool = False,
    debug_dir: str = "",
    debug_prefix: str = "",
) -> np.ndarray:
    """Align a scanned page to the master template using ORB homography.

    Returns an RGB image aligned to the master template dimensions.
    """
    if scanned_img is None or master_img is None:
        raise ValueError("Input images must not be None")

    scanned_gray = _to_gray(scanned_img)
    master_gray = _to_gray(master_img)

    scanned_keypoints, scanned_desc = _compute_keypoints(scanned_gray)
    master_keypoints, master_desc = _compute_keypoints(master_gray)

    if scanned_desc is None or master_desc is None:
        LOGGER.error("ORB failed to compute descriptors")
        return cv2.cvtColor(scanned_img, cv2.COLOR_BGR2RGB)

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    matches = matcher.match(scanned_desc, master_desc)
    if len(matches) < 4:
        LOGGER.error("Not enough matches for homography: %d", len(matches))
        return cv2.cvtColor(scanned_img, cv2.COLOR_BGR2RGB)

    # FIX: Convertimos a lista para poder ordenar
    matches = list(matches)
    matches.sort(key=lambda match: match.distance)
    
    matches.sort(key=lambda match: match.distance)
    keep_ratio = min(max(good_match_percent, 0.01), 1.0)
    keep_count = max(4, int(len(matches) * keep_ratio))
    matches = matches[:keep_count]

    points_scanned = np.zeros((len(matches), 2), dtype=np.float32)
    points_master = np.zeros((len(matches), 2), dtype=np.float32)

    for idx, match in enumerate(matches):
        points_scanned[idx, :] = scanned_keypoints[match.queryIdx].pt
        points_master[idx, :] = master_keypoints[match.trainIdx].pt

    homography, mask = cv2.findHomography(
        points_scanned,
        points_master,
        cv2.RANSAC,
        RANSAC_REPROJ_THRESHOLD,
    )

    if homography is None:
        LOGGER.error("Homography computation failed")
        return cv2.cvtColor(scanned_img, cv2.COLOR_BGR2RGB)

    height, width = master_img.shape[:2]
    aligned_bgr = cv2.warpPerspective(scanned_img, homography, (width, height))

    if debug_mode:
        _ensure_dir(debug_dir)
        overlay = cv2.addWeighted(master_img, 0.5, aligned_bgr, 0.5, 0)
        overlay_name = f"{debug_prefix}alignment_overlay.jpg"
        overlay_path = os.path.join(debug_dir, overlay_name)
        cv2.imwrite(overlay_path, overlay)

        matches_img = cv2.drawMatches(
            scanned_img,
            scanned_keypoints,
            master_img,
            master_keypoints,
            matches,
            None,
        )
        matches_name = f"{debug_prefix}alignment_matches.jpg"
        matches_path = os.path.join(debug_dir, matches_name)
        cv2.imwrite(matches_path, matches_img)

    return cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB)


def evaluate_omr(roi_img: np.ndarray, threshold_ratio: float = 0.15) -> int:
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    white_pixels = cv2.countNonZero(binary)
    total_pixels = binary.size
    ratio = white_pixels / total_pixels if total_pixels else 0.0
    return 1 if ratio > threshold_ratio else 0

@profile_time
def extract_rois(
    aligned_page: np.ndarray,
    page_fields: List[Dict[str, Any]],
    document_id: str,
    page_number: int,
) -> List[Dict[str, Any]]:
    results = []

    for field in page_fields:
        x, y, w, h = field["roi"]
        height, width = aligned_page.shape[:2]
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(width, x + w)
        y_end = min(height, y + h)
        if x_end <= x_start or y_end <= y_start:
            LOGGER.warning("Skipping ROI outside bounds: %s", field.get("field_id"))
            continue
        crop = aligned_page[y_start:y_end, x_start:x_end]
        field_type = field.get("type", "ICR")

        if field_type == "OMR":
            if len(crop.shape) == 3:
                crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
            else:
                crop_bgr = crop
            value = evaluate_omr(crop_bgr)
            results.append(
                {
                    "document_id": document_id,
                    "page_number": page_number,
                    "field_id": field["field_id"],
                    "group": field.get("group"),
                    "type": field_type,
                    "target_mappings": field.get("target_mappings"),
                    "value": value,
                }
            )
        else:
            results.append(
                {
                    "document_id": document_id,
                    "page_number": page_number,
                    "field_id": field["field_id"],
                    "group": field.get("group"),
                    "type": field_type,
                    "target_mappings": field.get("target_mappings"),
                    "image_array": crop,
                }
            )

    return results
