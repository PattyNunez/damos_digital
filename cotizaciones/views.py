import json

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cuentas.decorators import rol_requerido
from equipos.models import TipoEquipo
from personal.forms import PersonalEjecutorAsignacionFormSet
from servicios.models import EstadoServicio, Servicio

from .forms import (
    ClienteRapidoForm,
    DetalleCotizacionForm,
    EquipoRapidoForm,
    ItemAlcanceFormSet,
    ItemEquipoFormSet,
    ItemExclusionFormSet,
    ItemLogisticaFormSet,
    ItemManoObraFormSet,
    ItemMaterialFormSet,
    ItemProvisionClienteFormSet,
    ItemProvisionDamolFormSet,
    ProductoRapidoForm,
    ServicioCotizacionForm,
    TecnicoRapidoForm,
    UbicacionRapidoForm,
)
from .models import ItemCatalogo, TipoItemCatalogo

ROL_COTIZACIONES = ("comercial", "administrador")


def _catalogo_por_tipo():
    catalogo = {tipo: [] for tipo in TipoItemCatalogo.values}
    for item in ItemCatalogo.objects.all():
        catalogo[item.tipo].append(item.texto)
    return catalogo

VALORES_INICIALES_DETALLE = {
    "porcentaje_indirectos": 10,
    "porcentaje_utilidad_servicio": 20,
    "porcentaje_utilidad_repuestos": 15,
}


@rol_requerido(*ROL_COTIZACIONES)
def lista_cotizaciones(request):
    q = request.GET.get("q", "").strip()
    servicios = Servicio.objects.select_related("cliente", "equipo").order_by("-creado_en")
    if q:
        servicios = servicios.filter(Q(codigo__icontains=q) | Q(cliente__razon_social__icontains=q))
    return render(request, "cotizaciones/lista.html", {"servicios": servicios, "q": q})


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def iniciar_servicio(request, pk):
    """Colapsa en un clic lo que hoy son 2-3 pasos manuales: aprobar -> pasar a ejecución ->
    ir al checklist. Solo tiene sentido desde 'Aprobado' — si ya está en otro estado, no hace
    nada raro, solo redirige (no falla feo con un 404/500 si alguien hace doble clic)."""
    servicio = get_object_or_404(Servicio, pk=pk)
    if servicio.estado == EstadoServicio.APROBADO:
        servicio.estado = EstadoServicio.EN_EJECUCION
        servicio.save(update_fields=["estado", "codigo"])
        messages.success(request, f"{servicio.codigo} pasó a 'En ejecución'.")
    return redirect("servicios:formulario", pk=servicio.pk)


