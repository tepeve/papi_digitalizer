"""Generate template_mapping.json from src/schemas.py without runtime deps."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "src" / "schemas.py"
OUTPUT_PATH = PROJECT_ROOT / "template_mapping.json"

ROOT_METADATA = {
    "form_id": "DIAG_INTEGRAL",
    "reference_resolution": {"width": 1700, "height": 2200},
    "pages_count": 16,
}

NONE_MARKERS = {"none", "null", ""}

MULTIPLE_CHOICE_BLOCKS: Dict[str, Dict[str, Any]] = {
    "p16_s2_bloque": {
        "question": 16,
        "section": 2,
        "target_mappings": {
            "Con usted": "p16_s2_con_usted",
            "Con otro padre/madre": "p16_s2_otro_padre",
            "Con otro familiar 1": "p16_s2_otro_familiar_1",
            "Con otro familiar 2": "p16_s2_otro_familiar_2",
            "Solo/a": "p16_s2_solo",
            "Sin vinculo": "p16_s2_sin_vinculo",
            "Ns/Nc": "p16_s2_ns_nc",
        },
    },
    "p17_s2_bloque": {
        "question": 17,
        "section": 2,
        "target_mappings": {
            "Con otro padre/madre": "p17_s2_otro_padre",
            "Con otro familiar": "p17_s2_otro_familiar",
            "Con institucion": "p17_s2_institucion",
            "Solo/a": "p17_s2_solo",
            "Sin vinculo": "p17_s2_sin_vinculo",
            "Ns/Nc": "p17_s2_ns_nc",
        },
    },
    "p26_s3_bloque": {
        "question": 26,
        "section": 3,
        "target_mappings": {
            "Comisaria": "p26_s3_comisaria",
            "Alcaidia": "p26_s3_alcaidia",
            "Unidad penitenciaria": "p26_s3_unidad_penitenciaria",
            "Institucion de salud mental": "p26_s3_salud_mental",
            "Centro juvenil": "p26_s3_juvenil",
        },
    },
    "p45_s5_bloque": {
        "question": 45,
        "section": 5,
        "target_mappings": {
            "Actividad religiosa": "p45_s5_religiosa",
            "Deporte en equipo": "p45_s5_deporte_equipo",
            "Charlas": "p45_s5_charlas",
            "Talleres": "p45_s5_talleres",
            "Otras": "p45_s5_otras",
        },
    },
    "p47_s6_bloque": {
        "question": 47,
        "section": 6,
        "target_mappings": {
            "Comisaria": "p47_s6_comisaria",
            "Alcaidia": "p47_s6_alcaidia",
            "No": "p47_s6_no",
            "Ns/Nc": "p47_s6_ns_nc",
        },
    },
    "p74_s8_bloque": {
        "question": 74,
        "section": 8,
        "target_mappings": {
            "Conflicto con internos": "p74_s8_conflicto_internos",
            "Conflicto con policia": "p74_s8_conflicto_policia",
            "Sin conflicto": "p74_s8_sin_conflicto",
            "Ns/Nc": "p74_s8_ns_nc",
        },
    },
    "p83_s9_bloque": {
        "question": 83,
        "section": 9,
        "target_mappings": {
            "En pareja estable": "p83_s9_pareja",
            "Hijos/as": "p83_s9_hijos",
            "Madre": "p83_s9_madre",
            "Padre": "p83_s9_padre",
            "Hermanos/as": "p83_s9_hermanos",
            "Amigos/as": "p83_s9_amigos",
            "Vecinos/as": "p83_s9_vecinos",
            "Otro": "p83_s9_otro",
        },
    },
}

BLOCK_MEMBER_TO_BLOCK_ID = {
    target_field: block_id
    for block_id, block in MULTIPLE_CHOICE_BLOCKS.items()
    for target_field in block["target_mappings"].values()
}


def _parse_question_and_section(field_id: str) -> Optional[Tuple[int, int]]:
    match = re.match(r"^p(\d+)_s(\d+)_", field_id)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _extract_section_group(field_id: str) -> str:
    parsed = _parse_question_and_section(field_id)
    if parsed is None:
        return "DATOS DE LA ENCUESTA"
    return f"SECCIÓN {parsed[1]}"


def _field_sort_key(field_id: str) -> Tuple[int, int, int, str]:
    parsed = _parse_question_and_section(field_id)
    if parsed is None:
        special_order = {
            "id_encuesta": 0,
            "Fecha_encuesta": 1,
            "nombre_apellido_encuestador": 2,
        }
        return (0, 0, special_order.get(field_id, 1000), field_id)
    question, section = parsed
    return (1, question, section, field_id)


def _field_type_for_metadata(tipo_pregunta: str, data_type: str) -> str:
    if tipo_pregunta == "Cerrada - única":
        return "single_choice_block"
    if data_type == "date" or tipo_pregunta == "Fecha":
        return "date"
    if data_type in {"int", "float", "number"} or tipo_pregunta == "Numérica":
        return "number"
    return "text"


def _node_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return _node_name(node.slice)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant):
        return str(node.value) if isinstance(node.value, str) else None
    if isinstance(node, ast.Tuple):
        for elt in node.elts:
            candidate = _node_name(elt)
            if candidate and candidate != "None":
                return candidate
    if isinstance(node, ast.BinOp):
        # Python 3.10+ union syntax: A | None
        left = _node_name(node.left)
        if left and left != "None":
            return left
        right = _node_name(node.right)
        if right and right != "None":
            return right
    return None


def _string_constant(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_json_meta(field_call: ast.Call) -> Dict[str, str]:
    for keyword in field_call.keywords:
        if keyword.arg != "json_schema_extra":
            continue
        meta_call = keyword.value
        if not isinstance(meta_call, ast.Call):
            continue
        if not isinstance(meta_call.func, ast.Name) or meta_call.func.id != "meta":
            continue
        args = [_string_constant(arg) or "" for arg in meta_call.args[:3]]
        if len(args) == 3:
            return {
                "tipo_pregunta": args[0],
                "nivel_medicion": args[1],
                "data_type": args[2],
            }
    return {}


def _extract_enums(module_tree: ast.Module) -> Dict[str, List[str]]:
    enums: Dict[str, List[str]] = {}
    for node in module_tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {_node_name(base) for base in node.bases}
        if "Enum" not in base_names:
            continue

        values: List[str] = []
        for class_stmt in node.body:
            if not isinstance(class_stmt, ast.Assign):
                continue
            if len(class_stmt.targets) != 1 or not isinstance(class_stmt.targets[0], ast.Name):
                continue
            literal = _string_constant(class_stmt.value)
            if literal is not None and literal not in NONE_MARKERS:
                values.append(literal)

        enums[node.name] = values
    return enums


def _extract_model_fields(module_tree: ast.Module) -> List[Dict[str, Any]]:
    model_node: Optional[ast.ClassDef] = None
    for node in module_tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "DiagnosticoIntegral":
            model_node = node
            break

    if model_node is None:
        raise RuntimeError("Could not find class DiagnosticoIntegral in src/schemas.py")

    fields: List[Dict[str, Any]] = []
    for class_stmt in model_node.body:
        if not isinstance(class_stmt, ast.AnnAssign):
            continue
        if not isinstance(class_stmt.target, ast.Name):
            continue
        if not isinstance(class_stmt.value, ast.Call):
            continue
        if not isinstance(class_stmt.value.func, ast.Name) or class_stmt.value.func.id != "Field":
            continue

        field_name = class_stmt.target.id
        enum_name = _node_name(class_stmt.annotation)
        meta = _extract_json_meta(class_stmt.value)
        fields.append(
            {
                "field_name": field_name,
                "enum_name": enum_name,
                "meta": meta,
            }
        )
    return fields


def _build_multiple_choice_entry(block_id: str) -> Dict[str, Any]:
    block_cfg = MULTIPLE_CHOICE_BLOCKS[block_id]
    return {
        "field_id": block_id,
        "page": 1,
        "type": "multiple_choice_block",
        "group": f"SECCIÓN {block_cfg['section']}",
        "roi": [0, 0, 0, 0],
        "target_mappings": block_cfg["target_mappings"],
    }


def _single_choice_target_mappings(enum_values: List[str]) -> Optional[Dict[str, str]]:
    if not enum_values:
        return None
    mappings = {value: value for value in enum_values if value not in NONE_MARKERS}
    return mappings or None


def _build_fields(model_fields: List[Dict[str, Any]], enums: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    fields: List[Dict[str, Any]] = []
    emitted_blocks: set[str] = set()

    for field_data in model_fields:
        field_name = field_data["field_name"]
        block_id = BLOCK_MEMBER_TO_BLOCK_ID.get(field_name)
        if block_id is not None:
            if block_id not in emitted_blocks:
                fields.append(_build_multiple_choice_entry(block_id))
                emitted_blocks.add(block_id)
            continue

        meta = field_data["meta"]
        tipo_pregunta = str(meta.get("tipo_pregunta", "")).strip()
        data_type = str(meta.get("data_type", "")).strip()
        output_type = _field_type_for_metadata(tipo_pregunta, data_type)

        entry: Dict[str, Any] = {
            "field_id": field_name,
            "page": 1,
            "type": output_type,
            "group": _extract_section_group(field_name),
            "roi": [0, 0, 0, 0],
        }

        if output_type == "single_choice_block":
            enum_values = enums.get(field_data["enum_name"] or "", [])
            target_mappings = _single_choice_target_mappings(enum_values)
            if target_mappings:
                entry["target_mappings"] = target_mappings

        fields.append(entry)

    return sorted(fields, key=lambda item: _field_sort_key(item["field_id"]))


def _covered_schema_fields(fields: List[Dict[str, Any]]) -> set[str]:
    covered: set[str] = set()
    for field in fields:
        if field.get("type") == "multiple_choice_block":
            covered.update((field.get("target_mappings") or {}).values())
        else:
            covered.add(field["field_id"])
    return covered


def _validate_coverage(model_fields: List[Dict[str, Any]], fields: List[Dict[str, Any]]) -> None:
    schema_fields = {field["field_name"] for field in model_fields}
    covered = _covered_schema_fields(fields)

    missing = sorted(schema_fields - covered)
    extra = sorted(covered - schema_fields)
    if missing or extra:
        raise RuntimeError(
            "Coverage validation failed. "
            f"Missing fields: {missing or '[]'} | Extra fields: {extra or '[]'}"
        )


def generate_template_mapping() -> Dict[str, Any]:
    module_tree = ast.parse(SCHEMA_PATH.read_text(encoding="utf-8"), filename=str(SCHEMA_PATH))
    enums = _extract_enums(module_tree)
    model_fields = _extract_model_fields(module_tree)
    fields = _build_fields(model_fields, enums)
    _validate_coverage(model_fields, fields)

    return {
        "metadata": ROOT_METADATA,
        "fields": fields,
    }


def main() -> None:
    payload = generate_template_mapping()
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Generated {OUTPUT_PATH} with {len(payload['fields'])} fields")


if __name__ == "__main__":
    main()
