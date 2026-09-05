from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from servicios.models import Servicio

from .pdf import generar_pdf_propuesta, generar_pdf_servicio, guardar_informe, guardar_propuesta
from cuentas.decorators import rol_requerido


@rol_requerido("tecnico", "administrador")
@require_POST
def generar_informe(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if not servicio.informe_disponible:
        # No es solo cosmético: el botón se oculta en la UI, pero esto es lo que realmente
        # cierra el hueco — sin esto, cualquiera con la URL directa se lo saltaría.
        messages.error(request, servicio.mensaje_informe_no_disponible)
        return redirect("servicios:formulario", pk=servicio.pk)
    pdf_bytes = generar_pdf_servicio(servicio)
    usuario = request.user if request.user.is_authenticated else None
    informe = guardar_informe(servicio, pdf_bytes, usuario=usuario)
    messages.success(request, f"Informe generado (versión {informe.version}).")
    return redirect(informe.archivo_pdf.url)


@rol_requerido("comercial", "administrador")
@require_POST
def generar_propuesta(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if not hasattr(servicio, "detalle_cotizacion"):
        raise Http404("Este servicio no tiene una cotización asociada.")
    pdf_bytes = generar_pdf_propuesta(servicio)
    usuario = request.user if request.user.is_authenticated else None
    propuesta = guardar_propuesta(servicio, pdf_bytes, usuario=usuario)
    messages.success(request, f"Propuesta comercial generada (versión {propuesta.version}).")
    return redirect(propuesta.archivo_pdf.url)
