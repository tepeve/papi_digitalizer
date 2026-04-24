import os
from pathlib import Path
from typing import Optional

from .image_utils import preparar_documento
from .llm_engine import ejecutar_inferencia
from .preprocessor import limpiar_y_enderezar


def _output_dir_for_image(image_path: str) -> str:
    image_stem = Path(image_path).stem
    return os.path.join("data", "processed", image_stem)


def process_single_image(image_path: str) -> Optional[dict]:
    output_dir = _output_dir_for_image(image_path)

    # 1. Preprocesamiento (Limpiar y enderezar)
    pdf_limpio = limpiar_y_enderezar(image_path, output_dir)
    if not pdf_limpio:
        return None

    # 2. Preparamos 1 sola imagen y el texto base
    ruta_full, md_struct = preparar_documento(pdf_limpio, output_dir)

    # 3. Inferencia + Validacion
    return ejecutar_inferencia(ruta_full, md_struct)
