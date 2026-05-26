from enum import Enum
from datetime import date
from typing import Optional, Any
from pydantic import BaseModel, Field

# ==========================================
# HELPER PARA METADATOS DEL CONTRATO
# ==========================================
def meta(tipo_pregunta: str, nivel_medicion: str, data_type: str) -> dict:
    """Inyecta la tipificación estadística y de estructura en el esquema JSON."""
    return {
        "tipo_pregunta": tipo_pregunta,
        "nivel_medicion": nivel_medicion,
        "data_type": data_type
    }

# ==========================================
# ESCALAS DE RESPUESTA REUTILIZABLES (ENUMS DESCODIFICADOS)
# ==========================================

class SiNo(str, Enum):
    SI = "Si"
    NO = "No"

class SiNoNsNc(str, Enum):
    SI = "Si"
    NO = "No"
    NS_NC = "Ns/Nc"

class SiParcialNoNsNc(str, Enum):
    SI = "Si"
    PARCIALMENTE = "Parcialmente"
    NO = "No"
    NS_NC = "Ns/Nc"

class FrecuenciaSemejante(str, Enum):
    SIEMPRE = "Siempre"
    A_VECES = "A veces"
    NUNCA = "Nunca"
    NS_NC = "Ns/Nc"

class DependenciaEconomica(str, Enum):
    TOTALMENTE = "Totalmente"
    PARCIALMENTE = "Parcialmente"
    NO_DEPENDIA = "No dependía"
    NS_NC = "Ns/Nc"

class IdentidadGenero(str, Enum):
    VARON = "Varón"
    MUJER = "Mujer"
    TRANS_TRAVESTI = "Trans/Travesti"
    NO_BINARIE_OTRA = "No binarie/otra"
    PREFIERE_NO_RESPONDER = "Prefiere no responder"

class Nacionalidad(str, Enum):
    ARGENTINA = "Argentina"
    OTRA = "Otra"

class ResidenciaPrevia(str, Enum):
    CABA = "CABA"
    PBA = "Provincia de Buenos Aires"
    OTRA_PROVINCIA = "Otra Provincia"
    NO_RESIDIA = "No residía en Argentina"

class SituacionHabitacional(str, Enum):
    ALQUILADA = "Vivienda alquilada"
    CASA_PROPIA = "Casa propia"
    FAMILIAR = "Vivienda de familiar"
    IRREGULAR = "Ocupación irregular / hotel"
    HOGAR = "Hogar convivencial"
    CALLE = "Situación de calle"
    OTRA = "Otra"

class NivelEducativo(str, Enum):
    PRIMARIO_INC = "Primario incompleto"
    PRIMARIO_COM = "Primario completo"
    SECUNDARIO_INC = "Secundario incompleto"
    SECUNDARIO_COM = "Secundario completo"
    TERCIARIO_INC = "Terciario/universitario incompleto"
    TERCIARIO_COM = "Terciario/universitario completo"

class TipoTrabajo(str, Enum):
    FORMAL_COMPLETO = "Formal tiempo completo"
    FORMAL_PARCIAL = "Formal tiempo parcial"
    INFORMAL_COMPLETO = "Informal tiempo completo"
    INFORMAL_PARCIAL = "Informal tiempo parcial"
    CHANGA = "Changa"
    CUENTA_PROPIA = "Cuenta propia"
    OTRO = "Otro"
    NS_NC = "Ns/Nc"

class SituacionConyugal(str, Enum):
    SOLTERO = "Soltero/a"
    PAREJA = "En pareja estable"
    CASADO = "Casado/a"
    VIUDO = "Viudo/a"
    DIVORCIADO = "Divorciado/a o separado/a"
    OTRA = "Otra"
    NS_NC = "Ns/Nc"

class CantidadHijos(str, Enum):
    UNO = "Uno"
    DOS = "Dos"
    TRES_MAS = "Tres o más"

class EdadPrimerContacto(str, Enum):
    MENOR_18 = "Menor de 18"
    DE_18_24 = "18–24"
    DE_25_34 = "25–34"
    MAYOR_35 = "35 o más"

class EscalaNumericaAgrupada(str, Enum):
    UNO = "1"
    DOS = "2"
    TRES = "3"
    CUATRO_MAS = "4 o más"
    
class EscalaNumericaCorta(str, Enum):
    UNO = "1"
    DOS = "2"
    TRES = "3"
    CUATRO = "4"

class DuracionDetencionPrevia(str, Enum):
    M_0_6 = "0–6 meses"
    M_6_18 = "6–18 meses"
    M_18_3Y = "18 meses–3 años"
    MAS_3Y = "Más de 3 años"

class UltimoEstablecimiento(str, Enum):
    FEDERAL = "En una cárcel Federal"
    PROVINCIAL = "En una cárcel provincial"
    CABA = "Comisaría o alcaidía de CABA"

