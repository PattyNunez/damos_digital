from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm, ImportarClientesForm, UbicacionFormSet
from .importador import importar_clientes_desde_excel
from .models import Cliente
from cuentas.decorators import rol_requerido


@rol_requerido("comercial", "administrador")
def lista_clientes(request):
    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()
    if q:
        clientes = clientes.filter(
            Q(razon_social__icontains=q) | Q(ruc__icontains=q) | Q(codigo_corto__icontains=q)
        )
    return render(request, "clientes/lista.html", {"clientes": clientes, "q": q})


@rol_requerido("comercial", "administrador")
def formulario_cliente(request, pk=None):
    cliente = get_object_or_404(Cliente, pk=pk) if pk else None

    if request.method == "POST":
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        ubicaciones_formset = UbicacionFormSet(request.POST, instance=cliente, prefix="ubicaciones")
        if form.is_valid() and ubicaciones_formset.is_valid():
            cliente = form.save()
            ubicaciones_formset.instance = cliente
            ubicaciones_formset.save()
            messages.success(request, "Cliente guardado.")
            return redirect("clientes:lista")
    else:
        form = ClienteForm(instance=cliente)
        ubicaciones_formset = UbicacionFormSet(instance=cliente, prefix="ubicaciones")

    return render(
        request,
        "clientes/formulario.html",
        {"form": form, "ubicaciones_formset": ubicaciones_formset, "cliente": cliente},
    )


@rol_requerido("comercial", "administrador")
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(request, "Cliente eliminado.")
        except ProtectedError as e:
            cantidad = len(e.protected_objects)
            messages.error(
                request,
                f"No se puede eliminar '{cliente.razon_social}': tiene {cantidad} "
                "registro(s) asociado(s) (servicios, equipos o ubicaciones).",
            )
        return redirect("clientes:lista")
    return render(request, "clientes/eliminar_confirmar.html", {"cliente": cliente})


@rol_requerido("comercial", "administrador")
def importar_clientes(request):
    resultado = None
    if request.method == "POST":
        form = ImportarClientesForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = importar_clientes_desde_excel(request.FILES["archivo"])
    else:
        form = ImportarClientesForm()

    return render(request, "clientes/importar.html", {"form": form, "resultado": resultado})
