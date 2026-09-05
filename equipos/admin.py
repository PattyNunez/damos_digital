from django.contrib import admin

from .models import Equipo, TipoEquipo


@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "cliente", "tipo_equipo", "ubicacion", "capacidad_ton")
    list_filter = ("tipo_equipo", "cliente")
    search_fields = ("codigo_interno", "numero_serie", "modelo")