class AyudaDetalle(str, Enum):
    LABORAL = "Búsqueda laboral"
    HABITACIONAL = "Ayuda habitacional"
    SALUD_ADICCIONES = "Tratamiento de salud o de adicciones"
    OTRA = "otra"
    NS_NC = "Ns/Nc"

class PersonasOfrecimiento(str, Enum):
    ESTATAL = "Organismo estatal (patronato, programa ministerial o de justicia, etc)"
    SOCIEDAD_CIVIL = "Sociedad civil (ong, iglesia, etc)"
    OTRA = "otra"

class TiempoDetenidoActual(str, Enum):
    MENOS_1M = "Menos de 1 mes"
    ENTRE_1_6M = "Entre 1 y 6 meses"
    MAS_6M = "Más de 6 meses"
    NS_NC = "Ns/Nc"

class AccesoAbogado(str, Enum):
    PARTICULAR = "Sí, abogado particular"
    DEFENSOR_PUBLICO = "Sí, defensor público"
    NO = "No"
    NS_NC = "Ns/Nc"

class SituacionLegal(str, Enum):
    PROCESADO = "Procesado/a"
    CONDENADO = "Condenado/a"
    NS_NC = "Ns/Nc"

class DuracionRestoCondena(str, Enum):
    M_0_3 = "0–3 meses"
    M_3_6 = "3–6 meses"
    M_6_12 = "6–12 meses"
    MAS_12M = "Más de 12 meses"
    NS_NC = "Ns/Nc"

class TipoProfesionalSalud(str, Enum):
    POLICIA = "Personal de salud de la policia interviniente"
    OTRO_ORGANISMO = "Personal de salud de otro organismo público."
    NS_NC = "Ns/Nc"

class TratamientoActualSalud(str, Enum):
    EN_ALCAIDIA = "Sí, en alcaidía"
    EN_EXTERNO = "Sí, en un efector de salud externo"
    NO_GARANTIZADO = "No está garantizado"
    NS_NC = "Ns/Nc"

class MecanismoTurno(str, Enum):
    POLICIAL = "Gestionado por el personal policial"
    FAMILIAR = "Gestionado por familiar o referente socio-afectivo"
    OTRO = "Otro"

class TiempoTurno(str, Enum):
    D_1_3 = "1–3 días"
    D_3_7 = "3–7 días"
    D_7_15 = "7–15 días"
    M_1 = "1 mes"
    M_2 = "2 meses"
    M_3_MAS = "3 meses o más"

class TipoEfector(str, Enum):
    HOSPITAL = "Hospital público"
    CENTRO_SALUD = "Centro de salud"
    CLINICA = "Clínica privada"
    OTRO = "Otro"
    NS_NC = "Ns/Nc"

class CalificacionAtencion(str, Enum):
    MUY_BUENA = "Muy buena"
    BUENA = "Buena"
    REGULAR = "Regular"
    MALA = "Mala"
    MUY_MALA = "Muy mala"
    NS_NC = "Ns/Nc"

class CalificacionTrato(str, Enum):
    MUY_RESPETUOSO = "Muy respetuoso"
    RESPETUOSO = "Respetuoso"
    REGULAR = "Regular"
    IRRESPETUOSO = "Irrespetuoso"
    DEGRADANTE = "Degradante"
    NS_NC = "Ns/Nc"

class SeguridadPercibida(str, Enum):
    MUY_SEGURO = "Muy seguro/a"
    SEGURO = "Seguro/a"
    NI_NI = "Ni seguro ni inseguro"
    POCO_SEGURO = "Poco seguro/a"
    NADA_SEGURO = "Nada seguro/a"
    NS_NC = "Ns/Nc"

class CeseAgresion(str, Enum):
    INTERVENCION_DETENIDOS = "Intervención de otros detenidos"
    INTERVENCION_POLICIAL = "Intervención de personal policial"
    ESPONTANEAMENTE = "Espontáneamente"
    NS_NC = "Ns/Nc"

class CambioAlojamiento(str, Enum):
    CAMBIO_PROPIO = "Sí, me cambiaron de alojamiento"
    CAMBIO_AGRESOR = "Sí, cambiaron de alojamiento al agresor"
    CAMBIO_AMBOS = "Nos cambiaron de alojamiento a ambos"
    SIN_CAMBIO = "No hubo cambio de alojamiento, siguió conviviendo con su agresor"
    NS_NC = "Ns/Nc"

class FrecuenciaRequisa(str, Enum):
    DIARIO = "Todos los días"
    VARIAS_SEMANA = "Varias veces por semana"
    UNA_SEMANA = "Una vez por semana"
    QUINCENAL = "Cada quince días"
    MENSUAL = "Una vez por mes"
    MENOS_MENSUAL = "Menos de una vez por mes"
    NS_NC = "Ns/Nc"

