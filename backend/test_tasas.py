import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from facturacion.models import TasaCambio

def test_tasas():
    """Probar la creación y consulta de tasas de cambio"""
    print("=== Probando tasas de cambio ===\n")
    
    # Crear tasas de prueba
    tasas_prueba = [
        {'tipo': 'BCV', 'valor': 35.50},
        {'tipo': 'PARALELO', 'valor': 36.80}
    ]
    
    tasas_creadas = []
    for tasa_data in tasas_prueba:
        tasa, created = TasaCambio.objects.get_or_create(
            tipo=tasa_data['tipo'],
            fecha=date.today(),
            defaults={'valor': tasa_data['valor']}
        )
        tasas_creadas.append(tasa)
        if created:
            print(f"✨ Nueva tasa creada: {tasa.tipo} - {tasa.valor}")
        else:
            print(f"📝 Tasa existente actualizada: {tasa.tipo} - {tasa.valor}")
    
    # Consultar tasas
    print("\n📊 Tasas disponibles:")
    for tasa in TasaCambio.objects.filter(fecha=date.today()):
        print(f"   - {tasa.tipo}: {tasa.valor} BS/USD (fecha: {tasa.fecha})")

if __name__ == '__main__':
    test_tasas() 