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
