import unicodedata
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# ==========================================
# 1. CLASES REUTILIZABLES (Filas de Tablas)
# ==========================================

class GeneroTotalRow(BaseModel):
    """Fila estandar para conteos divididos por sexo."""
    masculino: int = 0
    femenino: int = 0
    total: int = 0


class JurisdiccionSexo(BaseModel):
    """Contenedor por jurisdiccion y sexo."""
    provincial: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    nacional: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    federal: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class SituacionLegalSexo(BaseModel):
    """Contenedor por situacion legal y sexo."""
    procesados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    condenados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    inimputables: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    contraventores: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class NinosRow(BaseModel):
    """Fila para Cuadro 6 (Ninos con sus madres)."""
    ninas: int = 0
    ninos: int = 0
    total: int = 0


class AlteracionRow(BaseModel):
    """Fila para Cuadro 7 (Alteraciones del orden)."""
    danos: int = 0
    rehenes: int = 0
    heridos_muertos: int = 0
    total: int = 0


class EgresosProcesados(BaseModel):
    """Motivos de egreso para procesados."""
    absolucion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    cambio_situacion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


class EgresosCondenados(BaseModel):
    """Motivos de egreso para condenados."""
    agotamiento: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    evasion: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = " ".join(normalized.split())
    if not normalized:
        return normalized
    return normalized.upper()


class Cuadro1Dotacion(BaseModel):
    """Cuadro 1: dotacion de personal (tabla completa)."""
    dotacion_oficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_suboficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_cadetes: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_personal_civil: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class Cuadro8Suicidios(BaseModel):
    """Cuadro 8: suicidios (tabla completa)."""
    suicidios_procesados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_condenados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_inimputables: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_contraventores: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class CuadroPoblacion(BaseModel):
    """Cuadro 2: poblacion privada de libertad (tabla completa)."""
    procesados: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    condenados: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    inimputables: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    contraventores: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    otros: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)
    total: JurisdiccionSexo = Field(default_factory=JurisdiccionSexo)


class CuadroIngresos(BaseModel):
    """Cuadro 3: ingresos del ultimo ano (tabla completa)."""
    ingresos_ultimo_ano: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


class CuadroEgresos(BaseModel):
    """Cuadros 4 y 5: egresos procesados y condenados (tabla completa)."""
    procesados: EgresosProcesados = Field(default_factory=EgresosProcesados)
    condenados: EgresosCondenados = Field(default_factory=EgresosCondenados)


class CuadroNinos(BaseModel):
    """Cuadro 6: ninos alojados con sus madres (tabla completa)."""
    ninos_hasta_1: NinosRow = Field(default_factory=NinosRow)
    ninos_1_a_2: NinosRow = Field(default_factory=NinosRow)
    ninos_2_a_3: NinosRow = Field(default_factory=NinosRow)
    ninos_3_a_4: NinosRow = Field(default_factory=NinosRow)
    ninos_total: NinosRow = Field(default_factory=NinosRow)


class CuadroAlteraciones(BaseModel):
    """Cuadro 7: alteraciones del orden (tabla completa)."""
    alteraciones_fuerza: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_negociacion: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_espontanea: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_total: AlteracionRow = Field(default_factory=AlteracionRow)


class CuadroFallecidos(BaseModel):
    """Cuadro 9: fallecidos excl. suicidios (tabla completa)."""
    fallecidos_violencia_internos: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_violencia_agentes: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_otras_causas: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)
    fallecidos_total: SituacionLegalSexo = Field(default_factory=SituacionLegalSexo)


class CuadroLesiones(BaseModel):
    """Cuadro 10: lesiones en alteraciones del orden (tabla completa)."""
    lesiones_agentes_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_agentes_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

# ==========================================
# 2. ESQUEMA PRINCIPAL (El Formulario Completo)
# ==========================================

class SneepCompleto(BaseModel):
    """Esquema completo del formulario SNEEP."""
    # --- DATOS GENERALES ---
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

    # --- CUADRO 1: Dotacion de Personal ---
    cuadro_1_dotacion: Cuadro1Dotacion = Field(default_factory=Cuadro1Dotacion)

    # --- CUADRO 2: Poblacion Privada de Libertad ---
    cuadro_poblacion: CuadroPoblacion = Field(default_factory=CuadroPoblacion)

    # --- CUADRO 3: Ingresos ---
    cuadro_ingresos: CuadroIngresos = Field(default_factory=CuadroIngresos)

    # --- CUADRO 4-5: Egresos ---
    cuadro_egresos: CuadroEgresos = Field(default_factory=CuadroEgresos)

    # --- CUADRO 6: Ninos ---
    cuadro_ninos: CuadroNinos = Field(default_factory=CuadroNinos)

    # --- CUADRO 7: Alteraciones ---
    cuadro_alteraciones: CuadroAlteraciones = Field(default_factory=CuadroAlteraciones)

    # --- CUADRO 8: Suicidios ---
    cuadro_8_suicidios: Cuadro8Suicidios = Field(default_factory=Cuadro8Suicidios)

    # --- CUADRO 9: Fallecidos ---
    cuadro_fallecidos: CuadroFallecidos = Field(default_factory=CuadroFallecidos)

    # --- CUADRO 10: Lesiones ---
    cuadro_lesiones: CuadroLesiones = Field(default_factory=CuadroLesiones)
