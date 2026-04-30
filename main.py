import signal
import sys
import json
import os
import logging
from src.batch_processor import process_batch

INPUT_DIR = "data/raw"
MASTER_PDF_PATH = "data/template/master_template.pdf"
TEMPLATE_JSON = "template_mapping.json"



def _print_error(message: str) -> None:
    print(f"Error: {message}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/processed/pipeline_telemetry.log")
    ]
)
LOGGER = logging.getLogger(__name__)


def handle_sigterm(signum, frame):
    LOGGER.info("Señal SIGTERM recibida. Interrumpiendo el pipeline de forma segura...")
    sys.exit(0)

def main() -> None:
    # Registrar la señal al inicio del main
    signal.signal(signal.SIGTERM, handle_sigterm)

    if not os.path.exists(TEMPLATE_JSON):
        _print_error(f"Template JSON not found: {TEMPLATE_JSON}")
        return

    if not os.path.exists(MASTER_PDF_PATH):
        _print_error(f"Master PDF not found: {MASTER_PDF_PATH}")
        return

    os.makedirs(INPUT_DIR, exist_ok=True)

    with open(TEMPLATE_JSON, "r", encoding="utf-8") as handle:
        template_mapping = json.load(handle)

    summary = process_batch(INPUT_DIR, MASTER_PDF_PATH, template_mapping)
    if not summary:
        return

    print(
        "Total processed: {total} | Successes: {success} | Quarantines: {quarantine}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
