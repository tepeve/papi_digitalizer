from typing import Tuple

from pdf2image import convert_from_path
from PIL import Image
import pymupdf4llm


def preparar_documento(pdf_limpio_path: str, output_dir: str) -> Tuple[str, str]:
    print("3. Convirtiendo PDF limpio a imagen optimizada para IA...")
    # Bajamos los DPI a 100 de base para trabajar con una imagen mas docil
    paginas = convert_from_path(pdf_limpio_path, dpi=100)
    imagen = paginas[0]

    w, h = imagen.size

    # --- EL FIX DEFINITIVO (Bypass al auto-resize de Ollama) ---
    max_edge = 1008  # Limite ultra seguro (36 x 28)

    # Calculamos la proporcion base para no deformar la hoja
    if w > h:
        new_w = max_edge
        new_h = int(h * (max_edge / w))
    else:
        new_h = max_edge
        new_w = int(w * (max_edge / h))

    # Aplicamos la regla estricta de multiplos de 28 a la miniatura
    final_w = (new_w // 28) * 28
    final_h = (new_h // 28) * 28

    # Un "safety net" por si las dudas
    final_w = max(28, final_w)
    final_h = max(28, final_h)

    # Redimensionamiento final de alta calidad
    imagen = imagen.resize((final_w, final_h), Image.Resampling.LANCZOS)
    # --- FIN DEL FIX ---

    ruta_full = f"{output_dir}/documento_completo.jpg"
    imagen.save(ruta_full, "JPEG", quality=95)

    print("4. Extrayendo esqueleto Markdown (PyMuPDF4LLM)...")
    markdown_structure = pymupdf4llm.to_markdown(pdf_limpio_path)

    return ruta_full, markdown_structure
