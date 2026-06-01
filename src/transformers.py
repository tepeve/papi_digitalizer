"""Utilities to expand macro ROI model outputs into atomic schema fields."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, Mapping


class MacroRoiTransformer:
    """Transform aggregated ROI outputs into schema-ready atomic fields.

    This transformer expands `multiple_choice_block` consolidated values (for
    example, "Madre, Amigos") into independent `Si`/`No` fields required by the
    final Pydantic contract.
    """

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

    def transform_aggregated_data(
        self,
        aggregated_data: Dict[str, Any],
        template_mapping: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize and expand macro ROI results into atomic schema fields.

        Args:
            aggregated_data: Flat dictionary with extracted values keyed by
                field_id (including macro block field_ids).
            template_mapping: Template JSON object containing `fields`.

        Returns:
            A new dictionary ready for schema validation, where macro ROI
            consolidated values are expanded into atomic destination fields.
        """
        transformed: Dict[str, Any] = dict(aggregated_data)
        fields = template_mapping.get("fields", [])
        if not isinstance(fields, list):
            return transformed

        for field in fields:
            if not isinstance(field, Mapping):
                continue

            field_type = str(field.get("type", "")).strip()
            field_id = field.get("field_id")
            if not isinstance(field_id, str) or not field_id:
                continue

            if field_type == "multiple_choice_block":
                self._expand_multiple_choice_block(transformed, field_id, field)
            elif field_type == "single_choice_block":
                self._normalize_single_choice_block(transformed, field_id, field)

        return transformed

    def _expand_multiple_choice_block(
        self,
        transformed: Dict[str, Any],
        block_field_id: str,
        field_config: Mapping[str, Any],
    ) -> None:
        if block_field_id not in transformed:
            return

        raw_value = transformed.get(block_field_id)
        target_mappings = field_config.get("target_mappings", {})
        if not isinstance(target_mappings, Mapping) or not target_mappings:
            transformed.pop(block_field_id, None)
            return

        # If no value (or explicit none marker), remove macro field and leave
        # existing atomic outputs untouched.
        if raw_value is None:
            transformed.pop(block_field_id, None)
            return

        normalized_response = self._normalize_text(str(raw_value))
        if normalized_response in self._NONE_MARKERS:
            transformed.pop(block_field_id, None)
            return

        # 1) Default every destination to "No" before matching selections.
        destination_fields = [dest for dest in target_mappings.values() if isinstance(dest, str) and dest]
        for destination in destination_fields:
            transformed[destination] = "No"

        response_tokens = self._tokenize_response(normalized_response)

        # 2) Partial matching by keyword across normalized response.
        for keyword, destination in target_mappings.items():
            if not isinstance(keyword, str) or not isinstance(destination, str):
                continue

            keyword_norm = self._normalize_text(keyword)
            if not keyword_norm:
                continue

            if self._is_keyword_selected(keyword_norm, normalized_response, response_tokens):
                transformed[destination] = "Si"

        # 3) Drop consolidated macro key to avoid contaminating the final payload.
        transformed.pop(block_field_id, None)

    def _normalize_single_choice_block(
        self,
        transformed: Dict[str, Any],
        field_id: str,
        field_config: Mapping[str, Any],
    ) -> None:
        if field_id not in transformed:
            return

        raw_value = transformed.get(field_id)
        if raw_value is None:
            return

        cleaned_value = str(raw_value).strip()
        if not cleaned_value:
            transformed[field_id] = ""
            return

        target_mappings = field_config.get("target_mappings", {})
        if not isinstance(target_mappings, Mapping) or not target_mappings:
            transformed[field_id] = cleaned_value
            return

        normalized_input = self._normalize_text(cleaned_value)

        # Prefer exact mapping label -> canonical value.
        for label, mapped_value in target_mappings.items():
            if not isinstance(label, str) or not isinstance(mapped_value, str):
                continue
            if self._normalize_text(label) == normalized_input:
                transformed[field_id] = mapped_value.strip()
                return

        # Fallback: if value already corresponds to a mapped value, keep canonical mapped value.
        for mapped_value in target_mappings.values():
            if not isinstance(mapped_value, str):
                continue
            if self._normalize_text(mapped_value) == normalized_input:
                transformed[field_id] = mapped_value.strip()
                return

        transformed[field_id] = cleaned_value

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = normalized.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def _tokenize_response(normalized_response: str) -> Iterable[str]:
        # Split common separators while preserving multi-word chunks.
        chunks = re.split(r"[,;|\n]", normalized_response)
        for chunk in chunks:
            token = chunk.strip()
            if token:
                yield token

    @staticmethod
    def _is_keyword_selected(
        keyword_norm: str,
        normalized_response: str,
        response_tokens: Iterable[str],
    ) -> bool:
        if keyword_norm in normalized_response:
            return True

        for token in response_tokens:
            if keyword_norm in token or token in keyword_norm:
                return True

        return False
