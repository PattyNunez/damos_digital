from django.contrib import admin

from .models import EquipoMedicion, NormaAplicable


@admin.register(NormaAplicable)
class NormaAplicableAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "activo", "orden")
    list_editable = ("orden", "activo")


@admin.register(EquipoMedicion)
class EquipoMedicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "marca", "modelo", "fecha_vencimiento")
    list_filter = ("marca",)
