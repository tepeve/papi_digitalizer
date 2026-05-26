# Last Sprint Summary (Contexto para manana)

Fecha: 2026-05-21
Proyecto: papi_digitalizer

## Objetivo general
Extender el pipeline para soportar el nuevo formulario DIAG_INTEGRAL con estrategia de Macro-ROIs, manteniendo compatibilidad con formularios legacy.

## Tareas completadas

### 1) Generacion automatica de template_mapping
- Se creo el script: src/tools equivalent en proyecto: tools/generate_template_mapping.py.
- El script lee programaticamente src/schemas.py (via AST) y genera template_mapping.json.
- Estructura generada:
  - metadata.form_id = DIAG_INTEGRAL
  - metadata.reference_resolution = { width: 1700, height: 2200 }
  - metadata.pages_count = 16
  - fields con tipos: multiple_choice_block, single_choice_block, text, number, date
- Consolidaciones obligatorias implementadas:
  - p16_s2_bloque
  - p17_s2_bloque
  - p26_s3_bloque
  - p45_s5_bloque
  - p47_s6_bloque
  - p74_s8_bloque
  - p83_s9_bloque
- Validacion de cobertura ejecutada:
  - missing = 0
  - extra = 0

### 2) Prompts dinamicos en motor LLM
- Archivo modificado: src/llm_engine.py
- Funcion modificada: process_icr_batch
- Cambio:
  - Instrucciones dinamicas segun record.get("type", "text")
  - Texto exacto para multiple_choice_block y single_choice_block segun requerimiento
  - Fallback para text/number/date mantiene transcripcion estricta
- Restriccion respetada:
  - No se modifico process_table_batch
  - No se elimino ni altero la logica de TABLE_ICR en esa funcion

### 3) Transformer dedicado para Macro-ROIs
- Archivo nuevo: src/transformers.py
- Clase creada: MacroRoiTransformer
- Metodo principal:
  - transform_aggregated_data(aggregated_data, template_mapping)
- Comportamiento implementado:
  - Recorre template_mapping["fields"]
  - Para multiple_choice_block:
    - Lee field_id consolidado
    - Usa target_mappings
    - Expande a campos atomicos Si/No con matching normalizado
    - Elimina el field_id consolidado del resultado final
  - Para single_choice_block:
    - Limpieza del string
    - Mapeo directo/canonico cuando hay target_mappings
- Fix aplicado durante pruebas:
  - Se corrigio un bug para no forzar "No" en destinos si el campo macro no estaba presente en aggregated_data.

### 4) Integracion en pipeline principal
- Archivo modificado: src/pipeline.py
- Cambios clave en process_document:
  - Import de MacroRoiTransformer
  - Inyeccion de middleware justo despues de aggregate_results:
    - transformer = MacroRoiTransformer()
    - aggregated = transformer.transform_aggregated_data(aggregated, template_mapping)
  - Routing de tipos nuevos al lote ICR:
    - multiple_choice_block
    - single_choice_block
    - text, number, date
  - Validacion dinamica por form_id:
    - form_id == DIAG_INTEGRAL -> valida con DiagnosticoIntegral
    - caso contrario -> valida con SneepCompleto (fallback a schemas_old si hace falta)
- Restriccion respetada:
  - Se mantuvo intacta la logica de alineamiento ORB
  - Se mantuvo process_table_batch/TABLE_ICR

### 5) Propagacion de metadata de mapeo
- Archivo modificado: src/image_utils.py
- Cambio:
  - extract_rois ahora propaga target_mappings desde template fields hacia los records, para que llegue al pipeline/transformer.

## Pruebas realizadas

### A) Pruebas de estructura y cobertura del mapping
- Comprobacion de metadata y bloques obligatorios: OK
- Cobertura de fields vs DiagnosticoIntegral: OK (missing 0 / extra 0)

### B) Smoke test integral DIAG_INTEGRAL (con mocks)
- Flujo probado de punta a punta en process_document:
  - conversion de paginas mockeada
  - alineamiento ORB mockeado
  - ROI extraction mockeada
  - salida LLM mockeada
  - transformacion MacroROI activa
  - validacion Pydantic DIAG_INTEGRAL activa
- Resultado final: INTEGRATION_SMOKE_OK

### C) Smoke test compatibilidad legacy (con mocks)
- form_id = SNEEP_2
- Validacion legacy activa
- Resultado final: LEGACY_COMPAT_SMOKE_OK

## Archivos creados/modificados relevantes
- tools/generate_template_mapping.py (nuevo)
- template_mapping.json (regenerado para DIAG_INTEGRAL)
- src/llm_engine.py (prompts dinamicos)
- src/transformers.py (nuevo)
- src/pipeline.py (middleware + validacion dinamica + routing ICR)
- src/image_utils.py (propagacion target_mappings)

## Estado actual
- Funcionalidad Macro-ROI implementada e integrada.
- Compatibilidad legacy validada en smoke test.
- Queda pendiente validacion con documentos reales (sin mocks) contra Ollama en entorno completo.

## Riesgos / notas tecnicas
- En entornos sin dependencias nativas instaladas (cv2, pdf2image, etc.) no corre pipeline real.
- El entorno temporal .uv-e2e se uso para ejecutar pruebas integrales con dependencias.
- Existe ruido en el repositorio por cambios previos no relacionados; no se revirtieron cambios ajenos.

## Como retomar manana (pasos sugeridos)
1. Verificar que Ollama este levantado y modelo disponible (qwen2.5vl:7b).
2. Ejecutar una corrida real con 1 PDF de data/raw y template actual.
3. Revisar salida validada y cuarentena.
4. Ajustar labels target_mappings si hay desalineaciones de OCR/VLM en multiples opciones.
5. Si todo esta bien, correr lote pequeno y monitorear errores de validacion.

## Comandos utiles de continuidad
- Generar mapping:
  - /usr/bin/python3 tools/generate_template_mapping.py
- Ejecutar pipeline (segun setup del entorno):
  - python main.py
- Verificacion rapida de cobertura (ya usada en sprint):
  - script AST + json para missing/extra

---
Resumen ejecutivo: se implemento el soporte completo de Macro-ROIs para DIAG_INTEGRAL (generacion de mapping, prompts dinamicos, transformacion de bloques a campos atomicos e integracion en pipeline) y se verifico con pruebas integrales de humo, incluyendo compatibilidad legacy.
