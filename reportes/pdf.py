import base64
import os
import sys
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone

from checklist.models import Hallazgo, RespuestaChecklist
from checklist.narrativa import resolver_narrativa
from mediciones.utils import construir_grupos_medicion
from personal.models import MaterialHerramienta, PersonalEjecutor
from servicios.models import TEXTOS_ESTANDAR_ANTECEDENTES, TEXTOS_ESTANDAR_OBJETIVO

if sys.platform == "darwin":
    # Homebrew instala Pango/Cairo/GLib en /opt/homebrew/lib, que no está en el path de
    # búsqueda dinámica de macOS por defecto; WeasyPrint (vía cffi) no las encuentra sin esto.
    os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

from .models import ConfiguracionInforme, InformeGenerado, PropuestaComercial

# Logo de Damol: activo fijo del proyecto, no depende de que alguien lo suba. Es la marca
# del dueño del sistema, siempre la misma — a diferencia del logo del cliente (Cliente.logo),
# que sí es opcional y variable por servicio.
_RUTA_LOGO_DAMOL = Path(__file__).resolve().parent / "static" / "reportes" / "damol_logo.jpg"


def _respuestas_checklist_completas(servicio):
    return (
        RespuestaChecklist.objects.filter(servicio=servicio)
        .select_related("item", "item__sistema")
        .prefetch_related("fotos")
        .order_by("item__sistema__orden", "item__orden", "variante")
    )


def _construir_anexo_checklist(respuestas):
    """Agrupa TODAS las respuestas por sistema, para la tabla completa del Anexo 4."""
    grupos = {}
    orden_sistemas = []
    for r in respuestas:
        sistema = r.item.sistema
        if sistema.pk not in grupos:
            grupos[sistema.pk] = {"sistema": sistema, "filas": []}
            orden_sistemas.append(sistema.pk)
        grupos[sistema.pk]["filas"].append(r)
    return [grupos[pk] for pk in orden_sistemas]


def _construir_trabajos_operativos(respuestas):
    """Solo los ítems con hallazgo (foto y/o comentario) entran al cuerpo, agrupados por
    sistema, con numeración correlativa de imágenes para todo el documento."""
    grupos = {}
    orden_sistemas = []
    contador_imagen = 0

    for r in respuestas:
        fotos = list(r.fotos.all())
        tiene_contenido = bool(fotos) or bool(r.observacion)
        if not tiene_contenido:
            continue
        parrafo = resolver_narrativa(r)
        if parrafo is None:
            continue

        fotos_numeradas = []
        for foto in fotos:
            contador_imagen += 1
            fotos_numeradas.append({"foto": foto, "numero": contador_imagen})

        sistema = r.item.sistema
        if sistema.pk not in grupos:
            grupos[sistema.pk] = {"sistema": sistema, "hallazgos": []}
            orden_sistemas.append(sistema.pk)
        grupos[sistema.pk]["hallazgos"].append(
            {"respuesta": r, "parrafo": parrafo, "fotos": fotos_numeradas}
        )

    return [grupos[pk] for pk in orden_sistemas]


def _logo_damol_data_uri():
    with open(_RUTA_LOGO_DAMOL, "rb") as f:
        datos = f.read()
    return f"data:image/jpeg;base64,{base64.b64encode(datos).decode()}"


def _ruta_imagen(campo_imagen):
    """file://<ruta absoluta> para un ImageField opcional, o None si no tiene archivo
    cargado (mismo patrón que ya usan las fotos del checklist)."""
    if not campo_imagen:
        return None
    try:
        return f"file://{campo_imagen.path}"
    except (FileNotFoundError, ValueError):
        return None


def _linea_encabezado(configuracion):
    fecha = (
        configuracion.encabezado_fecha_aprobacion.strftime("%d/%m/%Y")
        if configuracion.encabezado_fecha_aprobacion
        else "---"
    )
    return (
        f"Código {configuracion.encabezado_codigo}  ·  Versión {configuracion.encabezado_version}"
        f"  ·  Fecha Aprob. {fecha}"
    )


def generar_contexto(servicio):
    configuracion = ConfiguracionInforme.obtener()
    respuestas = list(_respuestas_checklist_completas(servicio))
    ficha = getattr(servicio, "ficha", None)

    # Objetivo/Antecedentes: si nunca se guardaron (el técnico no tocó ese tab, o la ficha ni
    # existe), el informe igual sale con el texto estándar del tipo de servicio — no en blanco.
    objetivo_texto = (ficha.objetivo if ficha else "") or TEXTOS_ESTANDAR_OBJETIVO.get(
        servicio.tipo_servicio, ""
    )
    antecedentes_texto = (ficha.antecedentes if ficha else "") or TEXTOS_ESTANDAR_ANTECEDENTES.get(
        servicio.tipo_servicio, ""
    )

    return {
        "servicio": servicio,
        "equipo": servicio.equipo,
        "ficha": ficha,
        "objetivo_texto": objetivo_texto,
        "antecedentes_texto": antecedentes_texto,
        "configuracion": configuracion,
        "logo_damol_data_uri": _logo_damol_data_uri(),
        "encabezado_linea": _linea_encabezado(configuracion),
        "logo_cliente_ruta": _ruta_imagen(servicio.cliente.logo),
        "equipo_foto_ruta": _ruta_imagen(servicio.equipo.foto),
        "equipo_foto_ubicacion_ruta": _ruta_imagen(servicio.equipo.foto_ubicacion),
        "personal_ejecutor": PersonalEjecutor.objects.filter(servicio=servicio).select_related(
            "tecnico"
        ),
        "materiales": MaterialHerramienta.objects.filter(servicio=servicio),
        "checklist_existe": bool(respuestas),
        "trabajos_operativos": _construir_trabajos_operativos(respuestas),
        "anexo_checklist": _construir_anexo_checklist(respuestas),
        "hallazgos": Hallazgo.objects.filter(servicio=servicio).select_related("sistema").prefetch_related("fotos"),
        "grupos_medicion": construir_grupos_medicion(servicio),
        "observaciones": servicio.observaciones.all(),
        "recomendaciones": servicio.recomendaciones.all(),
        "conclusiones": servicio.conclusiones.all(),
    }