class FrecuenciaLlamadas(str, Enum):
    DIARIO = "Una vez por día"
    DIA_POR_MEDIO = "Día por medio"
    UNA_SEMANA = "Una vez por semana"
    NO = "No"
    NS_NC = "Ns/Nc"

class DuracionLlamadas(str, Enum):
    MIN_15 = "15 minutos"
    MIN_30 = "30 minutos"
    MIN_45 = "45 minutos"
    H_1 = "1 hora"
    NO_PAUTADA = "No tiene una duración pautada"
    NS_NC = "Ns/Nc"

class FrecuenciaVisita(str, Enum):
    SEMANAL = "Todas las semanas"
    QUINCENAL = "Cada 15 días"
    MENSUAL = "1 vez por mes"
    CADA_TANTO = "Cada tanto"
    CASI_NUNCA = "Casi nunca"
    NS_NC = "Ns/Nc"


# ==========================================
# CONTRATO DE DATOS: DIAGNÓSTICO INTEGRAL
# ==========================================

class DiagnosticoIntegral(BaseModel):
    # --- DATOS DE LA ENCUESTA ---
    id_encuesta: int = Field(..., json_schema_extra=meta("Numérica", "Razón", "int"))
    Fecha_encuesta: date = Field(..., json_schema_extra=meta("Fecha", "Intervalo", "date"))
    nombre_apellido_encuestador: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Nominal", "string"))

    # --- SECCIÓN 1: DATOS DEMOGRÁFICOS ---
    p1_s1_edad: Optional[int] = Field(None, json_schema_extra=meta("Numérica", "Razón", "int"))
    p2_s1_genero: Optional[IdentidadGenero] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p3_s1_nacionalidad: Optional[Nacionalidad] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p4_s1_residencia_previa: Optional[ResidenciaPrevia] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p5_s1_otra: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p5_s1_partido_amba: Optional[str] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string")) # Se mantiene str abierto para evitar enums de 40+ elementos en extracción OCR directa, pero validados lógicamente.
    p5_s1_barrio_caba: Optional[str] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p6_s1_situacion_habitacional: Optional[SituacionHabitacional] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p6_s1_otra: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p7_s1_nivel_educativo: Optional[NivelEducativo] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p8_s1_estudiaba: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p9_s1_detalle_estudio: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p10_s1_trabajaba: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p11_s1_tipo_trabajo: Optional[TipoTrabajo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p11_s1_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p12_s1_busqueda_trabajo: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    # --- SECCIÓN 2: SITUACIÓN FAMILIAR Y REDES AFECTIVAS ---
    p13_s2_situacion_conyugal: Optional[SituacionConyugal] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p14_s2_tiene_hijos: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p15_s2_cant_hijos_menores: Optional[CantidadHijos] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    
    # Opciones Múltiples de P16 y P17
    p16_s2_con_usted: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_otro_padre: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_otro_familiar_1: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_otro_familiar_2: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_solo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_sin_vinculo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p16_s2_ns_nc: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    
    p17_s2_otro_padre: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p17_s2_otro_familiar: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p17_s2_institucion: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p17_s2_solo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p17_s2_sin_vinculo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p17_s2_ns_nc: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))

    p18_s2_hijo1_dep: Optional[DependenciaEconomica] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p18_s2_hijo2_dep: Optional[DependenciaEconomica] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p18_s2_hijo3_dep: Optional[DependenciaEconomica] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p18_s2_hijo4_dep: Optional[DependenciaEconomica] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p19_s2_otras_personas_a_cargo: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p20_s2_quienes_a_cargo: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p21_s2_contacto_familiar: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p22_s2_quienes_contacto: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))

    # --- SECCIÓN 3: TRAYECTORIA PENAL ANTERIOR ---
    p23_s3_primera_detencion: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p24_s3_edad_primer_contacto: Optional[EdadPrimerContacto] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p25_s3_cantidad_detenciones: Optional[EscalaNumericaAgrupada] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    
    p26_s3_comisaria: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p26_s3_alcaidia: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p26_s3_unidad_penitenciaria: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p26_s3_salud_mental: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p26_s3_juvenil: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    
    p27_s3_condenas_previas: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p28_s3_anio_ultima_detencion: Optional[int] = Field(None, json_schema_extra=meta("Numérica", "Intervalo", "int"))
    p29_s3_duracion_ultima_detencion: Optional[DuracionDetencionPrevia] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p30_s3_ultimo_establecimiento: Optional[UltimoEstablecimiento] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p30_s3_provincia_ultimo_est: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p31_s3_ofreciemiento_ayuda: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p32_s3_ayuda_detalle: Optional[AyudaDetalle] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p32_s3_ayuda_detalle_otra: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p33_s3_personas_ofrecimiento: Optional[PersonasOfrecimiento] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p33_s3_personas_ofrecimientos_otra: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))

    # --- SECCIÓN 4: DETENCIÓN POLICIAL Y SIT. JUDICIAL ---
    p34_s4_tiempo_detenido: Optional[TiempoDetenidoActual] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p35_s4_acceso_abogado: Optional[AccesoAbogado] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p36_s4_contacto_abogado: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p37_s4_situacion_legal_actual: Optional[SituacionLegal] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p38_s4_duracion_resto_condena: Optional[DuracionRestoCondena] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p39_s4_conocimiento_causa: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    # --- SECCIÓN 5: USO DEL TIEMPO ---
    p40_s5_salida_celda: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p41_s5_apertura: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p41_s5_apertura_carga_horaria: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p42_s5_cierre: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p43_s5_acceso_actividades: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p44_s5_frecuencia_actividades: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p45_s5_religiosa: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_deporte_equipo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_charlas: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_talleres: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_otras: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p46_s5_otra_actividad_texto: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))

    # --- SECCIÓN 6: ACCESO A LA SALUD INTEGRAL ---
    p47_s6_comisaria: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p47_s6_alcaidia: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p47_s6_no: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p47_s6_ns_nc: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p48_s6_tipo_profesional: Optional[TipoProfesionalSalud] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p48_s6_tipo_organismo: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p49_s6_presencia_policial: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p50_s6_enfermedad: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p51_s6_enfermedad_detalle: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p52_s6_requiere_tratamiento: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p53_s6_tratamiento_actual: Optional[TratamientoActualSalud] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p54_s6_necesidad_atencion_externa: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p55_s6_gestion_turno: Optional[MecanismoTurno] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p55_s6_gestion_turno_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p56_s6_tiempo_turno: Optional[TiempoTurno] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p57_s6_acceso_turno: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p58_s6_tipo_efector: Optional[TipoEfector] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p59_s6_perdio_turno: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p60_s6_calidad_atencion: Optional[CalificacionAtencion] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p61_s6_tratamiento_salud_mental: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p62_s6_entrevista_psicologica: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    # --- SECCIÓN 7: SEGURIDAD INTERNA ---
    p63_s7_seguridad_percibida: Optional[SeguridadPercibida] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p64_s7_robo: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p65_s7_ramenazas: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p66_s7_agresion_fisica: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p67_s7_cese_agresion: Optional[CeseAgresion] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p68_s7_cambio_alojamiento: Optional[CambioAlojamiento] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p69_s7_respuesta_agentes: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p70_s7_frecuencia_requisa: Optional[FrecuenciaRequisa] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p71_s7_recuentos_diarios: Optional[EscalaNumericaCorta] = Field(None, json_schema_extra=meta("Cerrada - única", "Razón", "string"))

    # --- SECCIÓN 8: DINÁMICAS DE CONVIVENCIA INSTITUCIONAL ---
    p72_s8_reglas_claras: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p73_s8_aplicacion_justa: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p74_s8_conflicto_internos: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p74_s8_conflicto_policia: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p74_s8_sin_conflicto: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p74_s8_ns_nc: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p75_s8_sanciones_informales: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p76_s8_violencia_fisica: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p77_s8_testigo_requisa: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p78_s8_requisa_dignidad: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))

    # --- SECCIÓN 9: VINCULACIÓN FAMILIAR Y SOCIOAFECTIVA ---
    p79_s9_llamadas: Optional[FrecuenciaLlamadas] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p80_s9_duracion_llamadas: Optional[DuracionLlamadas] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p81_s9_recibe_visitas: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p82_s9_frecuencia_visita: Optional[FrecuenciaVisita] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p83_s9_pareja: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_hijos: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_madre: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_padre: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_hermanos: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_amigos: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_vecinos: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_otro: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p83_s9_otro_texto: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p84_s9_suspension_visitas: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p85_s9_requisa_visitantes: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p86_s9_trato_requisa_visitante: Optional[CalificacionTrato] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p87_s9_requisa_mismo_genero: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p88_s9_trato_general_visitantes: Optional[CalificacionTrato] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p89_s9_visitas_nna: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p90_s9_requisa_nna: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p91_s9_presencia_adulto: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p92_s8_genero_requisa_nna: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p93_s9_impacto_requisa_nna: Optional[DependenciaEconomica] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))

    # --- SECCIÓN 10: ACOMPAÑAMIENTO POSTPENITENCIARIO ---
    p94_s10_planificacion_salida: Optional[SiParcialNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p95_s10_asistencia_pre_egreso: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p96_s10_lugar_vivir: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))