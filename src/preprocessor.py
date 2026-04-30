import os
import subprocess
import logging
from typing import Optional
from .telemetry import profile_time

LOGGER = logging.getLogger(__name__)

@profile_time
def limpiar_pdf(pdf_path: str, output_dir: str) -> Optional[str]:
    """
    Toma un PDF ruidoso y aplica unpaper para limpiar el fondo.
    Omite deliberadamente Tesseract (--skip-text) para ahorrar CPU.
    """
    LOGGER.info(f"Ejecutando limpieza (unpaper) sobre: {pdf_path}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Genera un nuevo archivo con el prefijo 'clean_'
    base_name = os.path.basename(pdf_path)
    output_pdf_path = os.path.join(output_dir, f"clean_{base_name}")
    
    comando = [
        "ocrmypdf",
        "--optimize", "0",
        "--clean",              # Aplica unpaper (elimina manchas y artefactos)
        "--skip-text",          # Apaga Tesseract (vital para la RTX A5000)
        "--jobs", "4",          # Límite de concurrencia de vCPU
        "--fast-web-view", "0",
        pdf_path,
        output_pdf_path,
    ]

    try:
        subprocess.run(comando, capture_output=True, text=True, check=True)
        LOGGER.info("✅ PDF limpiado con éxito.")
        return output_pdf_path
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"❌ Error en OCRmyPDF (Código {e.returncode}):\n{e.stderr}")
        return None