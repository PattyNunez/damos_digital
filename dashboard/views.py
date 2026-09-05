from collections import defaultdict
from itertools import groupby

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from servicios.models import EstadoServicio, HistorialEstadoServicio, Servicio, TipoServicio
from servicios.views import _respuestas_checklist_qs
from cuentas.decorators import rol_requerido
from .models import ConfiguracionAlertas

# Estados donde tiene sentido "llevar demasiado tiempo esperando": una cotización sin
# aprobar, o un trabajo que empezó pero no se termina de entregar.
ESTADOS_CON_ALERTA = (EstadoServicio.COTIZADO, EstadoServicio.EN_EJECUCION)

# Transiciones consecutivas del flujo normal de un Servicio.
TRANSICIONES = [
    (EstadoServicio.COTIZADO, EstadoServicio.APROBADO),
    (EstadoServicio.APROBADO, EstadoServicio.EN_EJECUCION),
    (EstadoServicio.EN_EJECUCION, EstadoServicio.ENTREGADO),
]

ETIQUETAS_ESTADO = dict(EstadoServicio.choices)
ETIQUETAS_ESTADO[EstadoServicio.ENTREGADO] = "Entregado/Facturado"


def _con_porcentajes(filas, clave_total="total"):
    """Agrega 'porcentaje' (relativo al máximo de la lista) para dibujar barras
    horizontales sin depender de ninguna librería de gráficos."""
    maximo = max((f[clave_total] for f in filas), default=0) or 1
    for f in filas:
        f["porcentaje"] = round(f[clave_total] / maximo * 100, 1)
    return filas


def _servicios_por_estado():
    conteo = {
        fila["estado"]: fila["total"]
        for fila in Servicio.objects.values("estado").annotate(total=Count("id"))
    }
    filas = [
        {"clave": valor, "estado": ETIQUETAS_ESTADO[valor], "total": conteo.get(valor, 0)}
        for valor, _ in EstadoServicio.choices
    ]
    return _con_porcentajes(filas)


def _eventos_por_servicio():
    """{servicio_id: [(estado, fecha_cambio), ...]} ordenados por fecha, a partir del
    historial que ya se registra automáticamente (ver servicios/signals.py)."""
    eventos = defaultdict(list)
    historial = HistorialEstadoServicio.objects.order_by(
        "servicio_id", "fecha_cambio"
    ).values_list("servicio_id", "estado", "fecha_cambio")
    for servicio_id, estado, fecha in historial:
        eventos[servicio_id].append((estado, fecha))
    return eventos


def _promedio_dias(origen, destino, eventos_por_servicio):
    """Promedio de tiempo entre 'origen' y el primer 'destino' posterior, entre los
    servicios que efectivamente completaron esa transición. Un servicio que nunca llegó a
    'destino' no se cuenta (no se fuerza a 0, sesgaría el promedio a la baja)."""
    duraciones = []
    for eventos in eventos_por_servicio.values():
        fecha_origen = next((f for e, f in eventos if e == origen), None)
        if fecha_origen is None:
            continue
        fecha_destino = next(
            (f for e, f in eventos if e == destino and f > fecha_origen), None
        )
        if fecha_destino is None:
            continue
        duraciones.append((fecha_destino - fecha_origen).total_seconds())

    if not duraciones:
        return None, 0
    promedio = sum(duraciones) / len(duraciones) / 86400
    return round(promedio, 1), len(duraciones)


def _tiempos_promedio_transicion():
    eventos_por_servicio = _eventos_por_servicio()
    resultados = []
    for origen, destino in TRANSICIONES:
        promedio_dias, cantidad = _promedio_dias(origen, destino, eventos_por_servicio)
        resultados.append(
            {
                "origen": ETIQUETAS_ESTADO[origen],
                "destino": ETIQUETAS_ESTADO[destino],
                "promedio_dias": promedio_dias,
                "cantidad": cantidad,
            }
        )

    promedio_total, cantidad_total = _promedio_dias(
        EstadoServicio.COTIZADO, EstadoServicio.ENTREGADO, eventos_por_servicio
    )
    resultados.append(
        {
            "origen": ETIQUETAS_ESTADO[EstadoServicio.COTIZADO],
            "destino": ETIQUETAS_ESTADO[EstadoServicio.ENTREGADO],
            "promedio_dias": promedio_total,
            "cantidad": cantidad_total,
            "es_total": True,
        }
    )
    return resultados


def _porcentaje_preventivos_con_correctivo():
    total_preventivos = Servicio.objects.filter(tipo_servicio=TipoServicio.PREVENTIVO).count()
    con_correctivo = (
        Servicio.objects.filter(
            tipo_servicio=TipoServicio.PREVENTIVO, correctivos_generados__isnull=False
        )
        .distinct()
        .count()
    )
    porcentaje = round(con_correctivo / total_preventivos * 100, 1) if total_preventivos else None
    return {
        "total_preventivos": total_preventivos,
        "con_correctivo": con_correctivo,
        "porcentaje": porcentaje,
    }


