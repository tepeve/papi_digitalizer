import os
import stat
import subprocess
from typing import Optional

from PIL import Image


def limpiar_y_enderezar(ruta_imagen: str, output_dir: str) -> Optional[str]:
    print("1. Preparando imagen y ejecutando OCRmyPDF...")
    os.makedirs(output_dir, exist_ok=True)

    # --- INICIO DEL PREPROCESAMIENTO (Normalizacion de Transparencias/PNG) ---
    img_segura = os.path.join(output_dir, "input_seguro.jpg")
    img = Image.open(ruta_imagen)

    # Chequeamos si la imagen tiene canal alfa (RGBA, LA) o paleta con transparencia
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        print("   [!] Canal alfa detectado. Normalizando a RGB puro con fondo blanco...")
        # Creamos un lienzo blanco del mismo tamano
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        # Pegamos la imagen original usando su propio canal de transparencia como mascara
        if img.mode == "RGBA":
            fondo.paste(img, mask=img.split()[3])
        else:
            fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])

        fondo.save(img_segura, "JPEG", quality=100)
        ruta_imagen = img_segura  # OCRmyPDF ahora usara esta version segura

    elif img.mode != "RGB" or ruta_imagen.lower().endswith(".png"):
        print("   [!] Normalizando formato de imagen a JPG estandar...")
        img.convert("RGB").save(img_segura, "JPEG", quality=100)
        ruta_imagen = img_segura
    # --- FIN DEL PREPROCESAMIENTO ---

    # --- INICIO DEL HACK: Crear un 'jbig2' falso ---
    fake_jbig2_path = os.path.join(output_dir, "jbig2")
    with open(fake_jbig2_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\n")
        f.write("echo 'jbig2enc 0.29'\n")

    os.chmod(fake_jbig2_path, os.stat(fake_jbig2_path).st_mode | stat.S_IEXEC)

    my_env = os.environ.copy()
    my_env["PATH"] = os.path.abspath(output_dir) + os.pathsep + my_env.get("PATH", "")
    # --- FIN DEL HACK ---

    output_pdf_path = os.path.join(output_dir, "limpio.pdf")
    comando = [
        "ocrmypdf",
        "--image-dpi",
        "300",
        "--optimize",
        "0",
        "--deskew",
        "--clean",
        "--force-ocr",
        "--language",
        "spa",
        ruta_imagen,  # <-- Ahora pasamos la imagen normalizada
        output_pdf_path,
    ]

    try:
        subprocess.run(comando, env=my_env, capture_output=True, text=True, check=True)
        print("✅ PDF limpio y enderezado con exito.")
        return output_pdf_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en OCRmyPDF (Codigo {e.returncode}):")
        print(f"--- DETALLE DEL ERROR ---\n{e.stderr}")
        return None
