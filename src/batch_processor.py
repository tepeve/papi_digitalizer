import os
import shutil
import traceback
from typing import Dict, List, Optional

from tqdm import tqdm

from .database import persist_results
from .pipeline import process_single_image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _iter_image_files(input_dir: str) -> List[str]:
    files: List[str] = []
    for name in os.listdir(input_dir):
        full_path = os.path.join(input_dir, name)
        if not os.path.isfile(full_path):
            continue
        _, ext = os.path.splitext(name)
        if ext.lower() in SUPPORTED_EXTENSIONS:
            files.append(full_path)
    return sorted(files)


def _quarantine_file(image_path: str, error_text: str) -> None:
    quarantine_dir = os.path.join("data", "quarantine")
    _ensure_dir(quarantine_dir)

    stem = os.path.splitext(os.path.basename(image_path))[0]
    dest_path = os.path.join(quarantine_dir, os.path.basename(image_path))
    error_path = os.path.join(quarantine_dir, f"{stem}_error.txt")

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(os.path.basename(image_path))
        dest_path = os.path.join(quarantine_dir, f"{base}_dup{ext}")
    shutil.move(image_path, dest_path)

    with open(error_path, "w", encoding="utf-8") as f:
        f.write(error_text)


def process_batch(input_dir: str) -> Optional[Dict[str, object]]:
    files = _iter_image_files(input_dir)
    if not files:
        print(f"No se encontraron imagenes en {input_dir}.")
        return None

    results: List[dict] = []
    success_count = 0
    quarantine_count = 0

    for image_path in tqdm(files, desc="Procesando", unit="img"):
        try:
            data = process_single_image(image_path)
            if not data:
                quarantine_count += 1
                _quarantine_file(image_path, "Pipeline devolvio None.\n")
                continue

            results.append(data)
            success_count += 1
        except Exception:
            quarantine_count += 1
            error_text = traceback.format_exc()
            _quarantine_file(image_path, error_text)
            continue

    if results:
        persist_results(results)

    return {
        "total": len(files),
        "success": success_count,
        "quarantine": quarantine_count,
        "results": results,
    }
