#!/usr/bin/env python3
"""Interactive ROI labeling tool for template_mapping.json."""

import json
import os
from typing import Any, Dict, List

import cv2
import numpy as np
from pdf2image import convert_from_path

MASTER_PDF_PATH = "data/template/master_template.pdf"
OUTPUT_JSON_PATH = "template_mapping.json"

DEFAULT_TYPE = "ICR"
ROI_COLOR = (0, 200, 0)
ROI_THICKNESS = 2
DISPLAY_MAX_HEIGHT = 900


def _load_pdf_pages(pdf_path: str) -> List[Any]:
    pages = convert_from_path(pdf_path)
    # Note: If poppler is not in the system PATH, specify the path to the poppler binaries:
    # pages = convert_from_path(pdf_path, poppler_path=r"poppler\Library\bin")
    # if you have to running on Windows and installed poppler, you may need to adjust the poppler_path above to point to the correct location of the poppler binaries on your system. and the run:
    # uv run --with opencv-python --with pdf2image roi_labeler.py
    page_arrays = []
    for page in pages:
        page_array = np.array(page)
        page_arrays.append(cv2.cvtColor(page_array, cv2.COLOR_RGB2BGR))
    return page_arrays


def _prompt_field_metadata(page_number: int) -> Dict[str, Any]:
    field_id = input("field_id: ").strip()
    if not field_id:
        raise ValueError("field_id is required")

    field_type = input(f"type (default {DEFAULT_TYPE}): ").strip().upper() or DEFAULT_TYPE
    if field_type not in {"ICR", "OMR", "TABLE_ICR"}:
        raise ValueError("type must be ICR, OMR, or TABLE_ICR")

    group = input("group (optional, blank for null): ").strip()
    if group == "":
        group = None

    return {
        "field_id": field_id,
        "page": page_number,
        "type": field_type,
        "group": group,
    }


def _draw_rois(image, fields: List[Dict[str, Any]]) -> Any:
    canvas = image.copy()
    for field in fields:
        x, y, w, h = field["roi"]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), ROI_COLOR, ROI_THICKNESS)
    return canvas


def _init_output(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metadata": metadata,
        "fields": [],
    }


def main() -> None:
    if not os.path.exists(MASTER_PDF_PATH):
        raise FileNotFoundError(f"Master PDF not found: {MASTER_PDF_PATH}")

    pages = _load_pdf_pages(MASTER_PDF_PATH)
    if not pages:
        raise RuntimeError("No pages found in the master PDF")

    reference_resolution = {
        "width": int(pages[0].shape[1]),
        "height": int(pages[0].shape[0]),
    }

    metadata = {
        "form_id": "SNEEP_2",
        "reference_resolution": reference_resolution,
        "pages_count": len(pages),
    }

    output = _init_output(metadata)
    fields_by_page: Dict[int, List[Dict[str, Any]]] = {i + 1: [] for i in range(len(pages))}

    page_index = 0
    window_name = "SNEEP Labeler"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 900)

    print("Controls: n=next page, p=prev page, u=undo last ROI, q=quit/save")

    while True:
        page_number = page_index + 1
        page_image = pages[page_index]
        scale_factor = min(1.0, DISPLAY_MAX_HEIGHT / page_image.shape[0])
        annotated_full = _draw_rois(page_image, fields_by_page[page_number])

        if scale_factor < 1.0:
            new_width = int(page_image.shape[1] * scale_factor)
            new_height = int(page_image.shape[0] * scale_factor)
            display_img = cv2.resize(annotated_full, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            display_img = annotated_full

        cv2.imshow(window_name, display_img)
        key = cv2.waitKey(0) & 0xFF

        if key == ord("q"):
            break
        if key == ord("n"):
            page_index = min(page_index + 1, len(pages) - 1)
            continue
        if key == ord("p"):
            page_index = max(page_index - 1, 0)
            continue
        if key == ord("u"):
            if fields_by_page[page_number]:
                removed = fields_by_page[page_number].pop()
                output["fields"].remove(removed)
                print(f"Removed ROI for field_id={removed['field_id']} on page {page_number}")
            else:
                print("No ROIs to undo on this page")
            continue

        roi = cv2.selectROI(window_name, display_img, fromCenter=False, showCrosshair=True)
        x, y, w, h = [int(v) for v in roi]
        if w == 0 or h == 0:
            print("Skipped empty ROI")
            continue

        try:
            field = _prompt_field_metadata(page_number)
        except ValueError as exc:
            print(f"Invalid metadata: {exc}")
            continue

        inv_scale = 1.0 / scale_factor
        true_x = int(round(x * inv_scale))
        true_y = int(round(y * inv_scale))
        true_w = int(round(w * inv_scale))
        true_h = int(round(h * inv_scale))

        field["roi"] = [true_x, true_y, true_w, true_h]
        fields_by_page[page_number].append(field)
        output["fields"].append(field)
        print(f"Added ROI for field_id={field['field_id']} on page {page_number}")

    cv2.destroyAllWindows()

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)

    print(f"Saved template mapping to {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
