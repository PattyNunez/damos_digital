from itertools import groupby

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from checklist.forms import FotoChecklistForm, FotoHallazgoForm, HallazgoFormSet, RespuestaChecklistFormSet
from checklist.models import (
    OPCIONES_ESTADO_CHIP,
    CategoriaSistema,
    FotoChecklist,
    FotoHallazgo,
    Hallazgo,
    RespuestaChecklist,
)
from cuentas.decorators import rol_requerido
from mediciones.forms import GrupoMedicionCreateForm
from mediciones.models import ColumnaMedicion, FilaMedicion, GrupoMedicion, ValorMedicion
from mediciones.utils import construir_grupos_medicion
from personal.forms import MaterialHerramientaFormSet, PersonalEjecutorFormSet

from .forms import (
    ConclusionFormSet,
    FichaServicioForm,
    ObservacionFormSet,
    RecomendacionFormSet,
)
from .models import (
    TEXTOS_ESTANDAR_ANTECEDENTES,
    TEXTOS_ESTANDAR_OBJETIVO,
    FichaServicio,
    Servicio,
)

ROL_CAMPO = ("tecnico", "administrador")


def _volver(pk, ancla):
    return redirect(f"{reverse('servicios:formulario', args=[pk])}#{ancla}")


@rol_requerido(*ROL_CAMPO)
def mis_servicios(request):
    perfil = getattr(request.user, "perfil", None)
    tecnico = perfil.tecnico if perfil else None
    if tecnico is None:
        servicios = Servicio.objects.none()
    else:
        servicios = (
            Servicio.objects.filter(personal_ejecutor__tecnico=tecnico)
            .select_related("cliente", "equipo")
            .distinct()
            .order_by("-creado_en")
        )
    return render(request, "servicios/mis_servicios.html", {"servicios": servicios, "tecnico": tecnico})


def _respuestas_checklist_qs(servicio):
    """Mismo orden siempre: el formset alinea POST <-> objetos por posición, así que
    el orden usado al mostrar el formulario y al guardarlo debe ser idéntico."""
    return (
        RespuestaChecklist.objects.filter(servicio=servicio)
        .select_related("item", "item__sistema")
        .order_by("item__sistema__orden", "item__orden", "variante")
    )


