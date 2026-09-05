from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.vista_dashboard, name="inicio"),
    path("kanban/", views.vista_kanban, name="kanban"),
    path("kanban/servicio/<int:pk>/", views.vista_detalle_servicio, name="detalle_servicio"),
    path("exportar/", views.exportar_servicios_excel, name="exportar_excel"),
]
