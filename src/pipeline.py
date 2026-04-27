"""Pipeline orchestration for multi-page PDF processing."""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from pdf2image import convert_from_path

from .image_utils import align_page_orb, extract_rois
from .llm_engine import process_icr_batch, process_table_batch
from .schemas import SneepCompleto

LOGGER = logging.getLogger(__name__)


def load_master_template(pdf_path: str) -> List[np.ndarray]:
    pages = convert_from_path(pdf_path)
    if not pages:
        raise RuntimeError(f"No pages found in master template: {pdf_path}")
    return [np.array(page) for page in pages]


def _sha256_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def aggregate_results(extracted_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    output: Dict[str, Any] = {}

    for field in extracted_fields:
        field_id = field["field_id"]
        group = field.get("group")
        value = field.get("value")

        if group is None:
            output[field_id] = value
        else:
            if group not in output:
                output[group] = {}
            output[group][field_id] = value

    return output


def process_document(
    pdf_path: str,
    master_pages: List[np.ndarray],
    template_mapping: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    document_id = _sha256_file(pdf_path)
    debug_mode = os.getenv("DEBUG_MODE", "").strip().lower() in {"1", "true", "yes"}
    debug_dir = os.path.join("data", "processed", document_id)

    scanned_pages = [np.array(page) for page in convert_from_path(pdf_path)]
    if len(scanned_pages) != len(master_pages):
        LOGGER.warning(
            "Page count mismatch (scanned=%d, master=%d)",
            len(scanned_pages),
            len(master_pages),
        )

    all_extracted_fields: List[Dict[str, Any]] = []

    for page_index, scanned_page in enumerate(scanned_pages):
        page_number = page_index + 1
        try:
            master_page = master_pages[page_index]

            page_fields = [
                field
                for field in template_mapping.get("fields", [])
                if field.get("page") == page_number
            ]
            if not page_fields:
                LOGGER.info("No fields for page %d", page_number)
                continue

            aligned_page = align_page_orb(
                scanned_page,
                master_page,
                debug_mode=debug_mode,
                debug_dir=debug_dir,
                debug_prefix=f"page_{page_number}_",
            )

            page_records = extract_rois(aligned_page, page_fields, document_id, page_number)
            if not page_records:
                LOGGER.warning("No ROIs extracted for page %d", page_number)
                continue

            omr_records = [record for record in page_records if record["type"] == "OMR"]
            icr_records = [record for record in page_records if record["type"] == "ICR"]
            table_records = [record for record in page_records if record["type"] == "TABLE_ICR"]

            all_extracted_fields.extend(omr_records)

            icr_results = process_icr_batch(icr_records)
            for record in icr_records:
                field_id = record["field_id"]
                value = icr_results.get(field_id)
                all_extracted_fields.append(
                    {
                        "document_id": document_id,
                        "page_number": page_number,
                        "field_id": field_id,
                        "group": record.get("group"),
                        "type": record.get("type"),
                        "value": value,
                    }
                )

            table_results = process_table_batch(table_records)
            for record in table_records:
                field_id = record["field_id"]
                value = table_results.get(field_id, {})
                all_extracted_fields.append(
                    {
                        "document_id": document_id,
                        "page_number": page_number,
                        "field_id": field_id,
                        "group": record.get("group"),
                        "type": record.get("type"),
                        "value": value,
                    }
                )
        except Exception as exc:
            LOGGER.exception("Failed processing page %d: %s", page_number, exc)
            continue

    aggregated = aggregate_results(all_extracted_fields)

    try:
        validated = SneepCompleto.model_validate(aggregated)
        return validated.model_dump()
    except Exception as exc:
        LOGGER.error("Pydantic validation failed: %s", exc)
        return {
            "document_id": document_id,
            "errors": str(exc),
            "data": aggregated,
        }
