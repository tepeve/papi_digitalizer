from typing import Optional
from pydantic import BaseModel, Field

# ==========================================
# 1. CLASES REUTILIZABLES (Filas de Tablas)
# ==========================================

class GeneroTotalRow(BaseModel):
    """Fila estándar para conteos divididos por sexo."""
    masculino: Optional[int] = 0
    femenino: Optional[int] = 0
    total: Optional[int] = 0

class JurisdiccionRow(BaseModel):
    """Fila para Cuadros 2, 4 y 5 (Dividido por Prov/Nac/Fed y Sexo)."""
    provincial_masc: Optional[int] = 0
    provincial_fem: Optional[int] = 0
    nacional_masc: Optional[int] = 0
    nacional_fem: Optional[int] = 0
    federal_masc: Optional[int] = 0
    federal_fem: Optional[int] = 0
    total: Optional[int] = 0

class NinosRow(BaseModel):
    """Fila para Cuadro 6 (Niños con sus madres)."""
    ninas: Optional[int] = 0
    ninos: Optional[int] = 0
    total: Optional[int] = 0

class AlteracionRow(BaseModel):
    """Fila para Cuadro 7 (Alteraciones del orden)."""
    danos: Optional[int] = 0
    rehenes: Optional[int] = 0
    heridos_muertos: Optional[int] = 0
    total: Optional[int] = 0

class SituacionLegalRow(BaseModel):
    """Fila para Cuadro 9 (Fallecidos divididos por situación legal y sexo)."""
    procesados_masc: Optional[int] = 0
    procesados_fem: Optional[int] = 0
    condenados_masc: Optional[int] = 0
    condenados_fem: Optional[int] = 0
    inimputables_masc: Optional[int] = 0
    inimputables_fem: Optional[int] = 0
    contraventores_masc: Optional[int] = 0
    contraventores_fem: Optional[int] = 0
    otros_masc: Optional[int] = 0
    otros_fem: Optional[int] = 0
    total: Optional[int] = 0

# ==========================================
# 2. ESQUEMA PRINCIPAL (El Formulario Completo)
# ==========================================

class SneepCompleto(BaseModel):
    # --- DATOS GENERALES (group: null) ---
    provincia: Optional[str] = None
    reparticion: Optional[str] = None
    nombre_establecimiento: Optional[str] = None
    tipo_establecimiento: Optional[str] = None
    domicilio_cp: Optional[str] = None
    telefono_fax: Optional[str] = None
    correo_electronico: Optional[str] = None
    responsable_estadistica: Optional[str] = None
    capacidad_fisica_alojamiento: Optional[int] = 0
    alojados_celdas_individuales: Optional[int] = 0
    alojados_locales_colectivos: Optional[int] = 0

    # --- CUADRO 1: Dotación de Personal (group: dotacion_X) ---
    dotacion_oficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_suboficiales: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_cadetes: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_personal_civil: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    dotacion_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

    # --- CUADRO 2: Población Privada de Libertad (group: poblacion_X) ---
    poblacion_procesados: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    poblacion_condenados: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    poblacion_inimputables: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    poblacion_contraventores: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    poblacion_otros: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    poblacion_total: JurisdiccionRow = Field(default_factory=JurisdiccionRow)

    # --- CUADRO 3 (o 4): Ingresos (group: ingresos_ultimo_ano) ---
    ingresos_ultimo_ano: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

    # --- CUADRO 4: Egresos Procesados (group: egresos_proc_X) ---
    egresos_proc_absolucion: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    egresos_proc_cambio_situacion: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    # ... (Puedes agregar los demás motivos de egreso siguiendo este patrón)
    egresos_proc_total: JurisdiccionRow = Field(default_factory=JurisdiccionRow)

    # --- CUADRO 5: Egresos Condenados (group: egresos_cond_X) ---
    egresos_cond_agotamiento: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    egresos_cond_evasion: JurisdiccionRow = Field(default_factory=JurisdiccionRow)
    # ... (Puedes agregar los demás motivos de egreso siguiendo este patrón)
    egresos_cond_total: JurisdiccionRow = Field(default_factory=JurisdiccionRow)

    # --- CUADRO 6: Niños Alojados (group: ninos_X) ---
    ninos_hasta_1: NinosRow = Field(default_factory=NinosRow)
    ninos_1_a_2: NinosRow = Field(default_factory=NinosRow)
    ninos_2_a_3: NinosRow = Field(default_factory=NinosRow)
    ninos_3_a_4: NinosRow = Field(default_factory=NinosRow)
    ninos_total: NinosRow = Field(default_factory=NinosRow)

    # --- CUADRO 7: Alteraciones del Orden (group: alteraciones_X) ---
    alteraciones_fuerza: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_negociacion: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_espontanea: AlteracionRow = Field(default_factory=AlteracionRow)
    alteraciones_total: AlteracionRow = Field(default_factory=AlteracionRow)

    # --- CUADRO 8: Suicidios (group: suicidios_X) ---
    suicidios_procesados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_condenados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_inimputables: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_contraventores: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_otros: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    suicidios_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)

    # --- CUADRO 9: Fallecidos excl. suicidios (group: fallecidos_X) ---
    fallecidos_violencia_internos: SituacionLegalRow = Field(default_factory=SituacionLegalRow)
    fallecidos_violencia_agentes: SituacionLegalRow = Field(default_factory=SituacionLegalRow)
    fallecidos_otras_causas: SituacionLegalRow = Field(default_factory=SituacionLegalRow)
    fallecidos_total: SituacionLegalRow = Field(default_factory=SituacionLegalRow)

    # --- CUADRO 10: Lesiones / Fallecimientos en alteraciones (group: lesiones_X) ---
    lesiones_agentes_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_agentes_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_lesionados: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_internos_fallecidos: GeneroTotalRow = Field(default_factory=GeneroTotalRow)
    lesiones_total: GeneroTotalRow = Field(default_factory=GeneroTotalRow)


## Guía Rápida para el Etiquetado en roi_labeler
# Cuando de ejecuta roi_labeler y se abre 
# la herramienta visual, guíate por estos tres ejemplos 
# para que el mapeo calce perfecto con el nuevo esquema:

# Para el campo Provincia:
# field_id: provincia
# group: [ENTER] (dejar en blanco para que sea null)

# Para la celda "Femenino" de los Oficiales (Cuadro 1):
# field_id: femenino (¡solo el nombre de la columna!)
# group: dotacion_oficiales

# Para la celda "Provincial Masc." de Procesados (Cuadro 2):
# field_id: provincial_masc
# group: poblacion_procesados

# Este esquema es increíblemente robusto. 
# Como usamos Optional[int] = 0, si Qwen no logra leer un número o devuelve 
# un string vacío, Pydantic lo inicializará en 0 por defecto, 
# garantizando que tu base de datos reciba exactamente los tipos de datos 
# que necesita sin que se rompa el pipeline. 
