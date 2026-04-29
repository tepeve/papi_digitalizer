# PAPI Digitalizer (Qwen2.5-VL)

Pipeline 100% local para digitalizar encuestas PAPI (SNEEP 2) usando alineamiento ORB, OMR/ICR/TABLE_ICR y el modelo multimodal Qwen2.5-VL 7B vía Ollama.

## Requisitos del sistema

```bash
sudo apt update
sudo apt install ocrmypdf tesseract-ocr-spa ghostscript unpaper poppler-utils -y
```

Además, tener [Ollama](https://ollama.com) instalado y el modelo descargado:

```bash
ollama pull qwen2.5vl:7b
```

## Instalación

Se recomienda `uv` como gestor de entornos:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Alternativamente con pip estándar:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Estructura de datos

```
data/
├── raw/        # PDFs de entrada
├── template/   # master_template.pdf (plantilla maestra)
├── processed/  # Artefactos de debug por documento (<sha256>/)
├── quarantine/ # PDFs con errores + *_error.txt + *_data.json
└── output/     # sneep_backup.csv
```

## Uso rápido

1. Colocar los PDFs a procesar en `data/raw/`.
2. Colocar la plantilla maestra en `data/template/master_template.pdf`.
3. Generar (o verificar) `template_mapping.json` con el labeler interactivo:

```bash
python tools/roi_labeler.py
```

4. Ejecutar el pipeline batch:

```bash
python main.py
```

Los resultados válidos se persisten en `data/output/sneep_backup.csv`. La versión de la aplicación para correr en instancias virtuales prescinde del feature que persiste datos en una base SQLite `data/output/sneep.db`. Los documentos con errores se mueven a `data/quarantine/`.

Activar modo debug para guardar overlays y recortes intermedios:

```bash
DEBUG_MODE=1 python main.py
```

## Docker (con soporte CUDA)

La imagen base es `nvidia/cuda:12.2.0-base-ubuntu22.04`. Para construir y levantar el contenedor:

```bash
docker compose up --build
```

El servicio monta el directorio actual en `/app` y se conecta al servidor Ollama del host vía `OLLAMA_HOST=http://host.docker.internal:11434`.

## Variables de entorno

| Variable | Valores | Descripción |
|---|---|---|
| `DEBUG_MODE` | `1` / `0` | Guarda imágenes de debug en `data/processed/<sha256>/` |
| `OLLAMA_HOST` | URL | Endpoint del servidor Ollama (default: `http://host.docker.internal:11434`) |

## Notas
- `document_id` (SHA-256 del PDF) está incluido en el modelo 
- `src/telemetry.py` expone el decorador `@profile_time` para medir tiempos de ejecución de funciones críticas.
- `pymupdf4llm` está declarado como dependencia pero no se usa en el pipeline actual.
- El LLM nunca escribe directamente en la base de datos; Pydantic es la barrera de validación.