import unicodedata
from enum import IntEnum
from datetime import date
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator

# ==========================================
# ESCALAS DE RESPUESTA REUTILIZABLES (ENUMS)
# ==========================================

class SiNo(IntEnum):
    NO = 0
    SI = 1

class SiNoNsNc(IntEnum):
    NO = 0
    SI = 1
    NS_NC = 99

class SiParcialNoNsNc(IntEnum):
    NO = 0
    SI = 1
    PARCIALMENTE = 2
    NS_NC = 99

class FrecuenciaSemejante(IntEnum):
    NUNCA = 1
    A_VECES = 2
    SIEMPRE = 3
    NS_NC = 99

class DependenciaEconomica(IntEnum):
    TOTALMENTE = 1
    PARCIALMENTE = 2
    NO_DEPENDIA = 3
    NS_NC = 99

class Calificacion5(IntEnum):
    MUY_MALA_DEGRADANTE = 1
    MALA_IRRESPETUOSO = 2
    REGULAR = 3
    BUENA_RESPETUOSO = 4
    MUY_BUENA_RESPETUOSO = 5
    NS_NC = 99

class IdentidadGenero(IntEnum):
    VARON = 1
    MUJER = 2
    TRANS_TRAVESTI = 3
    NO_BINARIE_OTRA = 4
    PREFIERE_NO_RESPONDER = 99

# ==========================================
# FUNCION DE NORMALIZACIÓN DE TEXTO
# ==========================================

def normalize_text(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    ).strip().upper()

# ==========================================
# CONTRATO DE DATOS: DIAGNÓSTICO INTEGRAL
# ==========================================

