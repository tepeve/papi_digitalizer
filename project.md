# Documentación del Proyecto: Digitalizador PAPI - SNEEP 2

## 📌 Resumen del Proyecto
Este proyecto es un pipeline para la digitalización automatizada de encuestas PAPI (Paper-and-Pencil Interviewing). Para el prototipo de desarrollo se han utilizado los cuestionarios del **Sistema Nacional de Estadísticas sobre Ejecución de la Pena (SNEEP 2)**. 

Se basa en una arquitectura de procesamiento 100% local y privada, aprovechando la potencia de procesamiento multicore (CPU) mediante modelos multimodales (Qwen2.5-VL 7B) y herramientas tradicionales de visión computacional.


---
papi-digitalizer-qwen/
├── data/
│   ├── raw/                 # PDFs de entrada
│   ├── template/            # master_template.pdf
│   ├── processed/           # Artefactos de debug por documento (data/processed/<sha256>/)
│   ├── quarantine/          # PDFs con errores + *_error.txt + *_data.json
│   └── output/              # SQLite/CSV generados
├── src/
│   ├── batch_processor.py   # Lote secuencial de PDFs + cuarentena + resumen
│   ├── database.py          # Persistencia (SQLite + CSV)
│   ├── image_utils.py       # Alineamiento ORB + extracción de ROIs + OMR
│   ├── llm_engine.py        # ICR por lotes (ROIs) vía Ollama/Qwen
│   ├── pipeline.py          # Orquestación por PDF multipágina
│   ├── preprocessor.py      # OCRmyPDF + normalización de transparencia (utilidad)
│   └── schemas.py           # Esquemas Pydantic
├── tools/
│   └── roi_labeler.py       # Etiquetador interactivo de ROIs
├── template_mapping.json    # Mapeo de ROIs por página
├── main.py                  # Entry point batch (data/raw/)
├── pyproject.toml
└── project.md

---

## 📦 Librerías y Dependencias

### Entorno de Desarrollo
* Gestor de paquetes y entornos virtuales: **`uv`** (extremadamente rápido, reemplazo de pip/conda).

### Python Stack
* **`ollama`:** Cliente de conexión con el servidor local del modelo multimodal.
* **`opencv-python`:** Alineamiento ORB, extracción de ROIs y OMR.
* **`pdf2image` & `Pillow`:** Conversión de PDF a imágenes y normalización de entradas.
* **`pydantic`:** Esquemas y validación estricta de datos.
* **`pandas` + `sqlalchemy`:** Persistencia a SQLite/CSV.
* **`tqdm`:** Barra de progreso en batch.
* **`img2pdf`:** Utilidad de conversión sin recomprimir (uso auxiliar).
* **`pymupdf4llm`:** Dependencia declarada (no usada en el pipeline actual).

### Dependencias de Sistema (WSL/Ubuntu)
* `ocrmypdf`, `tesseract-ocr-spa`, `ghostscript`, `unpaper` (Limpieza de imagen).
* `poppler-utils` (Motor detrás de pdf2image).

---

## 🏗️ Workflow y Arquitectura del Pipeline

El flujo de trabajo actual consta de 6 etapas fundamentales:

1. **Ingesta de PDFs y plantilla maestra: ver main.py + pipeline.py**
   - Entrada principal: PDFs en `data/raw/`.
   - Plantilla maestra: `data/template/master_template.pdf`.
   - Mapeo de ROIs: `template_mapping.json` (generado con `tools/roi_labeler.py`).
2. **Alineamiento por visión (ORB): ver image_utils.py**
   - Se alinea cada página del PDF escaneado contra la plantilla maestra usando homografía.
   - En modo debug (`DEBUG_MODE=1`) se guardan overlays y matches en `data/processed/<sha256>/`.
3. **Extracción de ROIs (OMR + ICR + TABLE_ICR): ver image_utils.py**
   - Se recortan campos usando el mapeo de ROIs.
   - OMR: umbralización + conteo de píxeles blancos.
   - ICR: recortes de campos individuales listos para inferencia por lote.
   - TABLE_ICR: recorte de tabla completa para inferencia estructurada en una sola pasada.
4. **Inferencia ICR/TABLE_ICR por lote (Qwen2.5-VL 7B): ver llm_engine.py**
   - `process_icr_batch`: un solo llamado al LLM por página para transcribir todos los recortes ICR individuales. Respuesta estricta en JSON con los `field_id` definidos.
   - `process_table_batch`: un llamado al LLM por cada tabla (`TABLE_ICR`), usando el esqueleto Pydantic del modelo correspondiente (`TABLE_MODEL_REGISTRY`) como plantilla JSON. Devuelve valores numéricos directamente en la estructura del cuadro.
5. **Agregación y validación (Pydantic): ver pipeline.py + schemas.py**
   - Se agregan resultados por `group` y se valida con `SneepCompleto`.
   - Si hay errores, se devuelve payload con `errors` + datos crudos.
6. **Persistencia y cuarentena: ver batch_processor.py + database.py**
   - Registros válidos -> `data/output/sneep.db` + `data/output/sneep_backup.csv`.
   - Fallos -> `data/quarantine/` con PDF y trazas.

---

## 🧭 Cómo generar template_mapping.json

1. Colocar la plantilla maestra en `data/template/master_template.pdf`.
2. Ejecutar el labeler interactivo:

```bash
python tools/roi_labeler.py
```
*Importante:* La UI en Ubuntu-WSL suele tener conflictos con los drivers de video de windows, por lo que una estrategia más simple es correr roi_labeler.py directamente en windows (es un script standalone).

