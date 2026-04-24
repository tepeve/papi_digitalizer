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
    if "dotacion_personal" in df.columns:
        df["dotacion_personal"] = df["dotacion_personal"].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
        )
    if "poblacion_por_jurisdiccion" in df.columns:
        df["poblacion_por_jurisdiccion"] = df["poblacion_por_jurisdiccion"].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
        )

    db_path = os.path.join(output_dir, "sneep.db")
    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    engine = create_engine(f"sqlite:///{db_path}")
    df.to_sql("sneep_records", con=engine, if_exists="append", index=False)
    df.to_csv(csv_path, index=False)

    print(f"✅ Persistencia OK: {len(df)} registros -> {db_path} + {csv_path}")
    return df
