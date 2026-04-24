"""LLM engine for batch ICR inference using ROI crops."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import cv2
import ollama

LOGGER = logging.getLogger(__name__)

MODEL_NAME = "qwen2.5vl:7b"


def _clean_json(raw_json: str) -> str:
    if "```json" in raw_json:
        return raw_json.split("```json")[1].split("```")[0].strip()
    if "```" in raw_json:
        return raw_json.split("```")[1].strip()
    return raw_json.strip()


def _encode_images(icr_records: List[Dict[str, Any]]) -> List[bytes]:
    images = []
    for record in icr_records:
        image = record["image_array"]
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode(".jpg", image_bgr)
        if not success:
            raise ValueError("Failed to encode ROI image")
        images.append(buffer.tobytes())
    return images


def _build_schema(field_ids: List[str]) -> Dict[str, Any]:
    return {field_id: None for field_id in field_ids}


def process_icr_batch(icr_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run a single LLM call for a batch of ICR crops.

    Returns a dictionary mapping field_id to extracted string values (or null).
    """
    if not icr_records:
        return {}

    field_ids = [record["field_id"] for record in icr_records]
    images = _encode_images(icr_records)
    schema = _build_schema(field_ids)
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    index_lines = [
        f"Image {idx + 1} corresponds to '{field_id}'."
        for idx, field_id in enumerate(field_ids)
    ]
    index_map = "\n".join(index_lines)

    system_prompt = (
        "You are a data entry clerk. Transcribe handwritten text from each image crop.\n"
        f"I am providing you with {len(field_ids)} image crops.\n"
        f"{index_map}\n"
        "Return ONLY a JSON object with the provided keys.\n"
        "If a crop is empty or illegible, use null.\n"
        "Do not add extra keys or commentary.\n"
        f"JSON schema:\n{schema_json}"
    )

    response = ollama.chat(
        model=MODEL_NAME,
        format="json",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Transcribe each image crop into the corresponding JSON field.",
                "images": images,
            },
        ],
    )

    raw_json = response.get("message", {}).get("content", "")
    if not raw_json:
        LOGGER.error("Empty response from LLM")
        return {}

    cleaned_json = _clean_json(raw_json)
    try:
        return json.loads(cleaned_json)
    except json.JSONDecodeError as exc:
        LOGGER.error("Invalid JSON from LLM: %s", exc)
        LOGGER.debug("Raw LLM response: %s", raw_json)
        return {}
