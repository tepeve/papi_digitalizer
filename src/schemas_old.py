import unicodedata
from typing import Optional

from pydantic import BaseModel, Field, field_validator

class GeneroTotalRow(BaseModel):
    masculino: int = 0
    femenino: int = 0
    total: int = 0

class NinosRow(BaseModel):
    ninas: int = 0
    ninos: int = 0
    total: int = 0

class AlteracionRow(BaseModel):
    danos: int = 0
    rehenes: int = 0
    heridos_muertos: int = 0
    total: int = 0

class JurisdiccionFila(BaseModel):
    provincial_masc: int = 0
    provincial_fem: int = 0
    nacional_masc: int = 0
    nacional_fem: int = 0
    federal_masc: int = 0
    federal_fem: int = 0
    total: int = 0

class SituacionLegalFila(BaseModel):
    procesados_masc: int = 0
    procesados_fem: int = 0
    condenados_masc: int = 0
    condenados_fem: int = 0
    inimputables_masc: int = 0
    inimputables_fem: int = 0
    contraventores_masc: int = 0
    contraventores_fem: int = 0
    otros_masc: int = 0
    otros_fem: int = 0
    total: int = 0

def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())
    
    if not normalized:
        return None
        
    return normalized.upper()

class CuadroDotacion(BaseModel):
    dotacion_oficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_suboficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_cadetes: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_personal_civil: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

class CuadroPoblacion(BaseModel):
    procesados: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    condenados: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    inimputables: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    contraventores: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    otros: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    total: JurisdiccionFila = Field(default_factory=JurisdiccionFila)

class CuadroIngresos(BaseModel):
    ingresos_ultimo_ano: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

class CuadroEgresosProcesados(BaseModel):
    absolucion: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    cambio_situacion: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    entrega_padres: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    evasion: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    excarcelacion: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    fallecimiento: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    falta_merito: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    fuga: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    indulto: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    sobreseimiento: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    traslados: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    vigilada: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    no_especificados: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    otros_motivos: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    total: JurisdiccionFila = Field(default_factory=JurisdiccionFila)

class CuadroEgresosCondenados(BaseModel):
    agotamiento: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    evasion: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    fallecimiento: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    fuga: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    indulto: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    lib_condicional_13: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    lib_condicional_53: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    lib_asistida_54: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    prision_domiciliaria_33: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    traslados: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    otros_motivos: JurisdiccionFila = Field(default_factory=JurisdiccionFila)
    total: JurisdiccionFila = Field(default_factory=JurisdiccionFila)

class CuadroNinos(BaseModel):
    ninos_hasta_1: NinosRow = Field(default_factory=NinosRow)
    ninos_1_a_2: NinosRow = Field(default_factory=NinosRow)
    ninos_2_a_3: NinosRow = Field(default_factory=NinosRow)
    ninos_3_a_4: NinosRow = Field(default_factory=NinosRow)
    ninos_total: NinosRow = Field(default_factory=NinosRow)

class CuadroAlteraciones(BaseModel):
    alteraciones_fuerza: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_negociacion: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_espontanea: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_total: AlteracionRow = Field(default_factory=AlteracionRow)

class CuadroSuicidios(BaseModel):
    suicidios_total: SituacionLegalFila = Field(default_factory=SituacionLegalFila)

class CuadroFallecidos(BaseModel):
    fallecidos_violencia_internos: SituacionLegalFila = Field(default_factory=SituacionLegalFila)
    fallecidos_violencia_agentes: SituacionLegalFila = Field(default_factory=SituacionLegalFila)
    fallecidos_otras_causas: SituacionLegalFila = Field(default_factory=SituacionLegalFila)
    fallecidos_total: SituacionLegalFila = Field(default_factory=SituacionLegalFila)

class CuadroLesiones(BaseModel):
    lesiones_agentes_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_agentes_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

class SneepCompleto(BaseModel):
    document_id: str
    provincia: Optional[str] = None
    reparticion: Optional[str] = None
    nombre_establecimiento: Optional[str] = None
    tipo_establecimiento: Optional[str] = None
    domicilio_cp: Optional[str] = None
    telefono_fax: Optional[str] = None
    correo_electronico: Optional[str] = None
    responsable_estadistica: Optional[str] = None

    capacidad_fisica_alojamiento: int = 0
    alojados_celdas_individuales: int = 0
    alojados_locales_colectivos: int = 0

    @field_validator(
        "provincia",
        "reparticion",
        "nombre_establecimiento",
        "tipo_establecimiento",
        "domicilio_cp",
        "telefono_fax",
        "correo_electronico",
        "responsable_estadistica",
        mode="before",
    )
    @classmethod
    def _normalize_text_fields(cls, value: Optional[str]) -> Optional[str]:
        return normalize_text(value)

    cuadro_dotacion: CuadroDotacion = Field(default_factory=CuadroDotacion)
    cuadro_poblacion: CuadroPoblacion = Field(default_factory=CuadroPoblacion)
    cuadro_ingresos: CuadroIngresos = Field(default_factory=CuadroIngresos)
    cuadro_egresos_procesados: CuadroEgresosProcesados = Field(default_factory=CuadroEgresosProcesados)
    cuadro_egresos_condenados: CuadroEgresosCondenados = Field(default_factory=CuadroEgresosCondenados)
    cuadro_ninos: CuadroNinos = Field(default_factory=CuadroNinos)
    cuadro_alteraciones: CuadroAlteraciones = Field(default_factory=CuadroAlteraciones)
    cuadro_suicidios: CuadroSuicidios = Field(default_factory=CuadroSuicidios)
    cuadro_fallecidos: CuadroFallecidos = Field(default_factory=CuadroFallecidos)
    cuadro_lesiones: CuadroLesiones = Field(default_factory=CuadroLesiones)