3. Usar los controles del visor:
   - `n` pagina siguiente, `p` pagina anterior, `u` deshacer ultimo ROI, `q` salir y guardar.
4. Para cada ROI, completar `field_id`, `type` (ICR/OMR/TABLE_ICR) y `group` (vacío para null).
5. Al salir, se genera `template_mapping.json` en la raiz del repo.
6. Verificar que `metadata.pages_count` y `reference_resolution` coincidan con la plantilla.

---

## ✅ Tareas Realizadas (Hasta Ahora)

- [x] Configuración del entorno de alto rendimiento usando `uv`.
- [x] Instalación y despliegue del modelo **Qwen2.5-VL 7B** vía CLI de Ollama.
- [x] Diseño e implementación del esquema de datos jerárquico para el formulario completo del SNEEP 2 utilizando `Pydantic` (10 cuadros: dotación, población, ingresos, egresos, niños, alteraciones, suicidios, fallecidos, lesiones).
- [x] **Normalización de texto:** validador `normalize_text` (NFKD + uppercase) aplicado a todos los campos de texto en `SneepCompleto`.
- [x] Construcción del pipeline de preprocesamiento (OCRmyPDF + normalización de transparencias con `jbig2` fake).
- [x] **Labeler de ROIs:** herramienta interactiva `tools/roi_labeler.py` para generar `template_mapping.json`.
- [x] **Alineamiento por ORB:** registro de páginas escaneadas contra la plantilla maestra.
- [x] **Extracción híbrida OMR/ICR:** OMR por umbralización + ICR por recortes.
- [x] **ICR por lote:** un llamado al LLM por página con múltiples ROIs.
- [x] **TABLE_ICR en una sola pasada:** `process_table_batch` + `TABLE_MODEL_REGISTRY` para inferir tablas completas enviando el esqueleto Pydantic como plantilla JSON al LLM.
- [x] **Pipeline multipágina:** procesamiento de PDFs completos con validación Pydantic (OMR + ICR + TABLE_ICR por página).
- [x] **Batch secuencial de PDFs:** cuarentena + resumen.
- [x] **Persistencia ETL:** exporta a SQLite/CSV con serialización automática de campos anidados.
- [x] **`document_id` en el modelo de datos:** campo `document_id` (SHA-256 del archivo) incorporado en `SneepCompleto` y propagado a través de todo el pipeline (ROIs, aggregation, persistencia).
- [x] **Observabilidad (telemetría):** módulo `src/telemetry.py` con decorador `@profile_time` para medir y loguear el tiempo de ejecución de funciones críticas.
- [x] **Contenerización:** `Dockerfile` con imagen base CUDA (`nvidia/cuda:12.2.0-base-ubuntu22.04`) para soporte GPU + `docker-compose.yml` con volúmenes, display X11 y variable `OLLAMA_HOST` apuntando al host.

---

## 🚀 Próximos Pasos (Roadmap)

1. **Validaciones Lógicas Complejas (Pydantic `@model_validator`):**
   - Chequeos cruzados matemáticos y generación de alertas/flags.
2. **Identificador de pieza procesada:**
   - Agregar nombre de archivo u otro identificador como columna en CSV y SQLite.
3. ~~**Multipagina (formularios extendidos):**~~
   - Agrupar campos de varias paginas en un unico JSON y registros de salida por entrevista. ✅ Implementado a través de roi_labeler.py
4. ~~**Optimización de inferencia:**~~ - Evaluar lectura selectiva de campos con escritura/marcas.✅ Implementado a través del pipeline bifurcado que separa el método de interpretación a través de `field_id`, `type` (ICR/OMR/TABLE_ICR)
5. ~~**Evaluar tablas anidadas en una sola pasada:**~~ ✅ Implementado con `TABLE_ICR` + `process_table_batch`.
6. **Pipeline para formularios con multiples registros por hoja:**
   - Diseñar un flujo adaptado para SNEEP 1 u otros formularios con mas de una unidad de registro por papel.
7. ~~**Contenerización:**~~ - Dockerfile con imagen CUDA + docker-compose con volúmenes y OLLAMA_HOST. ✅
8. **Interfaz de usuario:**
   - Diseñar una UI minima para carga, seguimiento y revision.

---

## 📏 Reglas de Codificación y Buenas Prácticas

1. **Contratos de Datos Estrictos:** El LLM **nunca** escribe directamente en la base de datos. Pydantic es la barrera inquebrantable. Todos los campos inciertos o vacíos deben inicializarse con valores por defecto (ej: `0` para enteros).
2. **Prompts Restrictivos (System Prompts):**
   - Devolver SIEMPRE JSON estricto con las claves exactas de `field_id`.
   - Si un campo es ilegible, usar `null` (la validación aplica defaults cuando corresponda).
3. **Gestión Eficiente del Hardware (CPU First):**
   - Minimizar tamaño de ROIs y evitar enviar paginas completas al LLM.
   - El preprocesamiento pesado (limpieza, enderezamiento, conversión) debe hacerse fuera del LLM.
4. **Resiliencia del Entorno e Insumos:**
   - Aislar los errores del sistema subyacente (WSL/Ubuntu). Si una dependencia externa falla, interceptar el error o aplicar by-pass dinámicos (`env["PATH"]`).
   - Nunca confiar en el formato de entrada de la imagen. Siempre verificar y normalizar el `mode` de la imagen (removiendo canales Alfa `RGBA` a `RGB`) antes de iniciar el OCR.