import json
import sys
import argparse
from src.database import persist_results

def main():
    parser = argparse.ArgumentParser(description="Recupera archivos JSON de cuarentena y los integra al CSV.")
    parser.add_argument("file_path", help="Ruta al archivo .json en la carpeta data/quarantine/")
    args = parser.parse_args()

    try:
        with open(args.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Persiste el dato validado manualmente
        persist_results([data])
        print(f"✅ Caso recuperado con éxito: {args.file_path}")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {args.file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()