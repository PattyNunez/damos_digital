from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ImportarProductosForm, ProductoForm, ProveedorForm
from .importador import importar_productos_desde_excel
from .models import Producto, Proveedor
from cuentas.decorators import rol_requerido


@rol_requerido("administrador")
def lista_proveedores(request):
    q = request.GET.get("q", "").strip()
    proveedores = Proveedor.objects.all()
    if q:
        proveedores = proveedores.filter(Q(razon_social__icontains=q) | Q(ruc__icontains=q))
    return render(request, "inventario/proveedores_lista.html", {"proveedores": proveedores, "q": q})


@rol_requerido("administrador")
def formulario_proveedor(request, pk=None):
    proveedor = get_object_or_404(Proveedor, pk=pk) if pk else None

    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor guardado.")
            return redirect("inventario:proveedores")
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, "inventario/proveedores_formulario.html", {"form": form, "proveedor": proveedor})


@rol_requerido("administrador")
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        try:
            proveedor.delete()
            messages.success(request, "Proveedor eliminado.")
        except ProtectedError as e:
            cantidad = len(e.protected_objects)
            messages.error(
                request,
                f"No se puede eliminar '{proveedor.razon_social}': tiene {cantidad} "
                "producto(s) asociado(s). Desactívalo en vez de eliminarlo.",
            )
        return redirect("inventario:proveedores")
    return render(request, "inventario/proveedores_eliminar.html", {"proveedor": proveedor})


@rol_requerido("administrador")
def lista_productos(request):
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("proveedor_principal").all()
    if q:
        productos = productos.filter(
            Q(codigo__icontains=q) | Q(nombre__icontains=q) | Q(categoria__icontains=q)
        )
    return render(request, "inventario/productos_lista.html", {"productos": productos, "q": q})


@rol_requerido("administrador")
def formulario_producto(request, pk=None):
    producto = get_object_or_404(Producto, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto guardado.")
            return redirect("inventario:productos")
    else:
        form = ProductoForm(instance=producto)

    return render(request, "inventario/productos_formulario.html", {"form": form, "producto": producto})


@rol_requerido("administrador")
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        try:
            producto.delete()
            messages.success(request, "Producto eliminado.")
        except ProtectedError:
            messages.error(
                request,
                f"No se puede eliminar '{producto.nombre}': está referenciado en otro registro. "
                "Desactívalo en vez de eliminarlo.",
            )
        return redirect("inventario:productos")
    return render(request, "inventario/productos_eliminar.html", {"producto": producto})


@rol_requerido("administrador")
def importar_productos(request):
    resultado = None
    if request.method == "POST":
        form = ImportarProductosForm(request.POST, request.FILES)
        if form.is_valid():
            resultado = importar_productos_desde_excel(request.FILES["archivo"])
    else:
        form = ImportarProductosForm()

    return render(request, "inventario/productos_importar.html", {"form": form, "resultado": resultado})
