import os
import subprocess
import logging
from typing import Optional
from .telemetry import profile_time

LOGGER = logging.getLogger(__name__)

@profile_time
def limpiar_y_enderezar(pdf_path: str, output_dir: str) -> Optional[str]:
    """
    Toma un PDF ruidoso, lo endereza y aplica limpieza de fondo.
    """
    LOGGER.info(f"Ejecutando OCRmyPDF sobre: {pdf_path}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Genera un nuevo archivo con el prefijo 'clean_'
    base_name = os.path.basename(pdf_path)
    output_pdf_path = os.path.join(output_dir, f"clean_{base_name}")
    
    comando = [
        "ocrmypdf",
        "--optimize", "0",
        "--deskew",             # Endereza páginas torcidas
        "--clean",              # Aplica unpaper (elimina manchas y artefactos)
        "--force-ocr",          # OCR forzado (cámbialo a --skip-text si quieres más velocidad)
        "--language", "spa",
        "--jobs", "4",          # Límite de concurrencia
        pdf_path,
        output_pdf_path,
    ]

    try:
        subprocess.run(comando, capture_output=True, text=True, check=True)
        LOGGER.info("✅ PDF limpiado y enderezado con éxito.")
        return output_pdf_path
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"❌ Error en OCRmyPDF (Código {e.returncode}):\n{e.stderr}")
        return None