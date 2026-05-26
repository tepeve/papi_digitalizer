"""Pipeline orchestration for multi-page PDF processing."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional
from .telemetry import profile_time

import cv2
import numpy as np
from pdf2image import convert_from_path

from .image_utils import align_page_orb, extract_rois
from .llm_engine import process_icr_batch, process_table_batch
from .transformers import MacroRoiTransformer

LOGGER = logging.getLogger(__name__)

_NONE_MARKERS = {
    "",
    "ninguna",
    "ninguno",
    "none",
    "null",
    "sin marca",
    "sin marcar",
    "sin opcion",
    "no marcada",
    "no marcado",
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _parse_multi_selection(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    normalized = _normalize_text(text)
    if normalized in _NONE_MARKERS:
        return []

    tokens = re.split(r"[,;\n|]", text)
    parsed = [token.strip() for token in tokens if token.strip()]
    return parsed or [text]


def _expand_multiple_choice_block(output: Dict[str, Any], field: Dict[str, Any]) -> bool:
    target_mappings = field.get("target_mappings")
    if not isinstance(target_mappings, dict) or not target_mappings:
        return False

    value = field.get("value")
    selected_tokens = _parse_multi_selection(value)

    normalized_labels = {
        _normalize_text(label): destination
        for label, destination in target_mappings.items()
    }

    selected_destinations: set[str] = set()
    for token in selected_tokens:
        token_norm = _normalize_text(token)
        destination = normalized_labels.get(token_norm)

        if destination is None:
            for label_norm, candidate in normalized_labels.items():
                if token_norm in label_norm or label_norm in token_norm:
                    destination = candidate
                    break

        if destination is not None:
            selected_destinations.add(destination)

    for destination in target_mappings.values():
        output[destination] = "Si" if destination in selected_destinations else "No"

    return True


def _expand_single_choice_block(output: Dict[str, Any], field: Dict[str, Any]) -> bool:
    target_mappings = field.get("target_mappings")
    if not isinstance(target_mappings, dict) or not target_mappings:
        return False

    value = field.get("value")
    if value is None:
        return True

    raw = str(value).strip()
    if not raw or _normalize_text(raw) in _NONE_MARKERS:
        return True

    normalized_key_map = {_normalize_text(key): mapped for key, mapped in target_mappings.items()}
    normalized_value_map = {_normalize_text(mapped): mapped for mapped in target_mappings.values()}
    resolved = normalized_key_map.get(_normalize_text(raw))
    if resolved is None:
        resolved = normalized_value_map.get(_normalize_text(raw))

    output[field["field_id"]] = resolved if resolved is not None else value
    return True


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
        value = field.get("value")
        field_type = field.get("type")

        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue

        if field_type == "multiple_choice_block" and _expand_multiple_choice_block(output, field):
            continue

        if field_type == "single_choice_block" and _expand_single_choice_block(output, field):
            continue

        # Keep aggregation flat: `group` is a UI concern and should not alter
        # the payload shape consumed by the Pydantic model.
        output[field_id] = value

    return output


@profile_time
def process_document(
    pdf_path: str,
    master_pages: List[np.ndarray],
    template_mapping: Dict[str, Any],
    forced_id: Optional[str] = None, # <-- 1. Agregar el parámetro
) -> Optional[Dict[str, Any]]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    # <-- 2. Usar el hash original si viene forzado, sino calcularlo
    document_id = forced_id if forced_id else _sha256_file(pdf_path)
    
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

            # Usamos el document_id (forzado o calculado) para los ROIs
            page_records = extract_rois(aligned_page, page_fields, document_id, page_number)
            if not page_records:
                LOGGER.warning("No ROIs extracted for page %d", page_number)
                continue

            omr_records = [record for record in page_records if record["type"] == "OMR"]
            icr_like_types = {
                "ICR",
                "text",
                "number",
                "date",
                "multiple_choice_block",
                "single_choice_block",
            }
            icr_records = [record for record in page_records if record["type"] in icr_like_types]
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
                        "target_mappings": record.get("target_mappings"),
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

    # Middleware injection: expand Macro-ROI consolidated outputs into
    # schema-atomic fields before the final Pydantic validation.
    transformer = MacroRoiTransformer()
    aggregated = transformer.transform_aggregated_data(aggregated, template_mapping)

    aggregated["document_id"] = document_id

    try:
        form_id = template_mapping.get("metadata", {}).get("form_id")
        if form_id == "DIAG_INTEGRAL":
            from .schemas import DiagnosticoIntegral

            validated = DiagnosticoIntegral.model_validate(aggregated)
        else:
            try:
                from .schemas import SneepCompleto
            except ImportError:
                from .schemas_old import SneepCompleto

            validated = SneepCompleto.model_validate(aggregated)

        return validated.model_dump()
    except Exception as exc:
        LOGGER.error("Pydantic validation failed: %s", exc)
        return {
            "document_id": document_id,
            "errors": str(exc),
            "data": aggregated,
        }