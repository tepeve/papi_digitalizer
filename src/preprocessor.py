import os
import subprocess
import logging
from typing import Optional
from .telemetry import profile_time

LOGGER = logging.getLogger(__name__)


def _resolve_clean_strategy(explicit_strategy: Optional[str] = None) -> str:
    strategy = (explicit_strategy or os.getenv("CLEAN_STRATEGY", "fast")).strip().lower()
    if strategy in {"robust", "full", "quality"}:
        return "robust"
    return "fast"


def _build_ocrmypdf_command(pdf_path: str, output_pdf_path: str, strategy: str) -> list[str]:
    base_cmd = [
        "ocrmypdf",
        "--optimize", "0",
        "--clean",
        "--jobs", "4",
    ]

    if strategy == "robust":
        # Calidad prioritaria: deskew + OCR forzado.
        return base_cmd + [
            "--deskew",
            "--force-ocr",
            "--language", "spa",
            pdf_path,
            output_pdf_path,
        ]

    # Costo CPU prioritario: limpieza sin OCR para ejecución masiva.
    return base_cmd + [
        "--skip-text",
        "--fast-web-view", "0",
        pdf_path,
        output_pdf_path,
    ]

@profile_time
def limpiar_pdf(pdf_path: str, output_dir: str, strategy: Optional[str] = None) -> Optional[str]:
    """
    Limpia un PDF usando una estrategia configurable por entorno:
    - fast (default): limpieza rápida sin OCR completo
    - robust: limpieza + deskew + OCR forzado
    """
    resolved_strategy = _resolve_clean_strategy(strategy)
    LOGGER.info("Ejecutando limpieza sobre %s con estrategia=%s", pdf_path, resolved_strategy)
    os.makedirs(output_dir, exist_ok=True)
    
    # Genera un nuevo archivo con el prefijo 'clean_'
    base_name = os.path.basename(pdf_path)
    output_pdf_path = os.path.join(output_dir, f"clean_{base_name}")
    comando = _build_ocrmypdf_command(pdf_path, output_pdf_path, resolved_strategy)

    try:
        subprocess.run(comando, capture_output=True, text=True, check=True)
        LOGGER.info("PDF limpiado con exito.")
        return output_pdf_path
    except subprocess.CalledProcessError as e:
        LOGGER.error("Error en OCRmyPDF (codigo %s):\n%s", e.returncode, e.stderr)
        return None


def limpiar_y_enderezar(pdf_path: str, output_dir: str) -> Optional[str]:
    """Alias retrocompatible para la estrategia robust."""
    return limpiar_pdf(pdf_path, output_dir, strategy="robust")