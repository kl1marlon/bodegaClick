import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Producto

def check_products():
    """Verificar los productos en la base de datos"""
    print("=== Verificando productos en la base de datos ===\n")
    
    productos = Producto.objects.all()
    total = productos.count()
    
    print(f"Total de productos: {total}\n")
    
    if total > 0:
        print("Primeros 5 productos:")
        for producto in productos[:5]:
            print(f"- {producto.nombre} (ID: {producto.id}, Precio: ${producto.precio_base})")
    else:
        print("No hay productos en la base de datos.")

if __name__ == '__main__':
    check_products() 