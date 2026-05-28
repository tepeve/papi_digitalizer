#!/usr/bin/env python3
"""Interactive ROI labeling tool for template_mapping.json."""

import json
import os
from typing import Any, Dict, List

import cv2
import numpy as np
from pdf2image import convert_from_path

MASTER_PDF_PATH = "data/template/master_template.pdf"
OUTPUT_JSON_PATH = "template_mapping.json"

DEFAULT_TYPE = "ICR"
ROI_COLOR = (0, 200, 0)
ROI_THICKNESS = 2
DISPLAY_MAX_HEIGHT = 900


def _load_pdf_pages(pdf_path: str) -> List[Any]:
    pages = convert_from_path(pdf_path)
    page_arrays = []
    for page in pages:
        page_array = np.array(page)
        page_arrays.append(cv2.cvtColor(page_array, cv2.COLOR_RGB2BGR))
    return page_arrays


def _prompt_field_metadata(page_number: int) -> Dict[str, Any]:
    field_id = input("field_id: ").strip()
    if not field_id:
        raise ValueError("field_id is required")

    field_type = input(f"type (default {DEFAULT_TYPE}): ").strip().upper() or DEFAULT_TYPE
    if field_type not in {"ICR", "OMR", "TABLE_ICR"}:
        raise ValueError("type must be ICR, OMR, or TABLE_ICR")

    group = input("group (optional, blank for null): ").strip()
    if group == "":
        group = None

    return {
        "field_id": field_id,
        "page": page_number,
        "type": field_type,
        "group": group,
    }


def _draw_rois(image, fields: List[Dict[str, Any]]) -> Any:
    canvas = image.copy()
    for field in fields:
        x, y, w, h = field["roi"]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), ROI_COLOR, ROI_THICKNESS)
    return canvas


def _init_output(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "metadata": metadata,
        "fields": [],
    }


def _print_table(fields: List[Dict[str, Any]]) -> None:
    print(f"\n{'-'*95}")
    print(f"{'FIELD_ID':<30} | {'PAGE':<4} | {'TYPE':<10} | {'GROUP':<15} | {'ROI'}")
    print(f"{'-'*95}")
    for f in fields:
        grp = str(f.get("group")) if f.get("group") is not None else "null"
        print(f"{f['field_id']:<30} | {f['page']:<4} | {f['type']:<10} | {grp:<15} | {f['roi']}")
    print(f"{'-'*95}\n")


def run_new_mode(pages: List[Any], reference_resolution: Dict[str, int]) -> None:
    metadata = {
        "form_id": "SNEEP_2",
        "reference_resolution": reference_resolution,
        "pages_count": len(pages),
    }

    output = _init_output(metadata)
    fields_by_page: Dict[int, List[Dict[str, Any]]] = {i + 1: [] for i in range(len(pages))}

    page_index = 0
    window_name = "SNEEP Labeler - Modo NEW"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 900)

    print("\nControles: n=siguiente, p=anterior, u=deshacer último ROI, q=guardar y salir")

    while True:
        page_number = page_index + 1
        page_image = pages[page_index]
        scale_factor = min(1.0, DISPLAY_MAX_HEIGHT / page_image.shape[0])
        annotated_full = _draw_rois(page_image, fields_by_page[page_number])

        if scale_factor < 1.0:
            new_width = int(page_image.shape[1] * scale_factor)
            new_height = int(page_image.shape[0] * scale_factor)
            display_img = cv2.resize(annotated_full, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            display_img = annotated_full

        cv2.imshow(window_name, display_img)
        key = cv2.waitKey(0) & 0xFF

        if key == ord("q"):
            break
        if key == ord("n"):
            page_index = min(page_index + 1, len(pages) - 1)
            continue
        if key == ord("p"):
            page_index = max(page_index - 1, 0)
            continue
        if key == ord("u"):
            if fields_by_page[page_number]:
                removed = fields_by_page[page_number].pop()
                output["fields"].remove(removed)
                print(f"Deshecho ROI para field_id={removed['field_id']} en la página {page_number}")
            else:
                print("No hay ROIs para deshacer en esta página")
            continue

        roi = cv2.selectROI(window_name, display_img, fromCenter=False, showCrosshair=True)
        x, y, w, h = [int(v) for v in roi]
        if w == 0 or h == 0:
            print("ROI vacío omitido")
            continue

        try:
            field = _prompt_field_metadata(page_number)
        except ValueError as exc:
            print(f"Metadatos inválidos: {exc}")
            continue

        inv_scale = 1.0 / scale_factor
        true_x = int(round(x * inv_scale))
        true_y = int(round(y * inv_scale))
        true_w = int(round(w * inv_scale))
        true_h = int(round(h * inv_scale))

        field["roi"] = [true_x, true_y, true_w, true_h]
        fields_by_page[page_number].append(field)
        output["fields"].append(field)
        print(f"ROI añadido para field_id={field['field_id']} en la página {page_number}")

    cv2.destroyAllWindows()

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)

    print(f"Template mapping guardado en {OUTPUT_JSON_PATH}")


