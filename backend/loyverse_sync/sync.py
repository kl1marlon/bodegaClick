"""
Punto de entrada principal para la sincronización con Loyverse.

Coordina la importación y exportación de productos, proporcionando
una interfaz simple para el uso desde la API y scripts.
"""

import logging
import time
from datetime import datetime

from django.db import transaction
from facturacion.models import Producto, TasaCambio, Factura
from .api import clear_cache
from .products import importar_productos, exportar_precios

logger = logging.getLogger(__name__)

def configurar_logging():
    """Configura el logging para la sincronización."""
    # Formato del log con emojis para mejor legibilidad
    formato = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Configurar el logger raíz para este módulo
    logger_root = logging.getLogger('loyverse_sync')
    logger_root.setLevel(logging.INFO)
    
    # Handler para archivo
    file_handler = logging.FileHandler('loyverse_sync.log')
    file_handler.setFormatter(logging.Formatter(formato))
    logger_root.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(formato))
    logger_root.addHandler(console_handler)
    
    return logger_root

def verificar_factura_reciente(dias=2):
    """
    Verifica si hay facturas creadas recientemente.
    
    Args:
        dias (int): Número de días hacia atrás para buscar facturas
        
    Returns:
        bool: True si hay facturas recientes, False en caso contrario
    """
    from datetime import datetime, timedelta
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    return Factura.objects.filter(fecha__gte=fecha_limite).exists()

