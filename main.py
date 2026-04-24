import argparse

from src.batch_processor import process_batch


def main():
    parser = argparse.ArgumentParser(description="Procesa un lote de imagenes SNEEP.")
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="data/raw",
        help="Directorio de entrada con imagenes.",
    )
    args = parser.parse_args()

    summary = process_batch(args.input_dir)
    if not summary:
        return

    print(
        f"Procesados: {summary['total']}, Exitosos: {summary['success']}, En Cuarentena: {summary['quarantine']}"
    )


if __name__ == "__main__":
    main()
