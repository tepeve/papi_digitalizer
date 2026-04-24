# Documentación del Proyecto: Digitalizador PAPI - SNEEP 2

## 📌 Resumen del Proyecto
Este proyecto es un pipeline para la digitalización automatizada de encuestas PAPI (Paper-and-Pencil Interviewing). Para el prototipo de desarrollo se han utilizado los cuestionarios del **Sistema Nacional de Estadísticas sobre Ejecución de la Pena (SNEEP 2)**. 

Se basa en una arquitectura de procesamiento 100% local y privada, aprovechando la potencia de procesamiento multicore (CPU) mediante modelos multimodales (Qwen2.5-VL 7B) y herramientas tradicionales de visión computacional.


---
papi-digitalizer-qwen/
├── data/
│   ├── raw/                 # Aquí van los escaneos nuevos (.jpg, .png)
│   ├── processed/           # Salidas por imagen (ej: data/processed/<stem>/)
│   ├── quarantine/          # Imágenes que Pydantic rechazó al intentar validar las interpretaciones de qwen
│   └── output/              # Bases de datos SQLite o .csv generados
├── src/
│   ├── __init__.py
│   ├── config.py            # Rutas, modelo a usar, resoluciones (1008, 28)
│   ├── schemas.py           # Tus clases de Pydantic
│   ├── preprocessor.py      # Tu código de Pillow y OCRmyPDF
│   ├── image_utils.py        # Preparación de imagen (1008px, múltiplos de 28)
│   ├── llm_engine.py        # La llamada a Ollama y armado de prompts
│   ├── pipeline.py          # Orquestación de process_single_image()
│   ├── batch_processor.py   # Lote secuencial + cuarentena + resumen
│   └── database.py          # Persistencia (SQLite + CSV)
├── main.py                  # Punto de entrada para batch (data/raw/)
├── pyproject.toml
└── project.md

---

## 🏗️ Workflow y Arquitectura del Pipeline

El flujo de trabajo actual consta de 5 etapas fundamentales:

1. **Ingesta y Normalización de Imágenes: ver preprocessor.py** - Recepción de formularios escaneados en formatos mixtos (`.jpg`, `.png`).
   - Detección y aplanado de canales Alfa (transparencias) convirtiendo imágenes RGBA a RGB puro con fondo blanco mediante `Pillow` para evitar fallos en el motor OCR.
2. **Preprocesamiento y Limpieza (OCRmyPDF): ver preprocessor.py**
   - Enderezamiento de páginas torcidas (`--deskew`).
   - Limpieza de ruido visual y manchas del escáner (`--clean`).
   - *Bypass* de optimización (`--optimize 0`) para acelerar el procesamiento y evitar dependencias rotas en WSL (`jbig2`).
3. **Extracción de Layout y Optimización Visual Avanzada: ver image_utils.py**
   - **PyMuPDF4LLM:** Extracción de la estructura esqueleto en formato Markdown para guiar al modelo de lenguaje.
   - **Ingeniería de Tensores (Anti-Ollama Bypass):** Redimensionamiento inteligente de la imagen para evitar el colapso del motor C++ de Ollama (`GGML_ASSERT`). Se limita el borde máximo a **1008 píxeles** y se fuerza matemáticamente a que ancho y alto sean **múltiplos exactos de 28** (tamaño del parche visual del modelo), evitando que el cliente auto-redimensione y desalinee la matriz.
4. **Inferencia IA Híbrida (Qwen2.5-VL 7B): ver llm_engine.py**
   - Procesamiento de la imagen completa optimizada junto con el prompt estructurado y el layout base.
   - Extracción combinada de marcas OMR (casillas de verificación) e ICR (texto manuscrito libre).
5. **Validación Estricta y Estructuración (Pydantic): ver schemas.py + ver llm_engine.py + batch_processor.py**
   - Parseo del JSON crudo devuelto por la IA.
   - Validación de tipos de datos, llaves requeridas y completitud del formulario.
   - Transformación a diccionario nativo de Python, listo para ingesta en bases de datos.

---

## 📦 Librerías y Dependencias

### Entorno de Desarrollo
* Gestor de paquetes y entornos virtuales: **`uv`** (extremadamente rápido, reemplazo de pip/conda).

### Python Stack
* **`ollama`:** Cliente de conexión con el servidor local del modelo multimodal.
* **`pydantic`:** Motor central de esquematización y validación de datos (contrato de datos).
* **`pymupdf4llm` & `pymupdf`:** Extracción nativa de estructura de documentos a Markdown.
* **`pdf2image` & `Pillow`:** Manipulación de imágenes, aplanado de canales alfa, down-sampling (LANCZOS) e interconexión con el sistema de archivos.
* **`img2pdf`:** Conversión sin pérdida térmica de imágenes a PDF.
* *Pendientes de uso intensivo:* `pandas` (tabulación final) y `sqlalchemy` (inserción en RDBMS).

