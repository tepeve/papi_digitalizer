import json
import os
import shutil
import traceback
import hashlib
import logging
from typing import Dict, List, Optional

from tqdm import tqdm
from .telemetry import profile_time
from .database import persist_results
from .pipeline import load_master_template, process_document
from .preprocessor import limpiar_y_enderezar  # Importado de gpu-batch

LOGGER = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf"}

def _sha256_file(path: str) -> str:
    """Calcula el hash del archivo original para mantener la integridad del ID."""
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

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

def _quarantine_file(pdf_path: str, error_text: str, document_id: str, payload: Optional[Dict[str, object]] = None) -> None:
    """
    Mueve el archivo original a cuarentena usando el hash como prefijo 
    para evitar colisiones y asegurar trazabilidad.
    """
    quarantine_dir = os.path.join("data", "quarantine")
    _ensure_dir(quarantine_dir)

    # Usamos los primeros 8 caracteres del hash para identificar el archivo unívocamente
    prefix = document_id[:8]
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    
    dest_name = f"{prefix}_{os.path.basename(pdf_path)}"
    dest_path = os.path.join(quarantine_dir, dest_name)
    error_path = os.path.join(quarantine_dir, f"{prefix}_{stem}_error.txt")
    data_path = os.path.join(quarantine_dir, f"{prefix}_{stem}_data.json")

    # Mover archivo original
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
        LOGGER.info(f"No se encontraron PDFs en {input_dir}.")
        return None

    master_pages = load_master_template(master_pdf_path)
    results: List[dict] = []
    success_count = 0
    quarantine_count = 0

    # Lógica de gpu-batch: permitir limpieza opcional vía variable de entorno
    apply_cleaning = os.getenv("CLEAN_SCANS", "0").strip().lower() in {"1", "true", "yes"}

    for raw_pdf_path in tqdm(files, desc="Procesando", unit="pdf"):
        # 1. GENERACIÓN DEL ID (FIX): Siempre sobre el archivo original
        doc_id = _sha256_file(raw_pdf_path)
        process_path = raw_pdf_path 
        
        try:
            # 2. PREPROCESAMIENTO: Si se limpia, el archivo cambia pero el doc_id no
            if apply_cleaning:
                cleaned_pdf_path = limpiar_y_enderezar(raw_pdf_path, "data/cleaned")
                if cleaned_pdf_path is None:
                    quarantine_count += 1
                    _quarantine_file(raw_pdf_path, "Error en limpieza (unpaper/ocrmypdf)", doc_id)
                    continue
                process_path = cleaned_pdf_path

            # 3. EJECUCIÓN: Pasamos el doc_id original para que el pipeline no lo recalcule erróneamente
            # Nota: Asegúrate de actualizar la firma de process_document en pipeline.py para aceptar 'forced_id'
            data = process_document(process_path, master_pages, template_mapping, forced_id=doc_id)
            
            if data is None:
                quarantine_count += 1
                _quarantine_file(raw_pdf_path, "El pipeline devolvió un objeto nulo.", doc_id)
                continue

            if "errors" in data:
                quarantine_count += 1
                error_text = f"Fallo en validación Pydantic: {data.get('errors', '')}\n"
                _quarantine_file(raw_pdf_path, error_text, doc_id, payload=data.get("data"))
                continue

            results.append(data)
            success_count += 1
            
            # (Opcional) Limpiar archivos temporales en data/cleaned si el proceso fue exitoso
            if apply_cleaning and os.path.exists(process_path):
                os.remove(process_path)

        except Exception:
            quarantine_count += 1
            error_text = traceback.format_exc()
            _quarantine_file(raw_pdf_path, error_text, doc_id)
            continue

    if results:
        persist_results(results)

    return {
        "total": len(files),
        "success": success_count,
        "quarantine": quarantine_count,
        "results": results,
    }