@rol_requerido(*ROL_CAMPO)
def formulario_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    ficha, _ = FichaServicio.objects.get_or_create(servicio=servicio)

    # Objetivo/Antecedentes: precarga editable con el texto estándar del tipo de servicio si
    # todavía no se guardó nada — no se escribe en la BD hasta que el técnico guarde el tab,
    # así que sigue siendo 100% editable, solo no arranca vacío.
    initial_ficha = {}
    if not ficha.objetivo:
        initial_ficha["objetivo"] = TEXTOS_ESTANDAR_OBJETIVO.get(servicio.tipo_servicio, "")
    if not ficha.antecedentes:
        initial_ficha["antecedentes"] = TEXTOS_ESTANDAR_ANTECEDENTES.get(servicio.tipo_servicio, "")
    ficha_form = FichaServicioForm(instance=ficha, initial=initial_ficha)
    personal_formset = PersonalEjecutorFormSet(instance=servicio, prefix="personal")
    materiales_formset = MaterialHerramientaFormSet(instance=servicio, prefix="materiales")

    respuestas_qs = _respuestas_checklist_qs(servicio)
    checklist_formset = RespuestaChecklistFormSet(queryset=respuestas_qs, prefix="checklist")
    # Emparejar cada form del formset con su instancia y agrupar en 2 niveles: categoría
    # (Mecánico → Eléctrico → Generales, la misma secuencia del checklist físico MNT-F-001)
    # y, dentro de cada una, por sistema. El queryset ya viene ordenado por sistema__orden,
    # que a su vez ya respeta ese agrupamiento por categoría (ver migración 0007), así que un
    # groupby directo (sin ordenar de nuevo acá) basta para ambos niveles.
    pares = list(zip(checklist_formset.forms, respuestas_qs))

    def _con_flag_respuestas(grupo_sistema):
        items = list(grupo_sistema)
        tiene_respuestas = any(par[1].estado for par in items)
        return items, tiene_respuestas

    checklist_por_categoria = [
        (
            CategoriaSistema(categoria).label,
            [
                (sistema,) + _con_flag_respuestas(grupo_sistema)
                for sistema, grupo_sistema in groupby(grupo_categoria, key=lambda par: par[1].item.sistema)
            ],
        )
        for categoria, grupo_categoria in groupby(pares, key=lambda par: par[1].item.sistema.categoria)
    ]
    foto_form = FotoChecklistForm()

    observaciones_formset = ObservacionFormSet(instance=servicio, prefix="observaciones")
    recomendaciones_formset = RecomendacionFormSet(instance=servicio, prefix="recomendaciones")
    conclusiones_formset = ConclusionFormSet(instance=servicio, prefix="conclusiones")

    hallazgos_formset = HallazgoFormSet(
        instance=servicio, prefix="hallazgos", form_kwargs={"tipo_equipo": servicio.equipo.tipo_equipo}
    )
    foto_hallazgo_form = FotoHallazgoForm()

    grupo_form = GrupoMedicionCreateForm()
    grupos_medicion_data = construir_grupos_medicion(servicio)

    contexto = {
        "servicio": servicio,
        "ficha_form": ficha_form,
        "personal_formset": personal_formset,
        "materiales_formset": materiales_formset,
        "checklist_formset": checklist_formset,
        "checklist_por_categoria": checklist_por_categoria,
        "opciones_estado_chip": OPCIONES_ESTADO_CHIP,
        "foto_form": foto_form,
        "observaciones_formset": observaciones_formset,
        "recomendaciones_formset": recomendaciones_formset,
        "conclusiones_formset": conclusiones_formset,
        "hallazgos_formset": hallazgos_formset,
        "foto_hallazgo_form": foto_hallazgo_form,
        "grupo_form": grupo_form,
        "grupos_medicion_data": grupos_medicion_data,
    }
    return render(request, "servicios/formulario_servicio.html", contexto)


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_ficha(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    ficha, _ = FichaServicio.objects.get_or_create(servicio=servicio)
    form = FichaServicioForm(request.POST, instance=ficha)
    if form.is_valid():
        form.save()
        messages.success(request, "Datos generales guardados.")
    else:
        messages.error(request, f"Revisa los datos generales: {form.errors}")
    return _volver(pk, "generales")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_personal(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = PersonalEjecutorFormSet(request.POST, instance=servicio, prefix="personal")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Personal ejecutor guardado.")
    else:
        messages.error(request, f"Revisa el personal ejecutor: {formset.errors}")
    return _volver(pk, "personal")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_materiales(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = MaterialHerramientaFormSet(request.POST, instance=servicio, prefix="materiales")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Materiales y herramientas guardados.")
    else:
        messages.error(request, f"Revisa materiales y herramientas: {formset.errors}")
    return _volver(pk, "materiales")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_checklist(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    respuestas_qs = _respuestas_checklist_qs(servicio)
    formset = RespuestaChecklistFormSet(request.POST, queryset=respuestas_qs, prefix="checklist")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Checklist guardado.")
    else:
        messages.error(request, f"Revisa el checklist: {formset.errors}")
    return _volver(pk, "checklist")


@rol_requerido(*ROL_CAMPO)
@require_POST
def agregar_foto_checklist(request, pk, respuesta_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    respuesta = get_object_or_404(RespuestaChecklist, pk=respuesta_id, servicio=servicio)
    form = FotoChecklistForm(request.POST, request.FILES)
    if form.is_valid():
        foto = form.save(commit=False)
        foto.respuesta = respuesta
        foto.save()
        messages.success(request, "Foto agregada.")
    else:
        messages.error(request, f"No se pudo subir la foto: {form.errors}")
    return _volver(pk, "checklist")


@rol_requerido(*ROL_CAMPO)
@require_POST
def eliminar_foto_checklist(request, pk, foto_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    foto = get_object_or_404(FotoChecklist, pk=foto_id, respuesta__servicio=servicio)
    foto.delete()
    messages.success(request, "Foto eliminada.")
    return _volver(pk, "checklist")


@rol_requerido(*ROL_CAMPO)
@require_POST
def crear_grupo_medicion(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    form = GrupoMedicionCreateForm(request.POST)
    if form.is_valid():
        nombres_columnas = form.limpiar_lista("columnas")
        nombres_filas = form.limpiar_lista("filas")
        grupo = GrupoMedicion.objects.create(
            servicio=servicio,
            nombre=form.cleaned_data["nombre"],
            unidad=form.cleaned_data["unidad"],
        )
        columnas = [
            ColumnaMedicion(grupo=grupo, etiqueta=nombre, orden=orden)
            for orden, nombre in enumerate(nombres_columnas)
        ]
        ColumnaMedicion.objects.bulk_create(columnas)
        filas = [
            FilaMedicion(grupo=grupo, etiqueta=nombre, orden=orden)
            for orden, nombre in enumerate(nombres_filas)
        ]
        FilaMedicion.objects.bulk_create(filas)
        valores = [
            ValorMedicion(fila=fila, columna=columna)
            for fila in grupo.filas.all()
            for columna in grupo.columnas.all()
        ]
        ValorMedicion.objects.bulk_create(valores)
        messages.success(request, f"Tabla de mediciones '{grupo.nombre}' creada.")
    else:
        messages.error(request, f"No se pudo crear la tabla: {form.errors}")
    return _volver(pk, "mediciones")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_grupo_medicion(request, pk, grupo_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    grupo = get_object_or_404(GrupoMedicion, pk=grupo_id, servicio=servicio)
    valores = ValorMedicion.objects.filter(fila__grupo=grupo)
    actualizados = []
    for valor in valores:
        campo = f"valor_{valor.pk}"
        if campo in request.POST:
            valor.valor = request.POST[campo]
            actualizados.append(valor)
    ValorMedicion.objects.bulk_update(actualizados, ["valor"])
    messages.success(request, f"Mediciones de '{grupo.nombre}' guardadas.")
    return _volver(pk, "mediciones")


@rol_requerido(*ROL_CAMPO)
@require_POST
def eliminar_grupo_medicion(request, pk, grupo_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    grupo = get_object_or_404(GrupoMedicion, pk=grupo_id, servicio=servicio)
    grupo.delete()
    messages.success(request, "Tabla de mediciones eliminada.")
    return _volver(pk, "mediciones")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_hallazgos(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = HallazgoFormSet(
        request.POST,
        instance=servicio,
        prefix="hallazgos",
        form_kwargs={"tipo_equipo": servicio.equipo.tipo_equipo},
    )
    if formset.is_valid():
        formset.save()
        messages.success(request, "Hallazgos guardados.")
    else:
        messages.error(request, f"Revisa los hallazgos: {formset.errors}")
    return _volver(pk, "hallazgos")


@rol_requerido(*ROL_CAMPO)
@require_POST
def agregar_foto_hallazgo(request, pk, hallazgo_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    hallazgo = get_object_or_404(Hallazgo, pk=hallazgo_id, servicio=servicio)
    form = FotoHallazgoForm(request.POST, request.FILES)
    if form.is_valid():
        foto = form.save(commit=False)
        foto.hallazgo = hallazgo
        foto.save()
        messages.success(request, "Foto agregada.")
    else:
        messages.error(request, f"No se pudo subir la foto: {form.errors}")
    return _volver(pk, "hallazgos")


@rol_requerido(*ROL_CAMPO)
@require_POST
def eliminar_foto_hallazgo(request, pk, foto_id):
    servicio = get_object_or_404(Servicio, pk=pk)
    foto = get_object_or_404(FotoHallazgo, pk=foto_id, hallazgo__servicio=servicio)
    foto.delete()
    messages.success(request, "Foto eliminada.")
    return _volver(pk, "hallazgos")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_observaciones(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = ObservacionFormSet(request.POST, instance=servicio, prefix="observaciones")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Observaciones guardadas.")
    else:
        messages.error(request, f"Revisa las observaciones: {formset.errors}")
    return _volver(pk, "observaciones")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_recomendaciones(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = RecomendacionFormSet(request.POST, instance=servicio, prefix="recomendaciones")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Recomendaciones guardadas.")
    else:
        messages.error(request, f"Revisa las recomendaciones: {formset.errors}")
    return _volver(pk, "observaciones")


@rol_requerido(*ROL_CAMPO)
@require_POST
def guardar_conclusiones(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    formset = ConclusionFormSet(request.POST, instance=servicio, prefix="conclusiones")
    if formset.is_valid():
        formset.save()
        messages.success(request, "Conclusiones guardadas.")
    else:
        messages.error(request, f"Revisa las conclusiones: {formset.errors}")
    return _volver(pk, "observaciones")
