import json
import os

from src.batch_processor import process_batch

INPUT_DIR = "data/raw"
MASTER_PDF_PATH = "data/template/master_template.pdf"
TEMPLATE_JSON = "template_mapping.json"


def _print_error(message: str) -> None:
    print(f"Error: {message}")


def main() -> None:
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