def run_edit_mode(pages: List[Any]) -> None:
    if not os.path.exists(OUTPUT_JSON_PATH):
        print(f"Error: No se encontró el archivo '{OUTPUT_JSON_PATH}'. Debe usar el modo NEW primero.")
        return

    with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    fields = data.get("fields", [])

    current_page = 1

    while True:
        print("\n--- ESTADO ACTUAL DEL TEMPLATE MAPPING ---")
        _print_table(fields)

        prompt = (
            f"Ingrese el 'field_id' que desea editar "
            f"(o 'q' guardar y salir, 'n' siguiente página, 'p' anterior, 'g <num>' ir a página [{current_page}]): "
        )
        raw = input(prompt).strip()

        if raw.lower() == 'q':
            break
        if raw.lower() == 'n':
            current_page = min(current_page + 1, len(pages))
            print(f"Página actual: {current_page}")
            continue
        if raw.lower() == 'p':
            current_page = max(current_page - 1, 1)
            print(f"Página actual: {current_page}")
            continue
        if raw.lower().startswith('g '):
            parts = raw.split()
            if len(parts) >= 2:
                try:
                    gp = int(parts[1])
                    if 1 <= gp <= len(pages):
                        current_page = gp
                        print(f"Página actual: {current_page}")
                    else:
                        print("Número de página fuera de rango.")
                except ValueError:
                    print("Comando 'g' inválido. Uso: g 3")
            else:
                print("Comando 'g' inválido. Uso: g 3")
            continue

        field_id = raw

        target_field = next((f for f in fields if f["field_id"] == field_id), None)
        if not target_field:
            create_new = input(f"❌ El campo '{field_id}' no existe. ¿Desea agregarlo como un nuevo campo? (Y/N): ").strip().lower()
            if create_new == 'y':
                # sugerir la página actual como valor por defecto
                while True:
                    try:
                        raw_page = input(f"Ingrese el número de página (1 a {len(pages)}) [default {current_page}]: ").strip()
                        if raw_page == "":
                            page_number = current_page
                            break
                        page_number = int(raw_page)
                        if 1 <= page_number <= len(pages):
                            break
                        print("Número de página fuera de rango.")
                    except ValueError:
                        print("Por favor, ingrese un número entero válido.")
                
                target_field = {
                    "field_id": field_id,
                    "page": page_number,
                    "type": DEFAULT_TYPE,
                    "group": None,
                    "roi": [0, 0, 0, 0]
                }
                fields.append(target_field)
            else:
                continue

        # allow in-window navigation between pages before selecting ROI
        page_number = target_field["page"]
        page_index = page_number - 1
        edit_page_index = page_index

        window_name = f"Editando ROI: {field_id}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 800, 900)

        roi = (0, 0, 0, 0)
        scale_factor = 1.0

        print(f"\n[UI] Dentro de la ventana: n=next, p=prev, e=editar ROI en esta página, ESC=cancelar.")
        while True:
            current_page_number = edit_page_index + 1
            page_image = pages[edit_page_index]

            # fields on the currently previewed page (exclude the field being edited)
            page_fields = [f for f in fields if f["page"] == current_page_number and f["field_id"] != field_id]
            annotated_full = _draw_rois(page_image, page_fields)

            scale_factor = min(1.0, DISPLAY_MAX_HEIGHT / page_image.shape[0])
            if scale_factor < 1.0:
                new_width = int(page_image.shape[1] * scale_factor)
                new_height = int(page_image.shape[0] * scale_factor)
                display_img = cv2.resize(annotated_full, (new_width, new_height), interpolation=cv2.INTER_AREA)
            else:
                display_img = annotated_full

            title = f"Editando ROI: {field_id} (Pagina {current_page_number}/{len(pages)})"
            cv2.setWindowTitle(window_name, title)
            cv2.imshow(window_name, display_img)

            key = cv2.waitKey(0) & 0xFF
            if key == ord('n'):
                edit_page_index = min(edit_page_index + 1, len(pages) - 1)
                continue
            if key == ord('p'):
                edit_page_index = max(edit_page_index - 1, 0)
                continue
            if key == ord('e'):
                # open ROI selector on the currently previewed page
                roi = cv2.selectROI(window_name, display_img, fromCenter=False, showCrosshair=True)
                cv2.destroyWindow(window_name)
                break
            if key == 27:  # ESC
                cv2.destroyWindow(window_name)
                roi = (0, 0, 0, 0)
                break

        x, y, w, h = [int(v) for v in roi]
        if w == 0 or h == 0:
            print("⚠️  ROI vacío. Operación cancelada. Se conservan las coordenadas anteriores.")
        else:
            inv_scale = 1.0 / scale_factor
            target_field["roi"] = [
                int(round(x * inv_scale)),
                int(round(y * inv_scale)),
                int(round(w * inv_scale)),
                int(round(h * inv_scale))
            ]
            # update the field's page to the page where the ROI was drawn
            target_field["page"] = edit_page_index + 1
            print(f"ROI actualizado en page={target_field['page']} para field_id={field_id}")

        current_type = target_field.get("type", DEFAULT_TYPE)
        current_group = target_field.get("group", "")
        if current_group is None:
            current_group = "null"

        new_type = input(f"Nuevo 'type' (actual: {current_type} | Enter para mantener): ").strip().upper()
        if new_type:
            if new_type in {"ICR", "OMR", "TABLE_ICR"}:
                target_field["type"] = new_type
            else:
                print("Tipo inválido. Se mantiene el valor anterior.")

        new_group = input(f"Nuevo 'group' (actual: {current_group} | Enter para mantener, 'null' para borrar): ").strip()
        if new_group:
            if new_group.lower() == "null":
                target_field["group"] = None
            else:
                target_field["group"] = new_group

        print(f"\n✅ Campo '{field_id}' actualizado correctamente.")

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Cambios guardados exitosamente en {OUTPUT_JSON_PATH}")


def main() -> None:
    if not os.path.exists(MASTER_PDF_PATH):
        raise FileNotFoundError(f"Master PDF not found: {MASTER_PDF_PATH}")

    print("Cargando páginas del PDF maestro (esto puede demorar unos segundos)...")
    pages = _load_pdf_pages(MASTER_PDF_PATH)
    if not pages:
        raise RuntimeError("No pages found in the master PDF")

    reference_resolution = {
        "width": int(pages[0].shape[1]),
        "height": int(pages[0].shape[0]),
    }

    print("\n" + "="*40)
    print("      SNEEP 2 - ROI Labeler")
    print("="*40)
    print("1. Modo NEW  (Crear template desde cero)")
    print("2. Modo EDIT (Modificar campos específicos)")
    print("="*40)

    while True:
        choice = input("Seleccione el modo de operación (1 o 2): ").strip()
        if choice in {"1", "2"}:
            break
        print("Opción inválida. Ingrese 1 o 2.")

    if choice == "1":
        run_new_mode(pages, reference_resolution)
    elif choice == "2":
        run_edit_mode(pages)


if __name__ == "__main__":
    main()