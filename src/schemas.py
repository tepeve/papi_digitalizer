from typing import List, Optional

from pydantic import BaseModel


class StaffRow(BaseModel):
    categoria: str
    masculino: Optional[int] = 0
    femenino: Optional[int] = 0
    total: Optional[int] = 0


class PopulationRow(BaseModel):
    situacion_legal: str
    provincial_masc: Optional[int] = 0
    provincial_fem: Optional[int] = 0
    nacional_masc: Optional[int] = 0
    nacional_fem: Optional[int] = 0
    federal_masc: Optional[int] = 0
    federal_fem: Optional[int] = 0
    total: Optional[int] = 0


class SneepPage1(BaseModel):
    provincia: Optional[str] = None
    reparticion: Optional[str] = None
    nombre_establecimiento: Optional[str] = None
    tipo_establecimiento: Optional[str] = None
    domicilio_cp: Optional[str] = None
    telefono_fax: Optional[str] = None
    email: Optional[str] = None
    responsable_estadistica: Optional[str] = None
    capacidad_fisica_alojamiento: Optional[int] = 0
    alojados_celdas_individuales: Optional[int] = 0
    alojados_locales_colectivos: Optional[int] = 0
    dotacion_personal: List[StaffRow]
    poblacion_por_jurisdiccion: List[PopulationRow]
