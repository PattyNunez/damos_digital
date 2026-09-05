from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.lista_clientes, name="lista"),
    path("nuevo/", views.formulario_cliente, name="nuevo"),
    path("<int:pk>/editar/", views.formulario_cliente, name="editar"),
    path("<int:pk>/eliminar/", views.eliminar_cliente, name="eliminar"),
    path("importar/", views.importar_clientes, name="importar"),
]
