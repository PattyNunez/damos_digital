from django.contrib import admin

from .models import (
    FotoChecklist,
    FotoHallazgo,
    Hallazgo,
    ItemChecklistPlantilla,
    RespuestaChecklist,
    SistemaChecklist,
)


class ItemChecklistPlantillaInline(admin.TabularInline):
    model = ItemChecklistPlantilla
    extra = 1


@admin.register(SistemaChecklist)
class SistemaChecklistAdmin(admin.ModelAdmin):
    list_display = ("orden", "categoria", "nombre", "tipo_equipo")
    list_filter = ("tipo_equipo", "categoria")
    ordering = ("tipo_equipo", "orden")
    inlines = [ItemChecklistPlantillaInline]


class FotoChecklistInline(admin.TabularInline):
    model = FotoChecklist
    extra = 1


@admin.register(RespuestaChecklist)
class RespuestaChecklistAdmin(admin.ModelAdmin):
    list_display = ("servicio", "item", "variante", "estado")
    list_filter = ("estado", "item__sistema")
    autocomplete_fields = ("servicio",)
    inlines = [FotoChecklistInline]


class FotoHallazgoInline(admin.TabularInline):
    model = FotoHallazgo
    extra = 1


@admin.register(Hallazgo)
class HallazgoAdmin(admin.ModelAdmin):
    list_display = ("servicio", "sistema", "descripcion")
    list_filter = ("sistema",)
    autocomplete_fields = ("servicio",)
    inlines = [FotoHallazgoInline]
