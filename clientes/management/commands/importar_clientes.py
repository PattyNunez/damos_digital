from django.core.management.base import BaseCommand, CommandError

from clientes.importador import importar_clientes_desde_excel


class Command(BaseCommand):
    help = "Importa/actualiza clientes desde un archivo Excel (.xlsx) con la plantilla de Damol Digital."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo .xlsx a importar.")

    def handle(self, *args, **options):
        ruta = options["archivo"]
        try:
            resultado = importar_clientes_desde_excel(ruta)
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {ruta}")

        self.stdout.write(
            self.style.SUCCESS(
                f"{resultado.creados} cliente(s) creado(s), {resultado.actualizados} actualizado(s)."
            )
        )
        if resultado.errores:
            self.stdout.write(self.style.ERROR(f"{len(resultado.errores)} fila(s) con error:"))
            for error in resultado.errores:
                self.stdout.write(f"  - {error}")
