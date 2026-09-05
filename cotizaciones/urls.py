from django.urls import path

from . import views

app_name = "cotizaciones"

urlpatterns = [
    path("", views.lista_cotizaciones, name="lista"),
    path("nueva/", views.formulario_cotizacion, name="nueva"),
    path("<int:pk>/editar/", views.formulario_cotizacion, name="editar"),
    path("<int:pk>/iniciar/", views.iniciar_servicio, name="iniciar_servicio"),
    path("crear-cliente/", views.crear_cliente_rapido, name="crear_cliente_rapido"),
    path("crear-equipo/", views.crear_equipo_rapido, name="crear_equipo_rapido"),
    path("crear-ubicacion/", views.crear_ubicacion_rapido, name="crear_ubicacion_rapido"),
    path("crear-tecnico/", views.crear_tecnico_rapido, name="crear_tecnico_rapido"),
    path("crear-producto/", views.crear_producto_rapido, name="crear_producto_rapido"),
    path("crear-item-catalogo/", views.crear_item_catalogo_rapido, name="crear_item_catalogo_rapido"),
]
