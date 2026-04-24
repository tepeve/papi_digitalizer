import json
import os
from typing import Iterable, List, Optional

import pandas as pd
from sqlalchemy import create_engine

def persist_results(records: Iterable[dict], output_dir: str = "data/output") -> Optional[pd.DataFrame]:
    records_list: List[dict] = list(records)
    if not records_list:
        print("No hay registros validados para persistir.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame(records_list)

    # Detección y serialización automática de diccionarios/listas anidadas a JSON
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].apply(
                lambda val: json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else val
            )

    db_path = os.path.join(output_dir, "sneep.db")
    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql("sneep_records", con=engine, if_exists="append", index=False)
    df.to_csv(csv_path, index=False)

    print(f"✅ Persistencia OK: {len(df)} registros -> {db_path} + {csv_path}")
    return df