# REPOSITORIO: papi_digitalizer

## Archivos Raíz

# ==========================================
# FILE: pyproject.toml
# ==========================================
```python
[project]
name = "papi-digitalizer-qwen"
version = "0.1.0"
description = "Pipeline de digitalización de encuestas PAPI usando Qwen2.5-VL y procesamiento local"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    { name = "Tomás Pont Verges" }
]
dependencies = [
    "ollama>=0.1.0",           # Cliente para hablar con el servidor de Qwen
    "opencv-python>=4.8.0",    # Procesamiento de imágenes (limpieza, rotación)
    "pymupdf4llm>=0.0.17",     # Extracción de estructura de PDFs a Markdown
    "pandas>=2.1.0",           # Manejo de matrices y tablas
    "sqlalchemy>=2.0.0",       # ORM para carga en RDBMS
    "pydantic>=2.5.0",         # Validación de los JSON que devuelva la IA
    "pillow>=10.0.0",          # Manipulación básica de imágenes
    "pdf2image>=1.16.3",       # Conversión de PDF a imágenes para el modelo VL
    "tqdm>=4.66.0",            # Barras de progreso para tus 20 núcleos
    "python-dotenv>=1.0.0",    # Manejo de variables de entorno (credenciales DB)
    "img2pdf",                 # Convierte imágenes a PDF manteniendo la integridad de los píxeles (sin re-compresión)
]

[tool.uv]
[dependency-groups]
dev = [
    "ipykernel>=6.25.0",
    "matplotlib>=3.8.0",
    "pytest>=7.4.0",
    "black>=26.3.1",
]
```

# ==========================================
# FILE: README.md
# ==========================================
```python
# PAPI Digitalizer (Qwen2.5-VL)

Pipeline para digitalizar encuestas PAPI (SNEEP) con OCR + vision LLM.

## Requisitos del sistema
- ocrmypdf
- tesseract-ocr-spa
- ghostscript
- unpaper
- poppler-utils

Ejemplo (Ubuntu):
sudo apt update
sudo apt install ocrmypdf tesseract-ocr-spa ghostscript unpaper poppler-utils -y

## Instalacion
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

## Uso rapido
- Notebook: src/prototype_1.ipynb
- Script: main.py

## Notas
- El pipeline usa OCRmyPDF + PyMuPDF4LLM + Qwen2.5-VL via Ollama.
```

## Carpeta: src/

# ==========================================
# FILE: src/batch_processor.py
# ==========================================
```python
import json
import os
import shutil
import traceback
from typing import Dict, List, Optional

from tqdm import tqdm

from .database import persist_results
from .pipeline import load_master_template, process_document

SUPPORTED_EXTENSIONS = {".pdf"}


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _iter_document_files(input_dir: str) -> List[str]:
    files: List[str] = []
    for name in os.listdir(input_dir):
        full_path = os.path.join(input_dir, name)
        if not os.path.isfile(full_path):
            continue
        _, ext = os.path.splitext(name)
        if ext.lower() in SUPPORTED_EXTENSIONS:
            files.append(full_path)
    return sorted(files)


def _quarantine_file(pdf_path: str, error_text: str, payload: Optional[Dict[str, object]] = None) -> None:
    quarantine_dir = os.path.join("data", "quarantine")
    _ensure_dir(quarantine_dir)

    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    dest_path = os.path.join(quarantine_dir, os.path.basename(pdf_path))
    error_path = os.path.join(quarantine_dir, f"{stem}_error.txt")
    data_path = os.path.join(quarantine_dir, f"{stem}_data.json")

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(os.path.basename(pdf_path))
        dest_path = os.path.join(quarantine_dir, f"{base}_dup{ext}")

    shutil.move(pdf_path, dest_path)

    with open(error_path, "w", encoding="utf-8") as handle:
        handle.write(error_text)

    if payload is not None:
        with open(data_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


def process_batch(
    input_dir: str,
    master_pdf_path: str,
    template_mapping: Dict[str, object],
) -> Optional[Dict[str, object]]:
    files = _iter_document_files(input_dir)
    if not files:
        print(f"No se encontraron PDFs en {input_dir}.")
        return None

    master_pages = load_master_template(master_pdf_path)

    results: List[dict] = []
    success_count = 0
    quarantine_count = 0

    for pdf_path in tqdm(files, desc="Procesando", unit="pdf"):
        try:
            data = process_document(pdf_path, master_pages, template_mapping)
            if data is None:
                quarantine_count += 1
                _quarantine_file(pdf_path, "Pipeline devolvio None.\n")
                continue

            if "errors" in data:
                quarantine_count += 1
                error_text = f"Pydantic validation failed: {data.get('errors', '')}\n"
                _quarantine_file(pdf_path, error_text, payload=data.get("data"))
                continue

            results.append(data)
            success_count += 1
        except Exception:
            quarantine_count += 1
            error_text = traceback.format_exc()
            _quarantine_file(pdf_path, error_text)
            continue

    if results:
        persist_results(results)

    return {
        "total": len(files),
        "success": success_count,
        "quarantine": quarantine_count,
        "results": results,
    }

```

