from .models import EstadoItem

# Redacción oficial de niveles de alerta según JP-F-007 (tabla "Trabajos operativos").
RESULTADOS_POR_ESTADO = {
    EstadoItem.BUENO: "Equipo o componentes en buen estado.",
    EstadoItem.REGULAR: (
        "El equipo puede trabajar con dicha observación, sin embargo, se recomienda su cambio."
    ),
    EstadoItem.MALO: "Se recomienda cambio inmediato o en corto plazo.",
}


def resolver_narrativa(respuesta):
    """Arma el párrafo narrativo de una RespuestaChecklist para el cuerpo del informe.
    Devuelve None si el ítem no tiene estado evaluable ("No aplica"/vacío) o no tiene
    texto_plantilla definido: esos ítems no se narran, solo aparecen en el Anexo 4."""
    if respuesta.estado not in RESULTADOS_POR_ESTADO or not respuesta.item.texto_plantilla:
        return None

    parrafo = respuesta.item.texto_plantilla.format(
        nombre_item=respuesta.item.descripcion,
        variante=respuesta.variante,
        resultado_por_estado=RESULTADOS_POR_ESTADO[respuesta.estado],
    )
    if respuesta.observacion:
        parrafo = f"{parrafo} {respuesta.observacion}"
    return parrafo
