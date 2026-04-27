import os
from typing import Dict, Iterable, List, Optional

import pandas as pd
from sqlalchemy import create_engine, inspect, text


def _flatten_record(record: Dict[str, object], parent_key: str = "", sep: str = "_") -> Dict[str, object]:
    items: Dict[str, object] = {}
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten_record(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


def _drop_table_if_schema_mismatch(engine, table_name: str, columns: List[str]) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]
    if set(existing_columns) == set(columns):
        return

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
    print(
        "⚠️  Esquema de SQLite no coincide con las columnas actuales. "
        "Se recrea la tabla para evitar fallos."
    )

def persist_results(records: Iterable[dict], output_dir: str = "data/output") -> Optional[pd.DataFrame]:
    records_list: List[dict] = list(records)
    if not records_list:
        print("No hay registros validados para persistir.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    flattened_records = [_flatten_record(record) for record in records_list]
    df = pd.DataFrame(flattened_records)

    db_path = os.path.join(output_dir, "sneep.db")
    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    engine = create_engine(f"sqlite:///{db_path}")
    _drop_table_if_schema_mismatch(engine, "sneep_records", list(df.columns))
    df.to_sql("sneep_records", con=engine, if_exists="append", index=False)

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as handle:
            header = handle.readline().strip()
        if header:
            existing_columns = header.split(",")
            if set(existing_columns) != set(df.columns):
                print(
                    "⚠️  Esquema de CSV no coincide con las columnas actuales. "
                    "Se sobrescribira el archivo."
                )
    df.to_csv(csv_path, index=False)

    print(f"✅ Persistencia OK: {len(df)} registros -> {db_path} + {csv_path}")
    return df