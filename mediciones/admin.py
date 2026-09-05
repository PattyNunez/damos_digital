from django.contrib import admin

from .models import ColumnaMedicion, FilaMedicion, GrupoMedicion, ValorMedicion


class ColumnaMedicionInline(admin.TabularInline):
    model = ColumnaMedicion
    extra = 1


class FilaMedicionInline(admin.TabularInline):
    model = FilaMedicion
    extra = 1


@admin.register(GrupoMedicion)
class GrupoMedicionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "servicio", "unidad")
    autocomplete_fields = ("servicio",)
    inlines = [ColumnaMedicionInline, FilaMedicionInline]


@admin.register(ValorMedicion)
class ValorMedicionAdmin(admin.ModelAdmin):
    list_display = ("fila", "columna", "valor")
    list_filter = ("fila__grupo",)
