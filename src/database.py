import os
from typing import Dict, Iterable, List, Optional
import pandas as pd

def _flatten_record(record: Dict[str, object], parent_key: str = "", sep: str = "_") -> Dict[str, object]:
    items: Dict[str, object] = {}
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten_record(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items

def persist_results(records: Iterable[dict], output_dir: str = "data/output") -> Optional[pd.DataFrame]:
    records_list: List[dict] = list(records)
    if not records_list:
        print("No hay registros validados para persistir.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    flattened_records = [_flatten_record(record) for record in records_list]
    df = pd.DataFrame(flattened_records)

    csv_path = os.path.join(output_dir, "sneep_backup.csv")

    modo_escritura = 'a'
    escribir_encabezado = False

    if not os.path.exists(csv_path):
        escribir_encabezado = True
        modo_escritura = 'w'
    else:
        with open(csv_path, "r", encoding="utf-8-sig") as handle:
            primer_linea = handle.readline().strip()
        
        if primer_linea:
            columnas_existentes = primer_linea.split(";")
            if set(columnas_existentes) != set(df.columns):
                print(
                    "⚠️ Esquema de CSV no coincide con las columnas actuales. "
                    "Se sobrescribirá el archivo completo."
                )
                modo_escritura = 'w'
                escribir_encabezado = True

    df.to_csv(csv_path, mode=modo_escritura, header=escribir_encabezado, index=False, encoding='utf-8-sig', sep=';')
    
    return df