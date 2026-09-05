from django.contrib import admin

from .models import CalificacionTecnico, MaterialHerramienta, PersonalEjecutor, Tecnico


class CalificacionTecnicoInline(admin.TabularInline):
    model = CalificacionTecnico
    extra = 1


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "dni", "cargo_habitual", "activo")
    search_fields = ("nombres", "apellidos", "dni")
    inlines = [CalificacionTecnicoInline]


@admin.register(PersonalEjecutor)
class PersonalEjecutorAdmin(admin.ModelAdmin):
    list_display = ("servicio", "tecnico", "rol")
    list_filter = ("rol",)
    autocomplete_fields = ("servicio", "tecnico")


@admin.register(MaterialHerramienta)
class MaterialHerramientaAdmin(admin.ModelAdmin):
    list_display = ("servicio", "item", "descripcion", "marca", "cantidad", "unidad")
    autocomplete_fields = ("servicio",)
