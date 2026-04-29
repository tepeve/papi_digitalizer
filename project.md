# PAPI Digitalizer — Project Notes (`gpu-batch`)

Documento interno de seguimiento del proyecto. Registra el estado actual, los cambios realizados respecto a la rama `main` y las tareas pendientes.

---

## Descripción

Pipeline batch para digitalizar encuestas PAPI (SNEEP 2) usando:
- Alineamiento de páginas por ORB (OpenCV).
- Reconocimiento de campos OMR / ICR / TABLE_ICR.
- Modelo multimodal **Qwen2.5-VL 7B** vía Ollama para interpretación visual.
- Validación de salida con Pydantic.
- Persistencia de resultados en CSV (`sneep_backup.csv`).

Esta rama (`gpu-batch`) está pensada para correr en instancias GPU remotas (RunPod u otras VMs con CUDA) donde no hay entorno gráfico disponible.

---

## Cambios realizados respecto a `main`

### Infraestructura (Docker)

**`Dockerfile`**
- Imagen base mantenida: `nvidia/cuda:12.2.0-base-ubuntu22.04`.
- **Eliminadas** las dependencias de GUI que solo eran necesarias para el ROI labeler interactivo: `libqt5gui5`, `libsm6`, `libxext6`, `libxrender1`.
- `OLLAMA_HOST` por defecto cambiado a `http://ollama:11434` para resolución por red interna de Compose (antes apuntaba a `host.docker.internal`).

**`docker-compose.yml`**
- Añadido servicio `ollama` independiente con acceso completo a GPU (`driver: nvidia`, `count: all`).
  - Expone el puerto `11434` del host.
  - Usa un volumen nombrado (`ollama_data`) para persistir los pesos del modelo entre reinicios.
- El servicio `papi-digitalizer` ahora declara `depends_on: ollama` y se conecta al servidor LLM por la red interna del Compose (`OLLAMA_HOST=http://ollama:11434`).
- Solo el directorio `data/` se monta como volumen en el contenedor de la aplicación; el código queda embebido en la imagen.
- El contenedor `papi-digitalizer` se apaga solo al terminar el procesamiento (sin `tail -f /dev/null`).

### Aplicación

**Eliminación del ROI Labeler (`tools/roi_labeler.py`)**
- La herramienta interactiva de definición de regiones de interés fue removida de esta rama.
- Se asume que `template_mapping.json` fue generado previamente en el entorno de desarrollo local (rama `main`) y está commiteado en el repositorio.
- Esto elimina la necesidad de un display gráfico y simplifica las dependencias del sistema.

**Eliminación de la persistencia SQLite**
- Removida la escritura en `data/output/sneep.db`.
- `src/database.py` mantiene únicamente la función `persist_results()` orientada a CSV (`sneep_backup.csv`), con lógica de append y detección de cambio de esquema.
- Reduce dependencias y simplifica el despliegue en entornos headless.

---

## Estado del pipeline

| Módulo | Estado |
|---|---|
| `src/preprocessor.py` — alineamiento ORB | ✅ Funcional |
| `src/image_utils.py` — recorte de ROIs | ✅ Funcional |
| `src/llm_engine.py` — inferencia Qwen2.5-VL | ✅ Funcional |
| `src/schemas.py` — validación Pydantic | ✅ Funcional |
| `src/database.py` — persistencia CSV | ✅ Funcional |
| `src/batch_processor.py` — orquestador | ✅ Funcional |
| `src/telemetry.py` — profiling | ✅ Funcional |
| `tools/roi_labeler.py` — UI definición de ROIs | ❌ Eliminado en esta rama |

---

## Tareas completadas

- [x] Configurar imagen base CUDA en Dockerfile.
- [x] Separar el servicio Ollama en `docker-compose.yml` con soporte GPU nativo.
- [x] Definir volumen nombrado `ollama_data` para persistir pesos del modelo.
- [x] Simplificar `database.py`: eliminar persistencia SQLite, mantener solo CSV.
- [x] Eliminar `tools/roi_labeler.py` y sus dependencias de GUI del Dockerfile.
- [x] Ajustar `OLLAMA_HOST` para resolución por red interna de Compose.
- [x] Documentar flujo de despliegue en RunPod (README + project.md).

---

## To-Do

### Inmediato

- [ ] **Validar pipeline end-to-end en RunPod** con los tres PDFs de prueba (`sneep2_caso*.pdf`).
- [ ] Verificar que `ollama pull qwen2.5vl:7b` dentro del contenedor resuelve correctamente hacia el servicio Ollama por la red interna de Compose.
- [ ] Confirmar que el volumen `ollama_data` persiste los pesos entre reinicios del pod (evitar re-descargar el modelo en cada sesión).

### Mejoras pendientes

- [ ] **Añadir healthcheck** al servicio `ollama` en `docker-compose.yml` para que `papi-digitalizer` espere a que el servidor LLM esté listo antes de iniciar (`condition: service_healthy`).
- [ ] Evaluar si vale la pena parametrizar el nombre del modelo (`OLLAMA_MODEL`) como variable de entorno para facilitar pruebas con otros modelos VL.
- [ ] Revisar si `pymupdf4llm` puede eliminarse de `pyproject.toml` dado que no se usa en el pipeline actual.
- [ ] Agregar manejo de señal `SIGTERM` en `main.py` para que el contenedor se cierre limpiamente si el pod es detenido manualmente.

### Futuro (post-validación)

- [ ] Reintegrar opcionalmente la persistencia SQLite como feature opt-in vía variable de entorno (`ENABLE_DB=1`).
- [ ] Publicar imagen pre-construida en Docker Hub / GHCR para evitar el `--build` en cada despliegue.
- [ ] Implementar reintentos automáticos para documentos que caen en cuarentena por timeout del LLM.

---

## Configuración de referencia para RunPod

| Parámetro | Valor |
|---|---|
| Pod name | `papi-digitalizer-qwen` |
| GPU | RTX 3090 (24 GB VRAM) |
| Template | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` |
| SSH terminal access | Activado |
| Start Jupyter notebook | Desactivado |
| Volume disk | 40 GB |

Costo de referencia: almacenamiento en estado *Stopped* ~$0.011/hr. Apagar con **Terminate** al finalizar el proyecto para llevar la facturación a $0.00.
