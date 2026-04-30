# PAPI Digitalizer (Qwen2.5-VL) — rama `main`

Pipeline 100% local para la digitalización y extracción de información de encuestas PAPI y formularios completados a mano mediante OCR/ICR, alineamiento ORB y LLMs Multimodales (Qwen2.5-VL 7B).

> **Rama orientada a desarrollo local, configuración de plantillas y pruebas.**
> Incluye herramientas con interfaz gráfica (UI) para la definición de Regiones de Interés (ROIs) y persistencia dual en bases de datos. 
> Para ejecución serverless o masiva en instancias remotas, consultar la rama `gpu-batch`.

## Diferencias entre ramas

| Aspecto | `main` (esta rama) | `gpu-batch` |
|---|---|---|
| UI de definición de ROIs | `tools/roi_labeler.py` y `roi_viewer.py` disponibles | **Eliminadas** — asume configuración previa |
| Persistencia de resultados | **SQLite (`sneep.db`) + CSV** | Solo CSV (`sneep_backup.csv`) |
| `docker-compose.yml` | Servicio único `papi-digitalizer` (red host) | Dos servicios aislados (App + Ollama) |
| Imagen base Docker | Incluye dependencias GUI (`libqt5gui5`, etc.) | Headless (sin dependencias gráficas) |
| `OLLAMA_HOST` por defecto | `http://host.docker.internal:11434` | `http://ollama:11434` |

## Entorno de Ejecución

Esta rama está optimizada para ejecutarse en estaciones de trabajo locales (Bare-Metal) o mediante Docker, permitiendo abrir ventanas interactivas para dibujar sobre los PDFs y configurar el mapeo de datos antes de un procesamiento masivo.

## Estructura del Proyecto

```text
papi_digitalizer/
├── data/
│   ├── raw/        # PDFs de entrada a procesar
│   ├── template/   # Plantilla maestra (master_template.pdf)
│   ├── processed/  # Artefactos visuales de debug (alineamiento, recortes)
│   ├── quarantine/ # Archivos originales con error, logs (.txt) y payloads (.json)
│   └── output/     # Base de datos (sneep.db) y backup (sneep_backup.csv)
├── src/            # Lógica central del pipeline y esquemas de validación
└── tools/          # Herramientas visuales interactivas (Labeler y Viewer)
```

## Requisitos del sistema

Para instalaciones nativas (fuera de Docker), el sistema requiere herramientas de procesamiento de imágenes y compresión:

```bash
sudo apt-get update && sudo apt-get install -y \
    ocrmypdf \
    tesseract-ocr-spa \
    ghostscript \
    unpaper \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libqt5gui5
```

## Instalación y Gestión de Entornos

### Opción A: Instalación Nativa (Recomendada con `uv`)

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```
*(Alternativamente, puedes usar `python -m venv .venv` y `pip install -e .`)*

**Instalación de Ollama y Modelo:**
Debes tener [Ollama](https://ollama.com/) ejecutándose localmente:

```bash
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
ollama serve > ollama.log 2>&1 &
ollama pull qwen2.5vl:7b
```

### Opción B: Despliegue en Docker (Soporte CUDA)

La imagen base `nvidia/cuda:12.2.0-base-ubuntu22.04` incluye todas las dependencias del sistema y GUI. 
```bash
docker compose up --build
```
*Nota: El servicio usa `network_mode: "host"` para conectarse fácilmente al servidor Ollama de tu máquina local y expone el volumen `/tmp/.X11-unix` para permitir la apertura de interfaces gráficas desde el contenedor.*

La primera vez que se levanta docker compose luego de buildear se debe hacer pull de ollama en la imagen

```bash
 docker compose exec ollama ollama pull qwen2.5vl:7b
```

## Instrucciones de Uso (Configuración)

Antes de procesar un lote, debes mapear las coordenadas del documento físico contra los modelos de datos.

### 1. Preparación de Archivos
* Coloca un escaneo en blanco y en alta calidad de tu formulario en `data/template/master_template.pdf`.
* Define las estructuras de datos esperadas (clases de Pydantic) editando el archivo `src/schemas.py`.

### 2. Mapeo Interactivo de ROIs (`roi_labeler`)
Ejecuta la herramienta gráfica para dibujar las cajas delimitadoras (Bounding Boxes) sobre la plantilla maestra:

```bash
python tools/roi_labeler.py
```
* **Modo NEW:** Permite navegar por las páginas del PDF maestro (teclas `n`/`p`), dibujar ROIs con el ratón y asignarles un `field_id` (que debe coincidir con tu `schemas.py`) y un tipo (`ICR`, `OMR`, `TABLE_ICR`).
* **Modo EDIT:** Permite modificar o re-dibujar regiones previamente guardadas.
* El resultado se guardará en `template_mapping.json` en la raíz del proyecto.

### 3. Verificación Visual (`roi_viewer`)
Para corroborar que todas las coordenadas se hayan guardado correctamente:
```bash
python tools/roi_viewer.py
```
*Esto generará imágenes en `data/processed/` con las cajas rojas dibujadas sobre la plantilla.*

## Ejecución y Procesamiento (Flujo de trabajo Batch)

Una vez configurado el `template_mapping.json`:

1. **Cargar:** Coloca todos los PDFs a procesar en `data/raw/`.
2. **Ejecutar:** Inicia el pipeline principal. Puedes controlar el nivel de debug y limpieza:
   ```bash
   DEBUG_MODE=1 CLEAN_SCANS=0 python main.py
   ```
3. **Revisar:** Los resultados exitosos se persistirán en la carpeta `output/`.
4. **Recuperar (Quarantine):** Si un documento falla la validación de Pydantic, el PDF original y su error van a `data/quarantine/`.
   * Abre el archivo `*_data.json` generado en cuarentena.
   * Corrige manualmente el dato que causó el error de validación.
   * Inyecta el registro corregido directamente a la base de datos usando:
     ```bash
     python recover.py data/quarantine/nombre_del_archivo_data.json
     ```

## Persistencia de Resultados

La rama `main` utiliza una estrategia de persistencia dual robusta a través de `src/database.py`:
* **SQLite (`sneep.db`):** Base de datos relacional principal. Crea e infiere automáticamente las columnas en base a la estructura aplanada de Pydantic. Si detecta cambios en el esquema (agregaste o quitaste campos), recreará la tabla temporalmente para evitar fallos.
* **CSV (`sneep_backup.csv`):** Respaldo plano de fácil acceso para exportación rápida.

*Nota: Ambos registros incluyen el `document_id` (Hash SHA-256 del archivo original), garantizando la trazabilidad exacta del dato extraído con el documento físico, sin importar cuántas veces pase por el preprocesador.*

## Variables de Entorno

| Variable | Valores | Descripción |
|---|---|---|
| `DEBUG_MODE` | `1` / `0` | Si es `1`, guarda imágenes del proceso de alineamiento (ORB) en `data/processed/<sha256>/`. |
| `CLEAN_SCANS` | `1` / `0` | Si es `1`, activa el pre-procesamiento (`ocrmypdf` + `unpaper`) para limpiar ruido de fondo y enderezar antes de la IA. |
| `OLLAMA_HOST` | URL | Endpoint de conexión a la API de Ollama (default: `http://host.docker.internal:11434`). |
```