class DiagnosticoIntegral(BaseModel):
    # --- DATOS DE LA ENCUESTA ---
    id_encuesta: int
    Fecha_encuesta: date
    nombre_apellido_encuestador: Optional[str] = None

    # --- SECCIÓN 1: DATOS DEMOGRÁFICOS ---
    p1_s1_edad: Optional[int] = None
    p2_s1_genero: Optional[IdentidadGenero] = None
    p3_s1_nacionalidad: Optional[int] = Field(None, description="1=Argentina, 2=Otra")
    p4_s1_residencia_previa: Optional[int] = Field(None, description="1=CABA, 2=PBA, 3=Otra Prov, 4=No residía en Arg")
    p5_s1_otra: Optional[str] = None
    p5_s1_partido_amba: Optional[int] = None
    p5_s1_barrio_caba: Optional[int] = None
    p6_s1_situacion_habitacional: Optional[int] = None
    p6_s1_otra: Optional[str] = None
    p7_s1_nivel_educativo: Optional[int] = None
    p8_s1_estudiaba: Optional[SiNo] = None
    p9_s1_detalle_estudio: Optional[str] = None
    p10_s1_trabajaba: Optional[SiNo] = None
    p11_s1_tipo_trabajo: Optional[int] = None
    p11_s1_otro: Optional[str] = None
    p12_s1_busqueda_trabajo: Optional[SiNoNsNc] = None

    # --- SECCIÓN 2: SITUACIÓN FAMILIAR Y REDES AFECTIVAS ---
    p13_s2_situacion_conyugal: Optional[int] = None
    p14_s2_tiene_hijos: Optional[SiNo] = None
    p15_s2_cant_hijos_menores: Optional[int] = None
    p16_s2_con_usted: Optional[SiNo] = None
    p16_s2_otro_padre: Optional[SiNo] = None
    p16_s2_otro_familiar_1: Optional[SiNo] = None
    p16_s2_otro_familiar_2: Optional[SiNo] = None
    p16_s2_solo: Optional[SiNo] = None
    p16_s2_sin_vinculo: Optional[SiNo] = None
    p16_s2_ns_nc: Optional[SiNo] = None
    p17_s2_otro_padre: Optional[SiNo] = None
    p17_s2_otro_familiar: Optional[SiNo] = None
    p17_s2_institucion: Optional[SiNo] = None
    p17_s2_solo: Optional[SiNo] = None
    p17_s2_sin_vinculo: Optional[SiNo] = None
    p17_s2_ns_nc: Optional[SiNo] = None
    p18_s2_hijo1_dep: Optional[DependenciaEconomica] = None
    p18_s2_hijo2_dep: Optional[DependenciaEconomica] = None
    p18_s2_hijo3_dep: Optional[DependenciaEconomica] = None
    p18_s2_hijo4_dep: Optional[DependenciaEconomica] = None
    p19_s2_otras_personas_a_cargo: Optional[SiNoNsNc] = None
    p20_s2_quienes_a_cargo: Optional[str] = None
    p21_s2_contacto_familiar: Optional[SiNo] = None
    p22_s2_quienes_contacto: Optional[str] = None

    # --- SECCIÓN 3: TRAYECTORIA PENAL ANTERIOR ---
    p23_s3_primera_detencion: Optional[SiNo] = None
    p24_s3_edad_primer_contacto: Optional[int] = None
    p25_s3_cantidad_detenciones: Optional[int] = None
    p26_s3_comisaria: Optional[SiNo] = None
    p26_s3_alcaidia: Optional[SiNo] = None
    p26_s3_unidad_penitenciaria: Optional[SiNo] = None
    p26_s3_salud_mental: Optional[SiNo] = None
    p26_s3_juvenil: Optional[SiNo] = None
    p27_s3_condenas_previas: Optional[SiNoNsNc] = None
    p28_s3_anio_ultima_detencion: Optional[int] = Field(None, description="Año")
    p29_s3_duracion_ultima_detencion: Optional[int] = None
    p30_s3_ultimo_establecimiento: Optional[int] = None
    p30_s3_provincia_ultimo_est: Optional[str] = None
    p31_s3_ofreciemiento_ayuda: Optional[SiNoNsNc] = None
    p32_s3_ayuda_detalle: Optional[int] = None
    p32_s3_ayuda_detalle_otra: Optional[str] = None
    p33_s3_personas_ofrecimiento: Optional[int] = None
    p33_s3_personas_ofrecimientos_otra: Optional[str] = None

    # --- SECCIÓN 4: DETENCIÓN POLICIAL Y SIT. JUDICIAL ---
    p34_s4_tiempo_detenido: Optional[int] = None
    p35_s4_acceso_abogado: Optional[int] = None
    p36_s4_contacto_abogado: Optional[SiNoNsNc] = None
    p37_s4_situacion_legal_actual: Optional[int] = None
    p38_s4_duracion_resto_condena: Optional[int] = None
    p39_s4_conocimiento_causa: Optional[SiNoNsNc] = None

    # --- SECCIÓN 5: USO DEL TIEMPO ---
    p40_s5_salida_celda: Optional[SiNoNsNc] = None
    p41_s5_apertura: Optional[SiNoNsNc] = None
    p41_s5_apertura_carga_horaria: Optional[str] = None
    p42_s5_cierre: Optional[str] = None
    p43_s5_acceso_actividades: Optional[SiNoNsNc] = None
    p44_s5_frecuencia_actividades: Optional[str] = None
    p45_s5_religiosa: Optional[SiNo] = None
    p45_s5_deporte_equipo: Optional[SiNo] = None
    p45_s5_charlas: Optional[SiNo] = None
    p45_s5_talleres: Optional[SiNo] = None
    p45_s5_otras: Optional[SiNo] = None
    p46_s5_otra_actividad_texto: Optional[str] = None

    # --- SECCIÓN 6: ACCESO A LA SALUD INTEGRAL ---
    p47_s6_comisaria: Optional[SiNo] = None
    p47_s6_alcaidia: Optional[SiNo] = None
    p47_s6_no: Optional[SiNo] = None
    p47_s6_ns_nc: Optional[SiNo] = None
    p48_s6_tipo_profesional: Optional[int] = None
    p48_s6_tipo_organismo: Optional[str] = None
    p49_s6_presencia_policial: Optional[SiNoNsNc] = None
    p50_s6_enfermedad: Optional[SiNoNsNc] = None
    p51_s6_enfermedad_detalle: Optional[str] = None
    p52_s6_requiere_tratamiento: Optional[SiNoNsNc] = None
    p53_s6_tratamiento_actual: Optional[int] = None
    p54_s6_necesidad_atencion_externa: Optional[SiNo] = None
    p55_s6_gestion_turno: Optional[int] = None
    p55_s6_gestion_turno_otro: Optional[str] = None
    p56_s6_tiempo_turno: Optional[int] = None
    p57_s6_acceso_turno: Optional[SiNoNsNc] = None
    p58_s6_tipo_efector: Optional[int] = None
    p59_s6_perdio_turno: Optional[SiNoNsNc] = None
    p60_s6_calidad_atencion: Optional[Calificacion5] = None
    p61_s6_tratamiento_salud_mental: Optional[SiNoNsNc] = None
    p62_s6_entrevista_psicologica: Optional[SiNoNsNc] = None

    # --- SECCIÓN 7: SEGURIDAD INTERNA ---
    p63_s7_seguridad_percibida: Optional[int] = None
    p64_s7_robo: Optional[SiNoNsNc] = None
    p65_s7_ramenazas: Optional[SiNoNsNc] = None
    p66_s7_agresion_fisica: Optional[SiNoNsNc] = None
    p67_s7_cese_agresion: Optional[int] = None
    p68_s7_cambio_alojamiento: Optional[int] = None
    p69_s7_respuesta_agentes: Optional[FrecuenciaSemejante] = None
    p70_s7_frecuencia_requisa: Optional[int] = None
    p71_s7_recuentos_diarios: Optional[int] = None

    # --- SECCIÓN 8: DINÁMICAS DE CONVIVENCIA INSTITUCIONAL ---
    p72_s8_reglas_claras: Optional[FrecuenciaSemejante] = None
    p73_s8_aplicacion_justa: Optional[FrecuenciaSemejante] = None
    p74_s8_conflicto_internos: Optional[SiNo] = None
    p74_s8_conflicto_policia: Optional[SiNo] = None
    p74_s8_sin_conflicto: Optional[SiNo] = None
    p74_s8_ns_nc: Optional[SiNo] = None
    p75_s8_sanciones_informales: Optional[SiNoNsNc] = None
    p76_s8_violencia_fisica: Optional[str] = None
    p77_s8_testigo_requisa: Optional[FrecuenciaSemejante] = None
    p78_s8_requisa_dignidad: Optional[FrecuenciaSemejante] = None

    # --- SECCIÓN 9: VINCULACIÓN FAMILIAR Y SOCIOAFECTIVA ---
    p79_s9_llamadas: Optional[int] = None
    p80_s9_duracion_llamadas: Optional[int] = None
    p81_s9_recibe_visitas: Optional[SiNoNsNc] = None
    p82_s9_frecuencia_visita: Optional[int] = None
    p83_s9_pareja: Optional[SiNo] = None
    p83_s9_hijos: Optional[SiNo] = None
    p83_s9_madre: Optional[SiNo] = None
    p83_s9_padre: Optional[SiNo] = None
    p83_s9_hermanos: Optional[SiNo] = None
    p83_s9_amigos: Optional[SiNo] = None
    p83_s9_vecinos: Optional[SiNo] = None
    p83_s9_otro: Optional[SiNo] = None
    p83_s9_otro_texto: Optional[str] = None
    p84_s9_suspension_visitas: Optional[SiNoNsNc] = None
    p85_s9_requisa_visitantes: Optional[FrecuenciaSemejante] = None
    p86_s9_trato_requisa_visitante: Optional[Calificacion5] = None
    p87_s9_requisa_mismo_genero: Optional[FrecuenciaSemejante] = None
    p88_s9_trato_general_visitantes: Optional[Calificacion5] = None
    p89_s9_visitas_nna: Optional[SiNoNsNc] = None
    p90_s9_requisa_nna: Optional[FrecuenciaSemejante] = None
    p91_s9_presencia_adulto: Optional[FrecuenciaSemejante] = None
    p92_s8_genero_requisa_nna: Optional[FrecuenciaSemejante] = None
    p93_s9_impacto_requisa_nna: Optional[DependenciaEconomica] = None

    # --- SECCIÓN 10: ACOMPAÑAMIENTO POSTPENITENCIARIO ---
    p94_s10_planificacion_salida: Optional[SiParcialNoNsNc] = None
    p95_s10_asistencia_pre_egreso: Optional[SiNoNsNc] = None
    p96_s10_lugar_vivir: Optional[SiNoNsNc] = None

    # ==========================================
    # VALIDACIONES Y LIMPIEZA DE CAMPOS
    # ==========================================

    @field_validator('*', mode='before')
    @classmethod
    def normalize_all_strings(cls, value: Any) -> Any:
        # Pasa todos los campos de texto por la función de normalización automáticamente
        if isinstance(value, str):
            return normalize_text(value)
        return value