def sincronizar_desde_loyverse(opciones=None):
    """
    Función principal para sincronizar desde Loyverse.
    
    Esta función coordina el proceso completo, incluyendo:
    1. Importación de productos desde Loyverse (sin actualizar precios)
    2. Opcional: Exportación de precios calculados hacia Loyverse
    
    Args:
        opciones (dict): Opciones de configuración:
            - solo_importar (bool): Si es True, solo importa productos sin exportar precios
            - categorias (list): Lista de categorías a sincronizar
            - tipo_tasa (str): Filtrar por tipo de tasa (BCV o PARALELO)
            - productos_ids (list): IDs específicos de productos a exportar
            - tamaño_lote (int): Número de productos por lote para exportación (default: 20)
            - direccion_sync (str): Dirección de sincronización:
                - 'bidireccional': Importa y exporta (comportamiento predeterminado)
                - 'bodegaclick_to_loyverse': Solo exporta precios a Loyverse
                - 'loyverse_to_bodegaclick': Solo importa productos desde Loyverse
            
    Returns:
        dict: Estadísticas completas de la operación
    """
    if opciones is None:
        opciones = {}
    
    tiempo_inicio = time.time()
    logger.info(f"🚀 Iniciando sincronización con Loyverse. Opciones: {opciones}")
    
    # Agregar logs informativos sobre las opciones
    if opciones.get('productos_ids'):
        logger.info(f"⚠️ MODO PRUEBA: Sincronizando solo productos específicos: {opciones.get('productos_ids')}")
    if opciones.get('categorias'):
        logger.info(f"📂 Filtrado por categorías: {opciones.get('categorias')}")
    if opciones.get('tipo_tasa'):
        logger.info(f"💲 Filtrado por tipo de tasa: {opciones.get('tipo_tasa')}")
    
    # Procesar dirección de sincronización
    direccion_sync = opciones.get('direccion_sync', 'bidireccional')
    logger.info(f"🔄 Dirección de sincronización: {direccion_sync}")
    
    # Determinar si debemos importar, exportar o ambos según la dirección seleccionada
    importar = direccion_sync in ['bidireccional', 'loyverse_to_bodegaclick']
    exportar = direccion_sync in ['bidireccional', 'bodegaclick_to_loyverse']
    
    # Tamaño de lote para exportación
    tamaño_lote = opciones.get('tamaño_lote', 20)
    if tamaño_lote != 20:  # Solo log si es diferente del valor por defecto
        logger.info(f"📊 Tamaño de lote personalizado para exportación: {tamaño_lote} productos")
    
    # Borrar caché para asegurar datos frescos
    clear_cache()
    
    # Estadísticas globales
    stats = {
        'importacion': {},
        'exportacion': {},
        'tiempo_total': 0,
        'exportacion_realizada': False,
        'importacion_realizada': False,
        'direccion_sync': direccion_sync
    }
    
    try:
        # Importar productos si corresponde según la dirección
        if importar:
            with transaction.atomic():
                opciones_importacion = {
                    'categorias': opciones.get('categorias'),
                    'actualizar_todos_datos': True
                }
                
                if opciones.get('productos_ids'):
                    # Si se especificaron productos, verificar si ya existen en DB y filtrar
                    from facturacion.models import Producto
                    ids_loyverse = []
                    for producto_id in opciones.get('productos_ids'):
                        try:
                            producto = Producto.objects.get(id=producto_id)
                            if producto.loyverse_id:
                                ids_loyverse.append(producto.loyverse_id)
                                logger.info(f"✅ Producto para prueba encontrado: {producto.nombre} (ID: {producto.id}, Loyverse ID: {producto.loyverse_id})")
                            else:
                                logger.warning(f"⚠️ Producto sin Loyverse ID, no se puede sincronizar: {producto.nombre} (ID: {producto.id})")
                        except Producto.DoesNotExist:
                            logger.warning(f"⚠️ Producto no encontrado con ID: {producto_id}")
                    
                    # Solo importar si hay IDs de Loyverse válidos
                    if ids_loyverse:
                        opciones_importacion['loyverse_ids'] = ids_loyverse
                        logger.info(f"🔍 Filtrando importación a solo {len(ids_loyverse)} productos específicos")
                
                stats['importacion'] = importar_productos(opciones_importacion)
                stats['importacion_realizada'] = True
                
            logger.info("✅ Importación completada exitosamente")
        else:
            logger.info("ℹ️ Importación omitida según la dirección de sincronización seleccionada")
        
        # Exportar precios si corresponde según la dirección
        if exportar:
            logger.info("🔄 Iniciando exportación de precios calculados a Loyverse")
            
            with transaction.atomic():
                opciones_exportacion = {
                    'categorias': opciones.get('categorias'),
                    'tipo_tasa': opciones.get('tipo_tasa'),
                    'ids': opciones.get('productos_ids'),
                    'tamaño_lote': tamaño_lote
                }
                stats['exportacion'] = exportar_precios(opciones_exportacion)
                stats['exportacion_realizada'] = True
                
            logger.info("✅ Exportación de precios completada exitosamente")
        else:
            logger.info("ℹ️ Exportación de precios omitida según la dirección de sincronización seleccionada")
    
    except Exception as e:
        logger.exception(f"❌ Error durante la sincronización: {str(e)}")
        stats['error'] = str(e)
    
    # Calcular tiempo total
    tiempo_total = time.time() - tiempo_inicio
    stats['tiempo_total'] = round(tiempo_total, 2)
    
    logger.info(f"🏁 Sincronización completada en {stats['tiempo_total']} segundos")
    
    return stats

if __name__ == "__main__":
    # Configurar logging cuando se ejecute como script
    configurar_logging()
    
    # Ejecutar sincronización con opciones por defecto
    stats = sincronizar_desde_loyverse()
    
    # Imprimir estadísticas
    print("\n=== ESTADÍSTICAS DE SINCRONIZACIÓN ===")
    print(f"Tiempo total: {stats['tiempo_total']} segundos")
    print("\nIMPORTACIÓN:")
    print(f"- Productos creados: {stats['importacion'].get('creados', 0)}")
    print(f"- Productos actualizados: {stats['importacion'].get('actualizados', 0)}")
    print(f"- Categorías actualizadas: {stats['importacion'].get('categorias_actualizadas', 0)}")
    
    if stats.get('exportacion_realizada'):
        print("\nEXPORTACIÓN:")
        print(f"- Precios actualizados: {stats['exportacion'].get('actualizados', 0)}")
        print(f"- Fallidos: {stats['exportacion'].get('fallidos', 0)}")
        print(f"- Sin precio base USD: {stats['exportacion'].get('sin_precio', 0)}")
    
    if 'error' in stats:
        print(f"\n❌ ERROR: {stats['error']}") 