def generar_pdf_servicio(servicio):
    from weasyprint import HTML

    contexto = generar_contexto(servicio)
    html_string = render_to_string("reportes/informe_pdf.html", contexto)
    return HTML(string=html_string, base_url="/").write_pdf()


def guardar_informe(servicio, pdf_bytes, usuario=None):
    """Reemplaza el PDF anterior (si existe) y sube la versión, en vez de acumular
    historial de archivos: los datos fuente siguen intactos y siempre se puede regenerar."""
    informe = InformeGenerado.objects.filter(servicio=servicio).first()
    if informe is None:
        informe = InformeGenerado(servicio=servicio, version=1)
    else:
        informe.archivo_pdf.delete(save=False)
        informe.version += 1

    informe.numero_informe = servicio.codigo
    informe.generado_por = usuario
    nombre_archivo = f"{servicio.codigo}_v{informe.version}.pdf"
    informe.archivo_pdf.save(nombre_archivo, ContentFile(pdf_bytes), save=True)
    return informe


def _bloque_equipo_propuesta(detalle, nombre_equipo=None):
    """Empaqueta los 2 montos consolidados del equipo para la tabla de precios de la propuesta:
    'Servicio de mantenimiento correctivo' = subtotal_servicio y 'Suministro' = subtotal_repuestos.
    Ambos ya vienen calculados y correctos desde DetalleCotizacion.recalcular() — esta función
    no recalcula nada, solo los junta en la forma que necesita la plantilla.

    nombre_equipo es un override opcional (en vez de tomar detalle.servicio.equipo): permite
    armar, solo a nivel de plantilla/demo, una propuesta con varios bloques de equipo sin
    necesitar todavía el modelo real de agrupación multi-equipo (Opción A, fase aparte)."""
    nombre = nombre_equipo or str(detalle.servicio.equipo)
    return {
        "nombre_equipo": nombre,
        "subtotal_servicio": detalle.subtotal_servicio,
        "subtotal_repuestos": detalle.subtotal_repuestos,
        "total": detalle.subtotal_servicio + detalle.subtotal_repuestos,
    }


def generar_contexto_propuesta(servicio, bloques_equipo=None):
    configuracion = ConfiguracionInforme.obtener()
    detalle = servicio.detalle_cotizacion

    # Hoy 1 cotización = 1 Servicio = 1 equipo (el modelo no agrupa varios todavía). bloques_equipo
    # ya deja la plantilla lista para mostrar varios equipos en una sola propuesta el día que ese
    # cambio de modelo se haga; mientras tanto, con un solo Servicio real, es una lista de 1.
    if bloques_equipo is None:
        bloques_equipo = [_bloque_equipo_propuesta(detalle)]

    total_general = sum((b["total"] for b in bloques_equipo), Decimal("0"))

    return {
        "servicio": servicio,
        "configuracion": configuracion,
        "logo_damol_data_uri": _logo_damol_data_uri(),
        "fecha_generacion": timezone.localdate(),
        "bloques_equipo": bloques_equipo,
        "total_partidas": total_general,
        "items_alcance": detalle.items_alcance.all(),
        "items_exclusion": detalle.items_exclusion.all(),
        "items_provision_cliente": detalle.items_provision_cliente.all(),
        "items_provision_damol": detalle.items_provision_damol.all(),
    }


def generar_pdf_propuesta(servicio, bloques_equipo=None):
    from weasyprint import HTML

    contexto = generar_contexto_propuesta(servicio, bloques_equipo=bloques_equipo)
    html_string = render_to_string("reportes/propuesta_pdf.html", contexto)
    return HTML(string=html_string, base_url="/").write_pdf()


def guardar_propuesta(servicio, pdf_bytes, usuario=None):
    """Mismo mecanismo de reemplazo + versión que guardar_informe."""
    propuesta = PropuestaComercial.objects.filter(servicio=servicio).first()
    if propuesta is None:
        propuesta = PropuestaComercial(servicio=servicio, version=1)
    else:
        propuesta.archivo_pdf.delete(save=False)
        propuesta.version += 1

    propuesta.generado_por = usuario
    nombre_archivo = f"{servicio.codigo}_propuesta_v{propuesta.version}.pdf"
    propuesta.archivo_pdf.save(nombre_archivo, ContentFile(pdf_bytes), save=True)
    return propuesta
