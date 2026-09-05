from .models import GrupoMedicion


def construir_grupos_medicion(servicio):
    """Arma cada GrupoMedicion del servicio como una grilla fila x columna ya resuelta,
    lista para renderizar en una tabla (formulario de campo o informe PDF)."""
    grupos_data = []
    grupos_qs = GrupoMedicion.objects.filter(servicio=servicio).prefetch_related(
        "columnas", "filas__valores"
    )
    for grupo in grupos_qs:
        columnas = list(grupo.columnas.all())
        filas_con_valores = []
        for fila in grupo.filas.all():
            valores_por_columna_id = {v.columna_id: v for v in fila.valores.all()}
            celdas = [valores_por_columna_id.get(columna.id) for columna in columnas]
            filas_con_valores.append((fila, celdas))
        grupos_data.append({"grupo": grupo, "columnas": columnas, "filas": filas_con_valores})
    return grupos_data
