# PAPI Digitalizer (Qwen2.5-VL) — rama `gpu-batch`

> **Rama orientada a ejecución en instancias GPU remotas (RunPod / VMs con CUDA).**
> Versión simplificada sin UI de definición de ROIs ni persistencia en SQLite.
> Para la versión de desarrollo local consultar la rama `main`.

Pipeline 100% local para digitalizar encuestas PAPI (SNEEP 2) usando alineamiento ORB, OMR/ICR/TABLE_ICR y el modelo multimodal Qwen2.5-VL 7B vía Ollama.

## Cambios respecto a `main`

| Aspecto | `main` | `gpu-batch` (esta rama) |
|---|---|---|
| UI de definición de ROIs | `tools/roi_labeler.py` disponible | **Eliminada** — se asume `template_mapping.json` ya generado |
| Persistencia de resultados | CSV + SQLite (`sneep.db`) | **Solo CSV** (`sneep_backup.csv`) |
| `docker-compose.yml` | Servicio único `papi-digitalizer` | **Dos servicios**: `ollama` (con GPU) + `papi-digitalizer` |
| Imagen base Docker | `nvidia/cuda:12.2.0-base-ubuntu22.04` | Igual, sin librerías de GUI (`libqt5gui5`, etc.) |
| `OLLAMA_HOST` por defecto | `http://host.docker.internal:11434` | `http://ollama:11434` (red interna de Compose) |

## Estructura de datos

```
data/
├── raw/        # PDFs de entrada (se cargan desde el equipo local via VS Code)
├── template/   # master_template.pdf (plantilla maestra)
├── processed/  # Artefactos de debug por documento (<sha256>/)
├── quarantine/ # PDFs con errores + *_error.txt + *_data.json
└── output/     # sneep_backup.csv
```

## Uso rápido (ejecución contenerizada en RunPod)

> Se asume que `template_mapping.json` ya fue generado en el entorno de desarrollo local con `roi_labeler.py` y está commiteado en el repositorio.

1. Levantar el servidor Ollama (con acceso a GPU):

```bash
docker compose up -d ollama
```

2. Descargar los pesos del modelo visual dentro del contenedor:

```bash
docker exec -it ollama_server ollama pull qwen2.5vl:7b
```

3. Ejecutar el pipeline de procesamiento por lotes:

```bash
docker compose up --build papi-digitalizer
```

El contenedor se apaga solo al terminar. Los resultados se escriben en `data/output/sneep_backup.csv`. Los documentos con errores se mueven a `data/quarantine/`.

Activar modo debug para guardar overlays y recortes intermedios:

```bash
DEBUG_MODE=1 docker compose up --build papi-digitalizer
```

## Despliegue en RunPod paso a paso

### Configuración del Pod recomendada

| Parámetro | Valor |
|---|---|
| GPU | RTX 3090 (24 GB VRAM) |
| Template | Runpod Pytorch 2.4.0 (`runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`) |
| SSH terminal access | Activado |
| Volume disk | 40 GB |

### Fase 1 — Tareas previas al deploy

1. Cargar créditos en la cuenta de RunPod.
2. Generar (o verificar) la clave SSH local y vincularla en **Settings > SSH Keys**:

```bash
ssh-keygen -t ed25519 -C "tu@email.com"
cat ~/.ssh/id_ed25519.pub
```

3. En la interfaz de RunPod, replicar la configuración de la tabla anterior y hacer clic en **Deploy On-Demand**.

### Fase 2 — Conexión al pod

1. Esperar a que el pod figure como *Running*. Hacer clic en **Connect** y copiar el comando SSH.
2. En VS Code: `F1` → `Remote-SSH: Connect to Host...` → `Add New SSH Host...` → pegar el comando.
3. Seleccionar **Linux** como sistema operativo y aceptar el fingerprint. El indicador verde en la esquina inferior izquierda confirma la conexión.

### Fase 3 — Preparación del entorno remoto

```bash
git clone -b gpu-batch https://github.com/tu_usuario/papi_digitalizer.git
cd papi_digitalizer
```

Cargar los PDFs a procesar arrastrándolos desde el explorador de VS Code hacia `data/raw/` en la máquina remota.

### Fase 4 — Ejecución del pipeline

```bash
docker compose up -d ollama
docker exec -it ollama_server ollama pull qwen2.5vl:7b
docker compose up --build papi-digitalizer
```

### Fase 5 — Extracción de resultados y apagado

1. En el explorador de VS Code, hacer clic derecho sobre `data/output/sneep_backup.csv` → **Download**.
2. Gestionar el pod según el caso:
   - **Stop** → si se procesarán más PDFs en otra sesión (se factura solo el almacenamiento, ~$0.011/hr).
   - **Terminate** (ícono de papelera) → si el proyecto finalizó por completo (facturación $0.00).

## Variables de entorno

| Variable | Valores | Descripción |
|---|---|---|
| `DEBUG_MODE` | `1` / `0` | Guarda imágenes de debug en `data/processed/<sha256>/` |
| `OLLAMA_HOST` | URL | Endpoint del servidor Ollama (default interno: `http://ollama:11434`) |

## Notas
- `document_id` (SHA-256 del PDF) está incluido en el modelo.
- `src/telemetry.py` expone el decorador `@profile_time` para medir tiempos de ejecución de funciones críticas.
- `pymupdf4llm` está declarado como dependencia pero no se usa en el pipeline actual.
- El LLM nunca escribe directamente en el CSV; Pydantic es la barrera de validación.