### Dependencias de Sistema (WSL/Ubuntu)
* `ocrmypdf`, `tesseract-ocr-spa`, `ghostscript`, `unpaper` (Limpieza de imagen).
* `poppler-utils` (Motor detrás de pdf2image).

---

## ✅ Tareas Realizadas (Hasta Ahora)

- [x] Configuración del entorno de alto rendimiento usando `uv`.
- [x] Instalación y despliegue del modelo **Qwen2.5-VL 7B** vía CLI de Ollama.
- [x] Diseño e implementación del esquema de datos jerárquico para la Hoja 1 del SNEEP 2 utilizando `Pydantic`.
- [x] Construcción del pipeline de preprocesamiento (corrección de errores de binarios de Linux `jbig2` mediante inyección de variables de entorno).
- [x] Integración de `PyMuPDF4LLM` para otorgar contexto estructural al LLM.
- [x] **Resolución de Canal Alfa:** Normalización automática de PNGs sintéticos y escaneos con transparencias a RGB sólido.
- [x] **Ingeniería de Tensores Visuales:** Solución definitiva al error `GGML_ASSERT` fijando dimensiones máximas seguras (1008px) y alineación de parches visuales (múltiplos de 28) para bypass del auto-resize de Ollama.
- [x] **Refactorización a módulos:** `schemas.py`, `preprocessor.py`, `image_utils.py`, `llm_engine.py`, `pipeline.py`.
- [x] **Pipeline 1 imagen funcionando:** `main.py` ejecuta `process_single_image()` con salida validada.
- [x] **Salidas por imagen:** artefactos en `data/processed/<stem>/`.
- [x] **Batch secuencial:** `batch_processor.py` recorre `data/raw/` con tqdm y maneja cuarentena.
- [x] **Persistencia ETL:** `database.py` exporta a `data/output/sneep.db` y `data/output/sneep_backup.csv`.
- [x] **Serialización JSON:** listas anidadas se guardan como JSON en SQLite/CSV.

---

## 🚀 Próximos Pasos (Roadmap)

1. **Validaciones Lógicas Complejas (Pydantic `@model_validator`):**
   - Implementar chequeos cruzados matemáticos (ej: Verificar que la suma de situaciones legales provinciales/nacionales coincida con los totales verticales y horizontales).
   - Generar un campo de "Alertas" o `flag_revision_manual` cuando la IA detecte inconsistencias o sumas incorrectas en el papel original.
2. **Identificador de pieza procesada:**
   - Agregar nombre de archivo u otro identificador como columna en CSV y SQLite.
3. **Multipagina (formularios extendidos):**
   - Agrupar campos de varias paginas en un unico JSON y registros de salida cuando corresponda a una misma entrevista.
4. **Optimización de inferencia:**
   - Evaluar si el modelo debe interpretar solo campos con escritura/marcas en lugar de todo el texto.
5. **Contenerización:**
   - Definir Dockerfile/compose y dependencias de sistema para despliegue reproducible.
6. **Interfaz de usuario:**
   - Diseñar una UI minima para carga, seguimiento y revision.

---

## 📏 Reglas de Codificación y Buenas Prácticas

1. **Contratos de Datos Estrictos:** El LLM **nunca** escribe directamente en la base de datos. Pydantic es la barrera inquebrantable. Todos los campos inciertos o vacíos deben inicializarse con valores por defecto (ej: `0` para enteros).
2. **Prompts Restrictivos (System Prompts):**
   - Siempre proveer el esquema JSON inyectado directamente en el prompt (`SneepPage1.model_json_schema()`).
   - Utilizar reglas en mayúsculas y directivas absolutas ("DEBES devolver el número 0. NUNCA devuelvas ''").
3. **Gestión Eficiente del Hardware (CPU First):**
   - Las imágenes que van al LLM deben estar en la resolución mínima viable para ICR. El límite arquitectónico está fijado en un **máximo de 1008px por lado**, siendo estrictamente **múltiplos de 28** para no quebrar la atención de parches del modelo multimodal.
   - El preprocesamiento pesado (limpieza de fondo, enderezamiento, conversión) debe hacerse fuera del LLM utilizando herramientas optimizadas en C++ como `ocrmypdf` y librerías de Python como `Pillow`.
4. **Resiliencia del Entorno e Insumos:**
   - Aislar los errores del sistema subyacente (WSL/Ubuntu). Si una dependencia externa falla, interceptar el error o aplicar by-pass dinámicos (`env["PATH"]`).
   - Nunca confiar en el formato de entrada de la imagen. Siempre verificar y normalizar el `mode` de la imagen (removiendo canales Alfa `RGBA` a `RGB`) antes de iniciar el OCR.