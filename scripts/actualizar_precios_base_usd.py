import os
import sys
import django
from decimal import Decimal

# Configura el entorno de Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from facturacion.models import Producto

from django.db import connection

def obtener_tasa_paralelo():
    # Aquí deberías implementar la lógica real para obtener la tasa paralelo
    # Por ahora, pedimos al usuario que la confirme manualmente
    tasa = input('Introduce la tasa paralelo a usar: ')
    try:
        tasa = Decimal(tasa)
    except Exception:
        print('Tasa inválida. Debe ser un número decimal.')
        sys.exit(1)
    confirm = input(f'¿Confirmas la tasa {tasa}? (s/n): ')
    if confirm.lower() != 's':
        print('Operación cancelada.')
        sys.exit(0)
    return tasa

def main():
    print(f'Conectado a la base de datos: {connection.settings_dict.get("NAME")}')
    tasa = obtener_tasa_paralelo()
    productos = Producto.objects.all()
    actualizados = 0
    for producto in productos:
        if producto.precio_base_usd and producto.precio_base_usd > 0:
            nuevo_precio = producto.precio_base_usd * tasa
            if producto.precio_base != nuevo_precio:
                producto.precio_base = nuevo_precio
                producto.save(update_fields=['precio_base'])
                actualizados += 1
    print(f'Actualizados {actualizados} productos con la tasa {tasa}')

if __name__ == '__main__':
    main()
