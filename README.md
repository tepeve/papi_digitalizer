# PAPI Digitalizer (Qwen2.5-VL) — rama `gpu-batch`

Pipeline para la digitalización y extracción de información de encuestas PAPI y formularios completados a mano mediante OCR/ICR y LLMs Multimodales (Qwen2.5-VL 7B)

> **Rama orientada a ejecución en instancias GPU remotas (RunPod / VMs con CUDA).**
> Versión simplificada sin UI de definición de ROIs ni persistencia en SQLite.
> Para la versión de desarrollo local consultar la rama `main`.

## Cambios respecto a `main`

| Aspecto | `main` | `gpu-batch` (esta rama) |
|---|---|---|
| UI de definición de ROIs | `tools/roi_labeler.py` disponible | **Eliminada** — se asume `template_mapping.json` ya generado |
| Persistencia de resultados | CSV + SQLite (`sneep.db`) | **Solo CSV** (`sneep_backup.csv`) |
| `docker-compose.yml` | Servicio único `papi-digitalizer` | **Dos servicios**: `ollama` (con GPU) + `papi-digitalizer` |
| Imagen base Docker | `nvidia/cuda:12.2.0-base-ubuntu22.04` | Igual, sin librerías de GUI (`libqt5gui5`, etc.) |
| `OLLAMA_HOST` por defecto | `http://host.docker.internal:11434` | `http://ollama:11434` (red interna de Compose) |

> Se asume que `template_mapping.json` ya fue generado en el entorno de desarrollo local con `roi_labeler.py` y el contrato de datos está commiteado en el repositorio que clonará en la instancia virtual.

## Entorno de Ejecución
Esta rama soporta dos modos de despliegue para garantizar la integridad y la velocidad:

1. **Desarrollo/Pods (Instalación Nativa):** Optimizado para debugeo en instancias de GPU (como RunPod). Evita el overhead de contenedores y facilita el acceso al sistema de archivos.
2. **Producción (Serverless):** Basado en contenedores Docker para escalabilidad.

## Estructura de datos

```
data/
├── raw/        # PDFs de entrada (se cargan desde el equipo local via VS Code)
├── template/   # master_template.pdf (plantilla maestra)
├── processed/  # Artefactos de debug por documento (<sha256>/)
├── quarantine/ # PDFs con errores + *_error.txt + *_data.json
└── output/     # sneep_backup.csv
```

## Despliegue en RunPod paso a paso

### Configuración del Pod recomendada

| Parámetro | Valor |
|---|---|
| GPU | RTX A5000 24 VRAM / 50GB RAM / PvCPU) / RTX 3090 (24 GB VRAM / 125 GB RAM 32 VCPU) |
| Template | Runpod Pytorch 2.4.0 (`runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`) |
| SSH terminal access | Activado |
| Volume disk | 40 GB |

### 1.Tareas previas al deploy

1. Cargar créditos en la cuenta de RunPod.

2. Generar (o verificar) la clave SSH local y vincularla en **Settings > SSH Keys**:

```bash
ssh-keygen -t ed25519 -C "tu@email.com"
cat ~/.ssh/id_ed25519.pub
```

3. En la interfaz de RunPod, replicar la configuración de la tabla anterior y hacer clic en **Deploy On-Demand**.

### 2.Conexión a la instancia de procesamiento remota(Pod)

1. Esperar a que el pod figure como *Running*. Hacer clic en **Connect** y copiar el comando SSH-TCP.

2. Edita tu configuración SSH local: `nano ~/.ssh/config` (o en Windows `C:\Users\<USER_NAME>\.ssh\config`):
   ```text
   Host runpod_a5000
       HostName <IP_TCP>
       User root
       Port <PUERTO_TCP>
       IdentityFile <PATH_TO_YOUR_PRIVATE_KEY>

3. En VS Code: `F1` → `Remote-SSH: Connect to Host...` → `Add New SSH Host...` → pegar el comando ssh vía TCP.
4. Seleccionar **Linux** como sistema operativo y aceptar el fingerprint. El indicador verde en la esquina inferior izquierda confirma la conexión.

### 3. Preparación del entorno remoto
Una vez conectado a la instancia virtual hay que clonar el repositorio de nuestro programa e instalar dependencias. 

#### 3.1.Clonar repositorio
```bash
git clone -b gpu-batch https://github.com/tu_usuario/papi_digitalizer.git
cd papi_digitalizer
```
#### 3.2. Dependencias de OCR, compresión y sistema

```bash
apt-get update && apt-get install -y zstd ocrmypdf tesseract-ocr-spa ghostscript unpaper poppler-utils libgl1-mesa-glx libglib2.0-0 zip
```
#### 3.3.Instalar Ollama y servir Qwen-vl
```bash
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
ollama serve > ollama.log 2>&1 &
ollama pull qwen2.5vl:7b
```
#### 3.4.Instalar Aplicación y Librerías
```bash
pip install uv
uv pip install --system -e .
```

# 4. Ejecución y Procesamiento

Cargar los PDFs a procesar arrastrándolos desde el explorador de VS Code hacia `data/raw/` en la máquina remota.

### Flujo de trabajo
1. **Ejecutar:** `python main.py`. Para modo Debug y con scans prolijos, ejecutar: `DEBUG_MODE=1 CLEAN_SCANS=0 python main.py`
2. **Revisar:** Los resultados se escriben en `data/output/sneep_backup.csv`. Los documentos con errores se mueven a `data/quarantine/`, inspeccionar los archivos `.json` con los documentos con datos incorrectos y el `.txt` de error.
3. **Corregir:** Editar el JSON con el valor correcto (dato limpio, sin "ruido").
4. **Recuperar:** Ejecutar `python recover.py data/quarantine/nombre_archivo.json`.

### 5.Extracción de resultados y apagado

1. En el explorador de VS Code, hacer clic derecho sobre `data/output/sneep_backup.csv` → **Download**. O bien Empaquetar todos archivos generados con `zip -r resultados_batch.zip data/output/ data/quarantine/ data/processed/`.
2. Gestionar la finalización del pod según el caso:
   - **Stop** → si se procesarán más PDFs en otra sesión (se factura solo el almacenamiento, ~$0.011/hr o 0.27/día).
   - **Terminate** (ícono de papelera) → si el proyecto finalizó por completo (facturación $0.00).

## Variables de entorno

| Variable | Valores | Descripción |
|---|---|---|
| `DEBUG_MODE` | `1` / `0` | Guarda imágenes de debug en `data/processed/<sha256>/` |
| `OLLAMA_HOST` | URL | Endpoint del servidor Ollama (default interno: `http://ollama:11434`) |
| `CLEAN_SCANS` | `1` / `0` | Activa pre-procesamiento de imagenes antes de que el modelo (Qwen2.5-VL) analice el documento.
| `CLEAN_STRATEGY` | `fast` / `robust` | Estrategia de limpieza cuando `CLEAN_SCANS=1`: `fast` prioriza costo CPU, `robust` prioriza calidad (deskew + OCR forzado). |


## Notas
- `src/telemetry.py` expone el decorador `@profile_time` para medir tiempos de ejecución de funciones críticas.
- El LLM nunca escribe directamente en el CSV; Pydantic es la barrera de validación.