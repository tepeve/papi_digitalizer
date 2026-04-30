import json
import os
import shutil
import traceback
from typing import Dict, List, Optional
from .telemetry import profile_time
import logging

LOGGER = logging.getLogger(__name__)

from tqdm import tqdm

from .database import persist_results
from .pipeline import load_master_template, process_document
from .preprocessor import limpiar_pdf

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


@profile_time
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

    apply_cleaning = os.getenv("CLEAN_SCANS", "0").strip().lower() in {"1", "true", "yes"}

    for raw_pdf_path in tqdm(files, desc="Procesando", unit="pdf"):
        # Mantenemos registro del PDF original para cuarentenas y hash
        process_path = raw_pdf_path 
        
        try:
            if apply_cleaning:
                cleaned_pdf_path = limpiar_pdf(raw_pdf_path, "data/cleaned")
                if cleaned_pdf_path is None:
                    quarantine_count += 1
                    _quarantine_file(raw_pdf_path, "Error al limpiar el PDF.\n")
                    continue
                process_path = cleaned_pdf_path

            # IMPORTANTE: Procesamos el limpio, pero si tuvieras forma de pasarle 
            # el hash original a process_document sería ideal. 
            # Como mínimo, ahora la cuarentena no se rompe.
            data = process_document(process_path, master_pages, template_mapping)
            
            if data is None:
                quarantine_count += 1
                _quarantine_file(raw_pdf_path, "Pipeline devolvio None.\n")
                continue

            if "errors" in data:
                quarantine_count += 1
                error_text = f"Pydantic validation failed: {data.get('errors', '')}\n"
                _quarantine_file(raw_pdf_path, error_text, payload=data.get("data"))
                continue

            results.append(data)
            success_count += 1
            
            # Limpieza (Opcional): Borrar el archivo original si todo salió bien, 
            # o moverlo a una carpeta de "completados".
            # os.remove(raw_pdf_path) 
            
        except Exception:
            quarantine_count += 1
            error_text = traceback.format_exc()
            _quarantine_file(raw_pdf_path, error_text) # Envia el ORIGINAL a cuarentena
            continue

    if results:
        persist_results(results)

    return {
        "total": len(files),
        "success": success_count,
        "quarantine": quarantine_count,
        "results": results,
    }
