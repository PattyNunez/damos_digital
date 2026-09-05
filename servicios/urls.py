from django.urls import path

from . import views

app_name = "servicios"

urlpatterns = [
    path("mis-servicios/", views.mis_servicios, name="mis_servicios"),
    path("<int:pk>/formulario/", views.formulario_servicio, name="formulario"),
    path("<int:pk>/ficha/", views.guardar_ficha, name="guardar_ficha"),
    path("<int:pk>/personal/", views.guardar_personal, name="guardar_personal"),
    path("<int:pk>/materiales/", views.guardar_materiales, name="guardar_materiales"),
    path("<int:pk>/checklist/", views.guardar_checklist, name="guardar_checklist"),
    path(
        "<int:pk>/checklist/<int:respuesta_id>/foto/",
        views.agregar_foto_checklist,
        name="agregar_foto_checklist",
    ),
    path(
        "<int:pk>/checklist/foto/<int:foto_id>/eliminar/",
        views.eliminar_foto_checklist,
        name="eliminar_foto_checklist",
    ),
    path("<int:pk>/mediciones/nuevo/", views.crear_grupo_medicion, name="crear_grupo_medicion"),
    path(
        "<int:pk>/mediciones/<int:grupo_id>/",
        views.guardar_grupo_medicion,
        name="guardar_grupo_medicion",
    ),
    path(
        "<int:pk>/mediciones/<int:grupo_id>/eliminar/",
        views.eliminar_grupo_medicion,
        name="eliminar_grupo_medicion",
    ),
    path("<int:pk>/hallazgos/", views.guardar_hallazgos, name="guardar_hallazgos"),
    path(
        "<int:pk>/hallazgos/<int:hallazgo_id>/foto/",
        views.agregar_foto_hallazgo,
        name="agregar_foto_hallazgo",
    ),
    path(
        "<int:pk>/hallazgos/foto/<int:foto_id>/eliminar/",
        views.eliminar_foto_hallazgo,
        name="eliminar_foto_hallazgo",
    ),
    path("<int:pk>/observaciones/", views.guardar_observaciones, name="guardar_observaciones"),
    path("<int:pk>/recomendaciones/", views.guardar_recomendaciones, name="guardar_recomendaciones"),
    path("<int:pk>/conclusiones/", views.guardar_conclusiones, name="guardar_conclusiones"),
]
