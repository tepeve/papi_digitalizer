# REPOSITORIO: llms

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

```

## Carpeta: src/

# ==========================================
# FILE: src/batch_processor.py
# ==========================================
```python
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

```

# ==========================================
# FILE: src/llm_engine.py
# ==========================================
```python
import json
from typing import Optional

import ollama

from .schemas import SneepPage1


def _clean_json(raw_json: str) -> str:
    if "```json" in raw_json:
        return raw_json.split("```json")[1].split("```")[0].strip()
    if "```" in raw_json:
        return raw_json.split("```")[1].strip()
    return raw_json


def ejecutar_inferencia(ruta_full: str, md_struct: str) -> Optional[dict]:
    # Generamos el esquema JSON a partir de tu clase Pydantic
    esquema_json = json.dumps(SneepPage1.model_json_schema(), indent=2)

    SYSTEM_PROMPT = f"""
    Eres un experto en digitalizacion de formularios estadisticos penitenciarios (SNEEP). 
    Analiza la imagen completa del formulario.

    Estructura OCR de guia:
    {str(md_struct)[:1000]}

    REGLAS ESTRICTAS:
    1. Transcribe el texto manuscrito con exactitud. Si esta vacio o ilegible, usa null.
    2. Para TODOS los campos numericos, si estan vacios o tienen una raya, DEBES devolver el numero 0. NUNCA devuelvas "".
    3. Devuelve EXCLUSIVAMENTE un objeto JSON que respete las llaves de este esquema EXACTO:
    {esquema_json}
    """

    print("5. Iniciando inferencia en Qwen2.5-VL (Imagen Unica)...")
    response = ollama.chat(
        model="qwen2.5vl:7b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Procesa esta imagen y extrae los datos al JSON.",
                "images": [ruta_full],
            },
        ],
    )

    raw_json = response["message"]["content"]
    raw_json = _clean_json(raw_json)

    print("6. Validando con Pydantic...")
    try:
        data_validada = SneepPage1.model_validate_json(raw_json)
        print("✅ ¡Validacion Pydantic superada!")
        return data_validada.model_dump()
    except Exception as e:
        print(f"❌ Error de validacion Pydantic:\n{e}")
        print(f"\n--- JSON DEVUELTO POR LA IA ---\n{raw_json}")
        return None

```

# ==========================================
# FILE: src/schemas.py
# ==========================================
```python
from typing import List, Optional

from pydantic import BaseModel


class StaffRow(BaseModel):
    categoria: str
    masculino: Optional[int] = 0
    femenino: Optional[int] = 0
    total: Optional[int] = 0


class PopulationRow(BaseModel):
    situacion_legal: str
    provincial_masc: Optional[int] = 0
    provincial_fem: Optional[int] = 0
    nacional_masc: Optional[int] = 0
    nacional_fem: Optional[int] = 0
    federal_masc: Optional[int] = 0
    federal_fem: Optional[int] = 0
    total: Optional[int] = 0


class SneepPage1(BaseModel):
    provincia: Optional[str] = None
    reparticion: Optional[str] = None
    nombre_establecimiento: Optional[str] = None
    tipo_establecimiento: Optional[str] = None
    domicilio_cp: Optional[str] = None
    telefono_fax: Optional[str] = None
    email: Optional[str] = None
    responsable_estadistica: Optional[str] = None
    capacidad_fisica_alojamiento: Optional[int] = 0
    alojados_celdas_individuales: Optional[int] = 0
    alojados_locales_colectivos: Optional[int] = 0
    dotacion_personal: List[StaffRow]
    poblacion_por_jurisdiccion: List[PopulationRow]

```

# ==========================================
# FILE: src/database.py
# ==========================================
```python
import json
import os
from typing import Iterable, List, Optional

import pandas as pd
from sqlalchemy import create_engine


def persist_results(records: Iterable[dict], output_dir: str = "data/output") -> Optional[pd.DataFrame]:
    records_list: List[dict] = list(records)
    if not records_list:
        print("No hay registros validados para persistir.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(records_list)
    if "dotacion_personal" in df.columns:
        df["dotacion_personal"] = df["dotacion_personal"].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
        )
    if "poblacion_por_jurisdiccion" in df.columns:
        df["poblacion_por_jurisdiccion"] = df["poblacion_por_jurisdiccion"].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
        )

    db_path = os.path.join(output_dir, "sneep.db")
    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql("sneep_records", con=engine, if_exists="append", index=False)
    df.to_csv(csv_path, index=False)

    print(f"✅ Persistencia OK: {len(df)} registros -> {db_path} + {csv_path}")
    return df

```

# ==========================================
# FILE: src/image_utils.py
# ==========================================
```python
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

```