# ==========================================
# FILE: src/preprocessor.py
# ==========================================
```python
import os
import stat
import subprocess
from typing import Optional

from PIL import Image


def limpiar_y_enderezar(ruta_imagen: str, output_dir: str) -> Optional[str]:
    print("1. Preparando imagen y ejecutando OCRmyPDF...")
    os.makedirs(output_dir, exist_ok=True)

    # --- INICIO DEL PREPROCESAMIENTO (Normalizacion de Transparencias/PNG) ---
    img_segura = os.path.join(output_dir, "input_seguro.jpg")
    img = Image.open(ruta_imagen)

    # Chequeamos si la imagen tiene canal alfa (RGBA, LA) o paleta con transparencia
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        print("   [!] Canal alfa detectado. Normalizando a RGB puro con fondo blanco...")
        # Creamos un lienzo blanco del mismo tamano
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        # Pegamos la imagen original usando su propio canal de transparencia como mascara
        if img.mode == "RGBA":
            fondo.paste(img, mask=img.split()[3])
        else:
            fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])

        fondo.save(img_segura, "JPEG", quality=100)
        ruta_imagen = img_segura  # OCRmyPDF ahora usara esta version segura

    elif img.mode != "RGB" or ruta_imagen.lower().endswith(".png"):
        print("   [!] Normalizando formato de imagen a JPG estandar...")
        img.convert("RGB").save(img_segura, "JPEG", quality=100)
        ruta_imagen = img_segura
    # --- FIN DEL PREPROCESAMIENTO ---

    # --- INICIO DEL HACK: Crear un 'jbig2' falso ---
    fake_jbig2_path = os.path.join(output_dir, "jbig2")
    with open(fake_jbig2_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\n")
        f.write("echo 'jbig2enc 0.29'\n")

    os.chmod(fake_jbig2_path, os.stat(fake_jbig2_path).st_mode | stat.S_IEXEC)

    my_env = os.environ.copy()
    my_env["PATH"] = os.path.abspath(output_dir) + os.pathsep + my_env.get("PATH", "")
    # --- FIN DEL HACK ---

    output_pdf_path = os.path.join(output_dir, "limpio.pdf")
    comando = [
        "ocrmypdf",
        "--image-dpi",
        "300",
        "--optimize",
        "0",
        "--deskew",
        "--clean",
        "--force-ocr",
        "--language",
        "spa",
        ruta_imagen,  # <-- Ahora pasamos la imagen normalizada
        output_pdf_path,
    ]

    try:
        subprocess.run(comando, env=my_env, capture_output=True, text=True, check=True)
        print("✅ PDF limpio y enderezado con exito.")
        return output_pdf_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en OCRmyPDF (Codigo {e.returncode}):")
        print(f"--- DETALLE DEL ERROR ---\n{e.stderr}")
        return None

```

# ==========================================
# FILE: src/pipeline.py
# ==========================================
```python
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

```

