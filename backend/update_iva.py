import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import Producto

def update_iva():
    """Actualizar el campo aplicar_iva en todos los productos"""
    try:
        count = Producto.objects.all().update(aplicar_iva=False)
        print(f"✅ Se actualizaron {count} productos exitosamente.")
    except Exception as e:
        print(f"❌ Error actualizando productos: {str(e)}")

if __name__ == '__main__':
    print("=== Actualizando campo aplicar_iva en productos ===\n")
    update_iva() 