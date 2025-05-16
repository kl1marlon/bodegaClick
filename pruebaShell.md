# --- Inicio del Script de Prueba en el Shell de Django ---
from django.contrib.auth import get_user_model
from facturacion.models import Producto, TasaCambio
from loyverse_integration.tasks import recalculate_user_base_prices_task # Asegúrate que la importación sea correcta
from decimal import Decimal
import json

User = get_user_model()

# --- CONFIGURACIÓN DE LA PRUEBA (AJUSTA ESTOS VALORES) ---
USER_USERNAME_PARA_PRUEBA = 'marlon' # CAMBIA ESTO
TASA_BCV_PRUEBA = Decimal('36.52')
TASA_PARALELO_PRUEBA = Decimal('40.15')

# --- Preparación (Asegurar que el usuario y las tasas existen) ---
try:
    user_obj = User.objects.get(username=USER_USERNAME_PARA_PRUEBA)
    print(f"Usuario de prueba encontrado: {user_obj.username} (ID: {user_obj.id})")

    # Crear/Actualizar tasas para este usuario (asegurar que sean las más recientes)
    TasaCambio.objects.update_or_create(
        user=user_obj, tipo='BCV',
        defaults={'valor': TASA_BCV_PRUEBA}
    )
    TasaCambio.objects.update_or_create(
        user=user_obj, tipo='PARALELO',
        defaults={'valor': TASA_PARALELO_PRUEBA}
    )
    print(f"Tasas para prueba: BCV={TASA_BCV_PRUEBA}, PARALELO={TASA_PARALELO_PRUEBA}")

    # (Opcional) Preparar/Verificar productos de prueba aquí si es necesario
    # Ejemplo: producto_bcv = Producto.objects.get(id=ID_PRODUCTO_BCV_PRUEBA, user=user_obj)
    # print(f"Precio base ANTES para producto BCV ({producto_bcv.nombre}): {producto_bcv.precio_base}")

except User.DoesNotExist:
    print(f"ERROR: Usuario de prueba '{USER_USERNAME_PARA_PRUEBA}' no encontrado. Crea el usuario y los datos necesarios.")
    exit()
except Exception as e:
    print(f"Error en la preparación: {e}")
    exit()

print("\n--- EJECUTANDO recalculate_user_base_prices_task DIRECTAMENTE ---")
# Llamar a la función de la tarea directamente para prueba síncrona
# Esto NO usa Celery, sino que ejecuta la lógica de la función en el hilo actual.
try:
    summary_result = recalculate_user_base_prices_task(user_obj.id) # Pasar el ID del usuario
    print("\n--- RESULTADO DE LA TAREA ---")
    # Usar json.dumps con default=str para manejar Decimals y otros tipos no serializables por defecto
    print(json.dumps(summary_result, indent=2, default=str))

    # --- VERIFICACIONES POST-EJECUCIÓN ---
    print("\n--- VERIFICANDO PRODUCTOS EN BASE DE DATOS ---")
    productos_despues = Producto.objects.filter(user=user_obj)
    for p in productos_despues:
        if p.id in [prod_err['product_id'] for prod_err in summary_result.get('errors', [])]:
            print(f"Producto ID {p.id} ({p.nombre}) tuvo un error, precio_base actual: {p.precio_base}")
        elif any(upd['id'] == p.id for upd in summary_result.get('details', {}).get('updated', [])):
            detalle_actualizado = next(item for item in summary_result['details']['updated'] if item['id'] == p.id)
            print(f"Producto ID {p.id} ({p.nombre}): ACTUALIZADO. Antes: {detalle_actualizado['old_price']}, Después (BD): {p.precio_base}, Calculado: {detalle_actualizado['new_price']}")
            # Aquí puedes añadir aserciones más específicas si el redondeo es complejo
        elif any(unc['id'] == p.id for unc in summary_result.get('details', {}).get('unchanged', [])):
             print(f"Producto ID {p.id} ({p.nombre}): SIN CAMBIOS. precio_base actual: {p.precio_base}")
        else:
             print(f"Producto ID {p.id} ({p.nombre}): No listado en detalles de actualizados/sin cambios, precio_base actual: {p.precio_base} (Revisar si tiene precio_base_usd > 0)")


    print("\n--- Resumen del Resultado ---")
    print(f"Total productos procesados (según tarea): {summary_result.get('total_products')}")
    print(f"Productos actualizados (según tarea): {summary_result.get('updated_products')}")
    print(f"Productos sin cambios (según tarea): {summary_result.get('unchanged_products')}")
    print(f"Número de errores (según tarea): {len(summary_result.get('errors', []))}")
    if summary_result.get('errors'):
        print("Detalle de errores:")
        for err in summary_result['errors']:
            print(f"  - Producto ID {err.get('product_id', 'N/A')} ({err.get('product_name', 'N/A')}): {err.get('error')}")

except Exception as e_task:
    print(f"\nERROR EJECUTANDO LA TAREA DIRECTAMENTE: {e_task}")
    import traceback
    traceback.print_exc()

print("\n--- Prueba Finalizada ---")
# --- Fin del Script de Prueba ---