# ==========================================
# FILE: src/llm_engine.py
# ==========================================
```python
"""LLM engine for batch ICR inference using ROI crops."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Type

import cv2
import ollama
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

        response = ollama.chat(
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

        if field_id in payload:
            results[field_id] = payload[field_id]
        else:
            results[field_id] = payload

    return results

```

# ==========================================
# FILE: src/schemas.py
# ==========================================
```python
import unicodedata
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# ==========================================
# 1. CLASES REUTILIZABLES (Filas de Tablas)
# ==========================================

class GeneroTotalRow(BaseModel):
    """Fila estandar para conteos divididos por sexo."""
    masculino: int = 0
    femenino: int = 0
    total: int = 0


class JurisdiccionSexo(BaseModel):
    """Contenedor por jurisdiccion y sexo."""
    provincial: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    nacional: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    federal: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class SituacionLegalSexo(BaseModel):
    """Contenedor por situacion legal y sexo."""
    procesados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    condenados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    inimputables: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    contraventores: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class NinosRow(BaseModel):
    """Fila para Cuadro 6 (Ninos con sus madres)."""
    ninas: int = 0
    ninos: int = 0
    total: int = 0


class AlteracionRow(BaseModel):
    """Fila para Cuadro 7 (Alteraciones del orden)."""
    danos: int = 0
    rehenes: int = 0
    heridos_muertos: int = 0
    total: int = 0


class EgresosProcesados(BaseModel):
    """Motivos de egreso para procesados."""
    absolucion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    cambio_situacion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


class EgresosCondenados(BaseModel):
    """Motivos de egreso para condenados."""
    agotamiento: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    evasion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())
    if not normalized:
        return normalized
    return normalized.upper()


class Cuadro1Dotacion(BaseModel):
    """Cuadro 1: dotacion de personal (tabla completa)."""
    dotacion_oficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_suboficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_cadetes: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_personal_civil: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class Cuadro8Suicidios(BaseModel):
    """Cuadro 8: suicidios (tabla completa)."""
    suicidios_procesados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_condenados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_inimputables: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_contraventores: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class CuadroPoblacion(BaseModel):
    """Cuadro 2: poblacion privada de libertad (tabla completa)."""
    procesados: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    condenados: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    inimputables: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    contraventores: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    otros: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


class CuadroIngresos(BaseModel):
    """Cuadro 3: ingresos del ultimo ano (tabla completa)."""
    ingresos_ultimo_ano: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class CuadroEgresos(BaseModel):
    """Cuadros 4 y 5: egresos procesados y condenados (tabla completa)."""
    procesados: EgresosProcesados = Field(default_factory=EgresosProcesados)
    condenados: EgresosCondenados = Field(default_factory=EgresosCondenados)


class CuadroNinos(BaseModel):
    """Cuadro 6: ninos alojados con sus madres (tabla completa)."""
    ninos_hasta_1: NinosRow = Field(default_factory=NinosRow)
    ninos_1_a_2: NinosRow = Field(default_factory=NinosRow)
    ninos_2_a_3: NinosRow = Field(default_factory=NinosRow)
    ninos_3_a_4: NinosRow = Field(default_factory=NinosRow)
    ninos_total: NinosRow = Field(default_factory=NinosRow)


class CuadroAlteraciones(BaseModel):
    """Cuadro 7: alteraciones del orden (tabla completa)."""
    alteraciones_fuerza: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_negociacion: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_espontanea: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_total: AlteracionRow = Field(default_factory=AlteracionRow)


class CuadroFallecidos(BaseModel):
    """Cuadro 9: fallecidos excl. suicidios (tabla completa)."""
    fallecidos_violencia_internos: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_violencia_agentes: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_otras_causas: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_total: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)


class CuadroLesiones(BaseModel):
    """Cuadro 10: lesiones en alteraciones del orden (tabla completa)."""
    lesiones_agentes_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_agentes_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

# ==========================================
# 2. ESQUEMA PRINCIPAL (El Formulario Completo)
# ==========================================

class SneepCompleto(BaseModel):
    """Esquema completo del formulario SNEEP."""
    # --- DATOS GENERALES ---
    provincia: Optional[str] = None
    reparticion: Optional[str] = None
    nombre_establecimiento: Optional[str] = None
    tipo_establecimiento: Optional[str] = None
    domicilio_cp: Optional[str] = None
    telefono_fax: Optional[str] = None
    correo_electronico: Optional[str] = None
    responsable_estadistica: Optional[str] = None

    capacidad_fisica_alojamiento: int = 0
    alojados_celdas_individuales: int = 0
    alojados_locales_colectivos: int = 0

    @field_validator(
        "provincia",
        "reparticion",
        "nombre_establecimiento",
        "tipo_establecimiento",
        "domicilio_cp",
        "telefono_fax",
        "correo_electronico",
        "responsable_estadistica",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Optional[str]) -> Optional[str]:
        return normalize_text(value)

    # --- CUADRO 1: Dotacion de Personal ---
    cuadro_1_dotacion: Cuadro1Dotacion = Field(default_factory=Cuadro1Dotacion)

    # --- CUADRO 2: Poblacion Privada de Libertad ---
    cuadro_poblacion: CuadroPoblacion = Field(default_factory=CuadroPoblacion)

    # --- CUADRO 3: Ingresos ---
    cuadro_ingresos: CuadroIngresos = Field(default_factory=CuadroIngresos)

    # --- CUADRO 4-5: Egresos ---
    cuadro_egresos: CuadroEgresos = Field(default_factory=CuadroEgresos)

    # --- CUADRO 6: Ninos ---
    cuadro_ninos: CuadroNinos = Field(default_factory=CuadroNinos)

    # --- CUADRO 7: Alteraciones ---
    cuadro_alteraciones: CuadroAlteraciones = Field(default_factory=CuadroAlteraciones)

    # --- CUADRO 8: Suicidios ---
    cuadro_8_suicidios: Cuadro8Suicidios = Field(default_factory=Cuadro8Suicidios)

    # --- CUADRO 9: Fallecidos ---
    cuadro_fallecidos: CuadroFallecidos = Field(default_factory=CuadroFallecidos)

    # --- CUADRO 10: Lesiones ---
    cuadro_lesiones: CuadroLesiones = Field(default_factory=CuadroLesiones)

```

