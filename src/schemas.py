import re
from enum import Enum
from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator

def meta(tipo_pregunta: str, nivel_medicion: str, data_type: str) -> dict:
    return {
        "tipo_pregunta": tipo_pregunta,
        "nivel_medicion": nivel_medicion,
        "data_type": data_type
    }

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
    VARON_CIS = "Varón_Cis"
    MUJER_CIS = "Mujer_Cis"
    VARON_TRANS = "Varón_Trans"
    MUJER_TRANS = "Mujer_Trans"
    NO_BINARIE_OTRA = "No binarie/otra"
    PREFIERE_NO_RESPONDER = "Prefiere no responder"

class OrientacionSexual(str, Enum):
    HETEROSEXUAL = "Heterosexual"
    HOMOSEXUAL = "Homosexual"
    BISEXUAL = "Bisexual"
    ASEXUAL = "Asexual"
    OTRA = "Otra"
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

class DiagnosticoIntegral(BaseModel):
    id_encuesta: Optional[int] = Field(None, json_schema_extra=meta("Numérica", "Razón", "int"))
    Fecha_encuesta: Optional[date] = Field(None, json_schema_extra=meta("Fecha", "Intervalo", "date"))
    nombre_apellido_encuestador: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Nominal", "string"))

    p1_s1_edad: Optional[str] = Field(None, json_schema_extra=meta("Categorizada", "Ordinal", "string"))
    p2_s1_genero: Optional[IdentidadGenero] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p2a_s1_orientacion_sexual: Optional[OrientacionSexual] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p3_s1_nacionalidad: Optional[Nacionalidad] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p4_s1_residencia_previa: Optional[ResidenciaPrevia] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p5_s1_otra: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p5_s1_partido_amba: Optional[str] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string")) 
    p5_s1_partido_amba_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p5_s1_barrio_caba: Optional[str] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p5_s1_barrio_caba_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p6_s1_situacion_habitacional: Optional[SituacionHabitacional] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p6_s1_situacion_habitacional_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p7_s1_nivel_educativo: Optional[NivelEducativo] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p8_s1_estudiaba: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p9_s1_detalle_estudio: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p10_s1_trabajaba: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p11_s1_tipo_trabajo: Optional[TipoTrabajo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p11_s1_otro: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p12_s1_busqueda_trabajo: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    p13_s2_situacion_conyugal: Optional[SituacionConyugal] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p14_s2_tiene_hijos: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p15_s2_cant_hijos_menores: Optional[CantidadHijos] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    
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

    p34_s4_tiempo_detenido: Optional[TiempoDetenidoActual] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p35_s4_acceso_abogado: Optional[AccesoAbogado] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p36_s4_contacto_abogado: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p37_s4_situacion_legal_actual: Optional[SituacionLegal] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p38_s4_duracion_resto_condena: Optional[DuracionRestoCondena] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p39_s4_conocimiento_causa: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    p40_s5_salida_celda: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p41_s5_apertura: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p42_s5_cierre: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p43_s5_acceso_actividades: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p44_s5_frecuencia_actividades: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p45_s5_religiosa: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_deporte_equipo: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_charlas: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_talleres: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_otras: Optional[SiNo] = Field(None, json_schema_extra=meta("Opción múltiple", "Nominal", "string"))
    p45_s5_otra_actividad_texto: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p46_descripcion_dia: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))

    p47_s6_comisaria: Optional[SiNo] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p48_s6_tipo_profesional: Optional[TipoProfesionalSalud] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p48_detalle_organismo: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
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

    p63_s7_seguridad_percibida: Optional[SeguridadPercibida] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p64_s7_robo: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p65_s7_ramenazas: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p66_s7_agresiones_detenidos: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p67_s7_cese_agresion: Optional[CeseAgresion] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p68_s7_cambio_alojamiento: Optional[CambioAlojamiento] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p69_s7_sanciones: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p70_s7_especificacion_sanciones: Optional[str] = Field(None, json_schema_extra=meta("Abierta", "Texto Libre", "string"))
    p71_agresion_detencion: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    
    p72_s7_respuesta_agentes: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p73_s7_frecuencia_requisa: Optional[FrecuenciaRequisa] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p74_s7_recuentos_diarios: Optional[EscalaNumericaCorta] = Field(None, json_schema_extra=meta("Cerrada - única", "Razón", "string"))

    p75_s8_reglas_claras: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p76_s8_respuesta_reclamos: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p77_s8_testigo_requisa: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    p78_s8_requisa_dignidad: Optional[FrecuenciaSemejante] = Field(None, json_schema_extra=meta("Cerrada - única", "Ordinal", "string"))
    
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

    p94_s10_planificacion_salida: Optional[SiParcialNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p95_s10_asistencia_pre_egreso: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))
    p96_s10_lugar_vivir: Optional[SiNoNsNc] = Field(None, json_schema_extra=meta("Cerrada - única", "Nominal", "string"))

    @model_validator(mode="before")
    @classmethod
    def pre_process_llm_outputs(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for k, v in list(data.items()):
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean in ["Ns / Nc", "Ns /Nc", "(Porc)", "Porc", "(Parc)", "Ns/nc"]:
                    v_clean = "Ns/Nc"
                data[k] = v_clean

        if "Fecha_encuesta" in data and isinstance(data["Fecha_encuesta"], str):
            val_fecha = data["Fecha_encuesta"].replace("-", "/")
            if re.match(r"^\d{1,2}/\d{1,2}$", val_fecha):
                partes = val_fecha.split('/')
                data["Fecha_encuesta"] = f"2026-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
            elif re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", val_fecha):
                try:
                    partes = val_fecha.split('/')
                    anio = partes[2]
                    if len(anio) == 2:
                        anio = f"20{anio}"
                    data["Fecha_encuesta"] = f"{anio}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
                except ValueError:
                    data.pop("Fecha_encuesta", None)
            else:
                data.pop("Fecha_encuesta", None)

        if "p28_s3_anio_ultima_detencion" in data and isinstance(data["p28_s3_anio_ultima_detencion"], str):
            match = re.search(r'\b(19\d{2}|20\d{2})\b', data["p28_s3_anio_ultima_detencion"])
            if match:
                data["p28_s3_anio_ultima_detencion"] = int(match.group(1))
            else:
                data.pop("p28_s3_anio_ultima_detencion", None)

        mapeos_heuristicos = {
            "p2_s1_genero": {"Varón cis": "Varón_Cis", "Varón": "Varón_Cis", "Mujer cis": "Mujer_Cis", "Mujer": "Mujer_Cis"},
            "p3_s1_nacionalidad": {"(Paraguay)": "Otra", "Paraguay": "Otra"},
            "p7_s1_nivel_educativo": {
                "Terciario–universitario completo": "Terciario/universitario completo",
                "Terciario-universitario completo": "Terciario/universitario completo",
                "Terciario–universitario incompleto": "Terciario/universitario incompleto",
                "Terciario-universitario incompleto": "Terciario/universitario incompleto"
            },
            "p13_s2_situacion_conyugal": {"En pareja": "En pareja estable"},
            "p15_s2_cant_hijos_menores": {"3 o más": "Tres o más", "3 o mas": "Tres o más", "1": "Uno", "2": "Dos", "3 ó más": "Tres o más"},
            "p18_s2_hijo1_dep": {"No dependían": "No dependía"},
            "p18_s2_hijo2_dep": {"No dependían": "No dependía"},
            "p18_s2_hijo3_dep": {"No dependían": "No dependía"},
            "p18_s2_hijo4_dep": {"No dependían": "No dependía"},
            "p29_s3_duracion_ultima_detencion": {
                "- 6 meses": "0–6 meses", "0 - 6 meses": "0–6 meses", "Entre 1 y 6 meses": "0–6 meses", "Menos de 1 mes": "0–6 meses",
                "6 – 18 meses": "6–18 meses", "18 meses – 3 años": "18 meses–3 años", "+ de 3 años": "Más de 3 años"
            },
            "p30_s3_ultimo_establecimiento": {"Comisaría o alcaldía de CABA": "Comisaría o alcaidía de CABA"},
            "p37_s4_situacion_legal_actual": {"Condenada": "Condenado/a", "Procesada": "Procesado/a"},
            "p38_s4_duracion_resto_condena": {"0-3 meses": "0–3 meses"},
            "p52_s6_requiere_tratamiento": {"No está garantizado": "Ns/Nc"},
            "p54_s6_necesidad_atencion_externa": {"Sí, en la alcaidía": "Si", "Sí": "Si"},
            "p55_s6_gestion_turno": {"Gestionado por abogado/ a defensor/ a": "Otro"},
            "p56_s6_tiempo_turno": {"1 a 3 días": "1–3 días", "entre 7 y 15 días": "7–15 días", "(3 semanas)": "1 mes", "3 semanas": "1 mes", "meses": None},
            "p61_s6_tratamiento_salud_mental": {"(Porc)": "Ns/Nc", "Porc": "Ns/Nc", "(Parc)": "Ns/Nc"},
            "p63_s7_seguridad_percibida": {"Ni seguro/a ni inseguro/a": "Ni seguro ni inseguro"},
            "p66_s7_agresiones_detenidos": {"Intervención de personal policial": "Si", "Espontáneamente": "Si", "Intervención de otros detenidos": "Si"},
            "p68_s7_cambio_alojamiento": {
                "No hubo cambios de alojamiento": "No hubo cambio de alojamiento, siguió conviviendo con su agresor",
                "Si, cambiaron de alojamiento al agredido": "Sí, me cambiaron de alojamiento"
            },
            "p73_s7_frecuencia_requisa": {"Nunca": "Menos de una vez por mes"},
            "p74_s7_recuentos_diarios": {"0": None},
            "p79_s9_llamadas": {"Sí, una vez por semana": "Una vez por semana", "Sí, una vez por día": "Una vez por día"},
            "p80_s9_duracion_llamadas": {"(10 min.)": "15 minutos", "10 min.": "15 minutos", "10 min": "15 minutos"},
            "p84_s9_suspension_visitas": {"Siempre": "Si"}
        }

        for campo, mapeo in mapeos_heuristicos.items():
            if campo in data and isinstance(data[campo], str):
                val_limpio = data[campo]
                if val_limpio in mapeo:
                    data[campo] = mapeo[val_limpio]

        for k, v in list(data.items()):
            if isinstance(v, str):
                if k != "Fecha_encuesta":
                    v_normalizado = re.sub(r'\s*[-–]\s*', '–', v)
                else:
                    v_normalizado = v

                if v_normalizado == "Ns/Nc" and k in [
                    "p15_s2_cant_hijos_menores", "p24_s3_edad_primer_contacto", 
                    "p25_s3_cantidad_detenciones", "p29_s3_duracion_ultima_detencion", 
                    "p30_s3_ultimo_establecimiento", "p33_s3_personas_ofrecimiento",
                    "p56_s6_tiempo_turno", "p74_s7_recuentos_diarios"
                ]:
                    v_normalizado = None
                    
                if v_normalizado is not None:
                    v_lower = v_normalizado.lower()
                    if k == "p11_s1_tipo_trabajo" and "informal" in v_lower and "parcial" in v_lower:
                        v_normalizado = "Informal tiempo parcial"
                    elif k == "p11_s1_tipo_trabajo" and "informal" in v_lower and "completo" in v_lower:
                        v_normalizado = "Informal tiempo completo"
                    elif k == "p58_s6_tipo_efector" and "público" in v_lower and "hospital" in v_lower:
                        v_normalizado = "Hospital público"
                    elif k == "p68_s7_cambio_alojamiento" and "no hubo" in v_lower:
                        v_normalizado = "No hubo cambio de alojamiento, siguió conviviendo con su agresor"
                    elif k == "p79_s9_llamadas" and "una vez por día" in v_lower:
                        v_normalizado = "Una vez por día"
                    elif k == "p82_s9_frecuencia_visita" and "menos de una vez al mes" in v_lower:
                        v_normalizado = "Casi nunca"
                    elif k == "p84_s9_suspension_visitas" and "nunca" in v_lower:
                        v_normalizado = "No"
                    elif k == "p93_s9_impacto_requisa_nna" and v_lower == "no":
                        v_normalizado = "No dependía"
                    elif k == "p49_s6_presencia_policial" and "oficia" in v_lower:
                        v_normalizado = "Ns/Nc"

                data[k] = v_normalizado

        data = {k: v for k, v in data.items() if v is not None}

        return data