from django.db import migrations

# (nombre_actual, categoria, nombre_nuevo_o_None, orden_nuevo)
# Reagrupa los 10 sistemas ya cargados de "Grúa pórtico" en 2 pasadas (Mecánico, luego
# Eléctrico) + una tercera categoría "Generales" para lo que no es ni uno ni otro — en vez
# de estar intercalados como quedaron en la carga original (0002_cargar_plantilla_grua_portico).
PLAN = [
    ("Polipasto", "mecanico", None, 1),
    ("Trolley Principal", "mecanico", "Trolley / Carro", 2),
    ("Puente / Pluma", "mecanico", None, 3),
    ("Componentes eléctricos del polipasto", "electrico", None, 4),
    ("Componentes carro y/o trolley", "electrico", "Componentes eléctricos del carro/trolley", 5),
    ("Componentes eléctricos puente", "electrico", "Componentes eléctricos del puente", 6),
    ("Sistemas de alimentación", "electrico", None, 7),
    ("Sistemas de mando", "electrico", None, 8),
    ("Sistema audio visual", "electrico", "Sistema audiovisual", 9),
    ("Otros", "generales", None, 10),
]


def recategorizar(apps, schema_editor):
    SistemaChecklist = apps.get_model("checklist", "SistemaChecklist")
    faltantes = []
    for nombre_actual, categoria, nombre_nuevo, orden in PLAN:
        sistema = SistemaChecklist.objects.filter(nombre=nombre_actual).first()
        if sistema is None:
            faltantes.append(nombre_actual)
            continue
        sistema.categoria = categoria
        sistema.orden = orden
        if nombre_nuevo:
            sistema.nombre = nombre_nuevo
        sistema.save(update_fields=["categoria", "orden", "nombre"])
    if faltantes:
        # No es fatal (una base sin el seed de checklist original no tiene nada que reordenar),
        # pero lo dejamos visible en el log de la migración en vez de fallar en silencio.
        print(f"  (aviso: no se encontraron estos sistemas, se omiten: {faltantes})")


def revertir(apps, schema_editor):
    # No hay un "orden original" que valga la pena reconstruir (la carga inicial ya estaba
    # intercalada, no en un orden con significado propio) — revertir es una operación no-op
    # deliberada; el campo 'categoria' vuelve a su default al desaplicar 0006.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("checklist", "0006_sistemachecklist_categoria_and_more"),
    ]

    operations = [
        migrations.RunPython(recategorizar, revertir),
    ]
