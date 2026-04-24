# PAPI Digitalizer (Qwen2.5-VL)

Pipeline para digitalizar encuestas PAPI (SNEEP) con OCR + vision LLM.

## Requisitos del sistema
- ocrmypdf
- tesseract-ocr-spa
- ghostscript
- unpaper
- poppler-utils

Ejemplo (Ubuntu):
sudo apt update
sudo apt install ocrmypdf tesseract-ocr-spa ghostscript unpaper poppler-utils -y

## Instalacion
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

## Uso rapido
- Notebook: src/prototype_1.ipynb
- Script: main.py

## Notas
- El pipeline usa OCRmyPDF + PyMuPDF4LLM + Qwen2.5-VL via Ollama.