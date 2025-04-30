from django.core.management.base import BaseCommand
from decimal import Decimal
from facturacion.models import Producto
# Agregado para mostrar la base de datos usada
from django.db import connection

class Command(BaseCommand):
    help = 'Actualiza el campo precio_base de todos los productos según precio_base_usd y la tasa indicada.'

    def add_arguments(self, parser):
        parser.add_argument('--tasa', type=Decimal, help='Valor de la tasa a aplicar. Si no se indica, se debe obtener de la BD.')

    def handle(self, *args, **options):
        # Log de la base de datos utilizada
        self.stdout.write(self.style.WARNING(f'Usando base de datos: {connection.settings_dict.get("NAME")}'))
        tasa = options['tasa']
        if tasa is None:
            self.stderr.write(self.style.ERROR('Debe indicar la tasa con --tasa (o implementar la lógica para obtenerla de la BD).'))
            return

        productos = Producto.objects.all()
        actualizados = 0
        for producto in productos:
            if producto.precio_base_usd and producto.precio_base_usd > 0:
                nuevo_precio = producto.precio_base_usd * tasa
                if producto.precio_base != nuevo_precio:
                    producto.precio_base = nuevo_precio
                    producto.save(update_fields=['precio_base'])
                    actualizados += 1
        self.stdout.write(self.style.SUCCESS(f'Actualizados {actualizados} productos con la tasa {tasa}'))
