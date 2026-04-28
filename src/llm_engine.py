"""LLM engine for batch ICR inference using ROI crops."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Type
from .telemetry import profile_time


import cv2
import ollama
from ollama import Client 
from pydantic import BaseModel

from .schemas import (
    Cuadro1Dotacion,
    Cuadro8Suicidios,
    CuadroAlteraciones,
    CuadroEgresos,
    CuadroFallecidos,
    CuadroIngresos,
    CuadroLesiones,
    CuadroNinos,
    CuadroPoblacion,
)

LOGGER = logging.getLogger(__name__)

MODEL_NAME = "qwen2.5vl:7b"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
llm_client = Client(host=OLLAMA_HOST)

TABLE_MODEL_REGISTRY: Dict[str, Type[BaseModel]] = {
    "cuadro_1_dotacion": Cuadro1Dotacion,
    "cuadro_8_suicidios": Cuadro8Suicidios,
    "cuadro_poblacion": CuadroPoblacion,
    "cuadro_ingresos": CuadroIngresos,
    "cuadro_egresos": CuadroEgresos,
    "cuadro_ninos": CuadroNinos,
    "cuadro_alteraciones": CuadroAlteraciones,
    "cuadro_fallecidos": CuadroFallecidos,
    "cuadro_lesiones": CuadroLesiones,
}


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


def _build_table_skeleton(model_cls: Type[BaseModel]) -> Dict[str, Any]:
    instance = model_cls()
    return instance.model_dump()

@profile_time
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
        "Return raw JSON only, no markdown or code blocks.\n"
        "If a crop is empty or illegible, use null.\n"
        "Do not add extra keys or commentary.\n"
        f"JSON schema:\n{schema_json}"
    )

    response = llm_client.chat(
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


@profile_time
def process_table_batch(table_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run a single LLM call for a batch of TABLE_ICR crops."""
    if not table_records:
        return {}

    results: Dict[str, Any] = {}

    for record in table_records:
        field_id = record["field_id"]
        model_cls = TABLE_MODEL_REGISTRY.get(field_id)
        if model_cls is None:
            LOGGER.error("Missing TABLE_ICR model for field_id=%s", field_id)
            continue

        images = _encode_images([record])
        template_json = json.dumps({field_id: _build_table_skeleton(model_cls)}, ensure_ascii=False, indent=2)

        system_prompt = (
            "You are a data entry clerk. Extract numeric values from the table image crop.\n"
            "I am providing you with 1 table image.\n"
            f"Image 1 corresponds to table '{field_id}'.\n"
            "Return raw JSON only, no markdown or code blocks.\n"
            "Do not remove or rename keys. Do not add extra keys or commentary.\n"
            "If a cell is empty or unreadable, use 0. Use integers only.\n"
            f"JSON template:\n{template_json}"
        )


        response = llm_client.chat(
            model=MODEL_NAME,
            format="json",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Fill the table JSON using the provided image.",
                    "images": images,
                },
            ],
        )

        raw_json = response.get("message", {}).get("content", "")
        if not raw_json:
            LOGGER.error("Empty response from LLM")
            continue

        cleaned_json = _clean_json(raw_json)
        try:
            payload = json.loads(cleaned_json)
        except json.JSONDecodeError as exc:
            LOGGER.error("Invalid JSON from LLM: %s", exc)
            LOGGER.debug("Raw LLM response: %s", raw_json)
            continue

        if not isinstance(payload, dict):
            LOGGER.error("Invalid JSON payload type from LLM: %s", type(payload))
            LOGGER.debug("Raw LLM response: %s", raw_json)
            continue

        if field_id in payload:
            results[field_id] = payload[field_id]
        else:
            results[field_id] = payload

    return results