# ==========================================
# FILE: src/database.py
# ==========================================
```python
import os
from typing import Dict, Iterable, List, Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text


def _flatten_record(record: Dict[str, object], parent_key: str = "", sep: str = "_") -> Dict[str, object]:
    items: Dict[str, object] = {}
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten_record(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


def _drop_table_if_schema_mismatch(engine, table_name: str, columns: List[str]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]
    if set(existing_columns) == set(columns):
        return

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    print(
        "⚠️  Esquema de SQLite no coincide con las columnas actuales. "
        "Se recrea la tabla para evitar fallos."
    )

def persist_results(records: Iterable[dict], output_dir: str = "data/output") -> Optional[pd.DataFrame]:
    records_list: List[dict] = list(records)
    if not records_list:
        print("No hay registros validados para persistir.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    flattened_records = [_flatten_record(record) for record in records_list]
    df = pd.DataFrame(flattened_records)

    db_path = os.path.join(output_dir, "sneep.db")
    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    engine = create_engine(f"sqlite:///{db_path}")
    _drop_table_if_schema_mismatch(engine, "sneep_records", list(df.columns))
    df.to_sql("sneep_records", con=engine, if_exists="append", index=False)

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as handle:
            header = handle.readline().strip()
        if header:
            existing_columns = header.split(",")
            if set(existing_columns) != set(df.columns):
                print(
                    "⚠️  Esquema de CSV no coincide con las columnas actuales. "
                    "Se sobrescribira el archivo."
                )
    df.to_csv(csv_path, index=False)

    print(f"✅ Persistencia OK: {len(df)} registros -> {db_path} + {csv_path}")
    return df
```

# ==========================================
# FILE: src/image_utils.py
# ==========================================
```python
"""Computer vision utilities for alignment and registration."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

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
                    "image_array": crop,
                }
            )

    return results

```