def _servicios_por_cliente():
    filas = list(
        Servicio.objects.values("cliente__razon_social")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return _con_porcentajes(filas)


def _servicios_en_alerta():
    """Servicios que llevan más días de la cuenta en 'Cotizado' o 'En ejecución', según los
    umbrales configurables en ConfiguracionAlertas. Devuelve una lista de dicts (más antiguo
    primero) y también un {servicio_id: dias} para poder pintar el badge en el kanban."""
    config = ConfiguracionAlertas.cargar()
    umbral_por_estado = {
        EstadoServicio.COTIZADO: config.dias_alerta_cotizado,
        EstadoServicio.EN_EJECUCION: config.dias_alerta_ejecucion,
    }

    candidatos = list(
        Servicio.objects.filter(estado__in=ESTADOS_CON_ALERTA).select_related("cliente")
    )
    if not candidatos:
        return []

    # Fecha en la que cada servicio entró a su estado ACTUAL (la última vez, por si alguna
    # vez vuelve a un estado ya visitado): se toma el último HistorialEstadoServicio de cada
    # servicio que coincide con su estado presente.
    fecha_entrada_estado_actual = {}
    historial = (
        HistorialEstadoServicio.objects.filter(servicio__in=candidatos)
        .order_by("fecha_cambio")
        .values_list("servicio_id", "estado", "fecha_cambio")
    )
    for servicio_id, estado, fecha in historial:
        fecha_entrada_estado_actual[(servicio_id, estado)] = fecha  # se queda con la última

    ahora = timezone.now()
    alertas = []
    for servicio in candidatos:
        fecha_entrada = fecha_entrada_estado_actual.get((servicio.id, servicio.estado))
        if fecha_entrada is None:
            continue
        dias = (ahora - fecha_entrada).days
        umbral = umbral_por_estado[servicio.estado]
        if dias >= umbral:
            alertas.append(
                {
                    "servicio": servicio,
                    "dias": dias,
                    "umbral": umbral,
                    "estado": servicio.estado,
                    "motivo": (
                        "Cotización sin aprobar"
                        if servicio.estado == EstadoServicio.COTIZADO
                        else "Trabajo atrasado"
                    ),
                }
            )

    alertas.sort(key=lambda a: -a["dias"])
    return alertas


@rol_requerido("administrador")
def vista_dashboard(request):
    alertas = _servicios_en_alerta()
    contexto = {
        "servicios_por_estado": _servicios_por_estado(),
        "tiempos_transicion": _tiempos_promedio_transicion(),
        "preventivos_correctivo": _porcentaje_preventivos_con_correctivo(),
        "servicios_por_cliente": _servicios_por_cliente(),
        "alertas": alertas,
        "alertas_cotizacion": [a for a in alertas if a["estado"] == EstadoServicio.COTIZADO],
        "alertas_ejecucion": [a for a in alertas if a["estado"] == EstadoServicio.EN_EJECUCION],
    }
    return render(request, "dashboard/inicio.html", contexto)


@rol_requerido("administrador")
def vista_kanban(request):
    # Una sola consulta, agrupada en Python: evita 4 queries (una por columna) y evita
    # tener que ordenar por el orden "lógico" de estado dentro de SQL.
    servicios = list(Servicio.objects.select_related("cliente").order_by("-creado_en"))
    servicios_por_estado = defaultdict(list)
    for s in servicios:
        servicios_por_estado[s.estado].append(s)

    dias_alerta_por_servicio = {a["servicio"].id: a["dias"] for a in _servicios_en_alerta()}
    for s in servicios:
        s.dias_en_alerta = dias_alerta_por_servicio.get(s.id)

    columnas = [
        {
            "clave": valor,
            "estado": ETIQUETAS_ESTADO[valor],
            "servicios": servicios_por_estado[valor],
        }
        for valor, _ in EstadoServicio.choices
    ]
    return render(request, "dashboard/kanban.html", {"columnas": columnas})


@rol_requerido("comercial", "administrador")
def vista_detalle_servicio(request, pk):
    servicio = get_object_or_404(
        Servicio.objects.select_related("cliente", "equipo"), pk=pk
    )
    historial = servicio.historial_estados.select_related("usuario").all()
    informe = getattr(servicio, "informe", None)
    propuesta = getattr(servicio, "propuesta_comercial", None)

    # Misma consulta/orden que usa el formulario de campo y el PDF, así el detalle
    # muestra el checklist en el mismo agrupamiento por sistema en todos lados.
    respuestas = list(_respuestas_checklist_qs(servicio))
    checklist_por_sistema = [
        (sistema, list(grupo))
        for sistema, grupo in groupby(respuestas, key=lambda r: r.item.sistema)
    ]

    contexto = {
        "servicio": servicio,
        "historial": historial,
        "informe": informe,
        "propuesta": propuesta,
        "checklist_por_sistema": checklist_por_sistema,
    }
    return render(request, "dashboard/detalle_servicio.html", contexto)


@rol_requerido("administrador")
def exportar_servicios_excel(request):
    import openpyxl

    servicios = Servicio.objects.select_related("cliente", "equipo").order_by("-creado_en")

    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Servicios"
    hoja.append(
        [
            "Código",
            "Cliente",
            "Equipo",
            "Tipo de servicio",
            "Estado",
            "Monto total",
            "Moneda",
            "Fecha de cotización",
            "Fecha de aprobación",
            "Fecha de inicio de ejecución",
            "Fecha de fin de ejecución",
            "Fecha de entrega",
            "Creado en",
        ]
    )

    for s in servicios:
        creado_en_local = timezone.localtime(s.creado_en).replace(tzinfo=None) if s.creado_en else None
        hoja.append(
            [
                s.codigo,
                s.cliente.razon_social,
                str(s.equipo),
                s.get_tipo_servicio_display(),
                s.get_estado_display(),
                float(s.monto_total),
                s.moneda,
                s.fecha_cotizacion,
                s.fecha_aprobacion,
                s.fecha_ejecucion_inicio,
                s.fecha_ejecucion_fin,
                s.fecha_entrega,
                creado_en_local,
            ]
        )

    for indice, encabezado in enumerate(hoja[1], start=1):
        columna = openpyxl.utils.get_column_letter(indice)
        hoja.column_dimensions[columna].width = max(12, len(str(encabezado.value)) + 2)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    nombre_archivo = f"servicios_damol_{timezone.localdate():%Y%m%d}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    libro.save(response)
    return response
