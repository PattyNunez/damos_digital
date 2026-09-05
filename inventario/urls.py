from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("proveedores/", views.lista_proveedores, name="proveedores"),
    path("proveedores/nuevo/", views.formulario_proveedor, name="proveedor_nuevo"),
    path("proveedores/<int:pk>/editar/", views.formulario_proveedor, name="proveedor_editar"),
    path("proveedores/<int:pk>/eliminar/", views.eliminar_proveedor, name="proveedor_eliminar"),
    path("", views.lista_productos, name="productos"),
    path("nuevo/", views.formulario_producto, name="producto_nuevo"),
    path("<int:pk>/editar/", views.formulario_producto, name="producto_editar"),
    path("<int:pk>/eliminar/", views.eliminar_producto, name="producto_eliminar"),
    path("importar/", views.importar_productos, name="importar"),
]
