import json
import os
import cv2
import numpy as np
from pdf2image import convert_from_path

def main():
    with open("template_mapping.json", "r", encoding="utf-8") as f:
        mapping = json.load(f)

    pages = convert_from_path("data/template/master_template.pdf")
    
    os.makedirs("data/processed", exist_ok=True)

    for page_idx, page_img in enumerate(pages):
        page_num = page_idx + 1
        img_bgr = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
        
        fields = [f for f in mapping.get("fields", []) if f.get("page") == page_num]
        
        for field in fields:
            x, y, w, h = field["roi"]
            name = field["field_id"]
            
            cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cv2.putText(img_bgr, name, (x, max(10, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        output_path = f"data/processed/roi_debug_page_{page_num}.jpg"
        cv2.imwrite(output_path, img_bgr)
        print(f"Página {page_num} guardada en {output_path}")

if __name__ == "__main__":
    main()