@rol_requerido(*ROL_COTIZACIONES)
def formulario_cotizacion(request, pk=None):
    servicio = get_object_or_404(Servicio, pk=pk) if pk else None
    detalle = getattr(servicio, "detalle_cotizacion", None) if servicio else None

    if request.method == "POST":
        servicio_form = ServicioCotizacionForm(request.POST, instance=servicio)
        detalle_form = DetalleCotizacionForm(request.POST, instance=detalle)
        personal_formset = PersonalEjecutorAsignacionFormSet(request.POST, instance=servicio, prefix="personal")
        mano_obra_formset = ItemManoObraFormSet(request.POST, instance=detalle, prefix="mano_obra")
        logistica_formset = ItemLogisticaFormSet(request.POST, instance=detalle, prefix="logistica")
        equipo_formset = ItemEquipoFormSet(request.POST, instance=detalle, prefix="equipo")
        material_formset = ItemMaterialFormSet(request.POST, instance=detalle, prefix="material")
        alcance_formset = ItemAlcanceFormSet(request.POST, instance=detalle, prefix="alcance")
        exclusion_formset = ItemExclusionFormSet(request.POST, instance=detalle, prefix="exclusion")
        provision_cliente_formset = ItemProvisionClienteFormSet(request.POST, instance=detalle, prefix="provision_cliente")
        provision_damol_formset = ItemProvisionDamolFormSet(request.POST, instance=detalle, prefix="provision_damol")

        formsets_de_detalle = (
            mano_obra_formset,
            logistica_formset,
            equipo_formset,
            material_formset,
            alcance_formset,
            exclusion_formset,
            provision_cliente_formset,
            provision_damol_formset,
        )

        formularios_validos = servicio_form.is_valid() and detalle_form.is_valid()
        formularios_validos = personal_formset.is_valid() and formularios_validos
        for formset in formsets_de_detalle:
            formularios_validos = formset.is_valid() and formularios_validos

        if formularios_validos:
            servicio = servicio_form.save()

            personal_formset.instance = servicio
            personal_formset.save()

            if detalle is None:
                detalle = detalle_form.save(commit=False)
                detalle.servicio = servicio
                detalle.save()
            else:
                detalle_form.save()

            for formset in formsets_de_detalle:
                formset.instance = detalle
                formset.save()

            verbo = "actualizada" if pk else "creada"
            messages.success(request, f"Cotización {servicio.codigo} {verbo}.")
            return redirect("dashboard:detalle_servicio", pk=servicio.pk)
    else:
        servicio_form = ServicioCotizacionForm(instance=servicio)
        detalle_form = DetalleCotizacionForm(
            instance=detalle, initial=None if detalle else VALORES_INICIALES_DETALLE
        )
        personal_formset = PersonalEjecutorAsignacionFormSet(instance=servicio, prefix="personal")
        mano_obra_formset = ItemManoObraFormSet(instance=detalle, prefix="mano_obra")
        logistica_formset = ItemLogisticaFormSet(instance=detalle, prefix="logistica")
        equipo_formset = ItemEquipoFormSet(instance=detalle, prefix="equipo")
        material_formset = ItemMaterialFormSet(instance=detalle, prefix="material")
        alcance_formset = ItemAlcanceFormSet(instance=detalle, prefix="alcance")
        exclusion_formset = ItemExclusionFormSet(instance=detalle, prefix="exclusion")
        provision_cliente_formset = ItemProvisionClienteFormSet(instance=detalle, prefix="provision_cliente")
        provision_damol_formset = ItemProvisionDamolFormSet(instance=detalle, prefix="provision_damol")

    return render(
        request,
        "cotizaciones/nueva.html",
        {
            "servicio": servicio,
            "servicio_form": servicio_form,
            "detalle_form": detalle_form,
            "personal_formset": personal_formset,
            "mano_obra_formset": mano_obra_formset,
            "logistica_formset": logistica_formset,
            "equipo_formset": equipo_formset,
            "material_formset": material_formset,
            "alcance_formset": alcance_formset,
            "exclusion_formset": exclusion_formset,
            "provision_cliente_formset": provision_cliente_formset,
            "provision_damol_formset": provision_damol_formset,
            "tipos_equipo": TipoEquipo.objects.all(),
            "catalogo_json": json.dumps(_catalogo_por_tipo()),
        },
    )


# --- Creación rápida (combobox "buscar o crear" de Cliente/Equipo/Ubicación) ---
# Endpoints JSON minimalistas: no reemplazan los formularios completos de clientes/ ni de
# equipos/, solo permiten crear el registro mínimo sin salir del formulario de cotización.


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_cliente_rapido(request):
    form = ClienteRapidoForm(request.POST)
    if form.is_valid():
        cliente = form.save()
        return JsonResponse({"id": cliente.pk, "label": str(cliente)})
    return JsonResponse({"errors": form.errors}, status=400)


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_equipo_rapido(request):
    form = EquipoRapidoForm(request.POST)
    if form.is_valid():
        equipo = form.save()
        return JsonResponse({"id": equipo.pk, "label": str(equipo), "cliente_id": equipo.cliente_id})
    return JsonResponse({"errors": form.errors}, status=400)


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_ubicacion_rapido(request):
    form = UbicacionRapidoForm(request.POST)
    if form.is_valid():
        ubicacion = form.save()
        return JsonResponse({"id": ubicacion.pk, "label": str(ubicacion), "cliente_id": ubicacion.cliente_id})
    return JsonResponse({"errors": form.errors}, status=400)


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_tecnico_rapido(request):
    form = TecnicoRapidoForm(request.POST)
    if form.is_valid():
        tecnico = form.save()
        return JsonResponse({"id": tecnico.pk, "label": str(tecnico)})
    return JsonResponse({"errors": form.errors}, status=400)


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_producto_rapido(request):
    form = ProductoRapidoForm(request.POST)
    if form.is_valid():
        producto = form.save()
        return JsonResponse(
            {
                "id": producto.pk,
                "label": str(producto),
                "precio": str(producto.precio_referencial),
                "moneda": producto.moneda,
            }
        )
    return JsonResponse({"errors": form.errors}, status=400)


@rol_requerido(*ROL_COTIZACIONES)
@require_POST
def crear_item_catalogo_rapido(request):
    tipo = request.POST.get("tipo", "")
    texto = request.POST.get("texto", "").strip()
    if tipo not in TipoItemCatalogo.values or not texto:
        return JsonResponse({"errors": "Datos inválidos."}, status=400)
    # get_or_create a propósito: si dos personas escriben el mismo texto en distintas
    # cotizaciones, se reutiliza la misma entrada de catálogo en vez de duplicarla.
    item, _ = ItemCatalogo.objects.get_or_create(tipo=tipo, texto=texto)
    return JsonResponse({"label": item.texto})
