"""
Funcionalidades de sincronización de productos con Loyverse.

Implementa:
- Importación de productos manteniendo precio_base_usd intacto
- Exportación de precios calculados hacia Loyverse
- Sincronización selectiva por categoría y tipo de tasa
"""

import logging
from decimal import Decimal
import datetime

from django.db.models import Q
from facturacion.models import Producto, Factura, TasaCambio
from .api import get_categories, get_all_products, get_product_by_id, update_product_price

logger = logging.getLogger(__name__)

def importar_productos(opciones=None):
    """
    Importa productos desde Loyverse, sin modificar los precios base en USD.
    
    Args:
        opciones (dict): Opciones de filtrado y configuración:
            - categorias (list): Lista de categorías a importar
            - incluir_precio_variable (bool): Si se deben incluir productos con precio variable
            - actualizar_todos_datos (bool): Si se deben actualizar todos los campos excepto precios
            - loyverse_ids (list): Lista de IDs específicos de Loyverse para importar solo esos productos
            
    Returns:
        dict: Estadísticas de la operación
    """
    if opciones is None:
        opciones = {}
    
    # Obtener mapa de categorías
    category_map = get_categories()
    
    # Obtener todos los productos de Loyverse
    loyverse_products = get_all_products()
    
    # Filtrar por IDs específicos de Loyverse si se proporcionan
    if opciones.get('loyverse_ids'):
        loyverse_ids = opciones.get('loyverse_ids')
        logger.info(f"🔍 Filtrando por {len(loyverse_ids)} IDs específicos de Loyverse")
        loyverse_products = [p for p in loyverse_products if p.get('id') in loyverse_ids]
        logger.info(f"✅ Filtrado completado. Productos encontrados: {len(loyverse_products)}")
    
    # Filtrar por categorías si es necesario
    if opciones.get('categorias'):
        categorias_solicitadas = opciones.get('categorias')
        # Convertir IDs de categoría a nombres usando el mapa
        # También permitimos filtrar por nombres directamente
        categorias_nombres = []
        for cat in categorias_solicitadas:
            if cat in category_map.values():
                categorias_nombres.append(cat)
            elif cat in category_map:
                categorias_nombres.append(category_map.get(cat))
        
        # Filtrar productos
        loyverse_products = [
            p for p in loyverse_products 
            if category_map.get(p.get('category_id')) in categorias_nombres
        ]
        
        logger.info(f"🔍 Filtrando por categorías: {categorias_nombres}. Productos filtrados: {len(loyverse_products)}")
    
    # Obtener productos en BD para actualización
    db_products = {
        p.loyverse_id: p for p in Producto.objects.filter(loyverse_id__isnull=False)
    }
    
    # Contadores
    stats = {
        'creados': 0,
        'actualizados': 0,
        'categorias_actualizadas': 0,
        'inactivos': 0,
        'total_loyverse': len(loyverse_products),
        'total_procesados': 0
    }
    
    # Procesar cada producto
    for producto_loyverse in loyverse_products:
        loyverse_id = producto_loyverse.get('id')
        if not loyverse_id:
            continue
        
        nombre = producto_loyverse.get('item_name', '')
        descripcion = producto_loyverse.get('description', '')
        categoria_id = producto_loyverse.get('category_id')
        categoria_nombre = category_map.get(categoria_id) if categoria_id else None
        
        # Detectar si el producto está eliminado
        if producto_loyverse.get('deleted_at'):
            if loyverse_id in db_products:
                # Marcar como inactivo en lugar de eliminar 
                db_product = db_products[loyverse_id]
                # En lugar de eliminar, consideramos que podría marcarse de alguna forma
                # que indique que el producto está inactivo
                stats['inactivos'] += 1
                logger.info(f"🚫 Producto marcado como inactivo: {nombre} (ID: {loyverse_id})")
            continue
        
        # Determinar si es precio variable desde Loyverse
        es_precio_variable = False
        if producto_loyverse.get('variants'):
            variant = producto_loyverse['variants'][0]
            es_precio_variable = variant.get('default_pricing_type') == 'VARIABLE'
        
        # Obtener fecha de actualización
        updated_at = None
        if producto_loyverse.get('updated_at'):
            updated_at = datetime.datetime.fromisoformat(
                producto_loyverse['updated_at'].replace('Z', '+00:00')
            )
        
        # Si el producto existe, actualizar datos básicos (excepto precios)
        if loyverse_id in db_products:
            db_product = db_products[loyverse_id]
            actualizar = False
            
            # Solo actualizar campos básicos, nunca precios
            if opciones.get('actualizar_todos_datos', True):
                if db_product.nombre != nombre or db_product.descripcion != descripcion:
                    db_product.nombre = nombre
                    db_product.descripcion = descripcion
                    actualizar = True
                    
                if db_product.categoria != categoria_nombre:
                    db_product.categoria = categoria_nombre
                    stats['categorias_actualizadas'] += 1
                    actualizar = True
                
                if db_product.es_precio_variable != es_precio_variable:
                    db_product.es_precio_variable = es_precio_variable
                    actualizar = True
                
                # Asegurar que aplicar_iva sea False para productos importados
                if hasattr(db_product, 'aplicar_iva') and db_product.aplicar_iva != False:
                    db_product.aplicar_iva = False
                    actualizar = True
                    
                if actualizar:
                    db_product.save()
                    stats['actualizados'] += 1
                    logger.info(f"✏️ Producto actualizado: {nombre} (ID: {loyverse_id})" + 
                               (f", categoría: {categoria_nombre}" if categoria_nombre else ""))
        else:
            # Crear nuevo producto preservando precio_base_usd como 0
            nuevo_producto = Producto(
                loyverse_id=loyverse_id,
                nombre=nombre,
                descripcion=descripcion,
                precio_base=Decimal('0'),
                precio_base_usd=Decimal('0'),
                categoria=categoria_nombre,
                fuente_actualizacion='loyverse',
                es_precio_variable=es_precio_variable,
                porcentaje_ganancia=Decimal('30.00'),
                tipo_tasa='BCV',
                aplicar_iva=False
            )
            
            if updated_at:
                nuevo_producto.ultima_actualizacion_precio = updated_at
            
            nuevo_producto.save()
            stats['creados'] += 1
            logger.info(f"➕ Nuevo producto creado: {nombre} (ID: {loyverse_id})" + 
                      (f", categoría: {categoria_nombre}" if categoria_nombre else ""))
                      
        stats['total_procesados'] += 1
    
    logger.info(f"✅ Importación completada. Creados: {stats['creados']}, " +
               f"Actualizados: {stats['actualizados']}, " +
               f"Categorías actualizadas: {stats['categorias_actualizadas']}")
    
    return stats

def aplicar_redondeo_especial(precio_bs):
    """
    Implementa la misma lógica de redondeo que se usa en el frontend.
    
    ¡IMPORTANTE! Esta función debe ser llamada siempre que se actualicen precios 
    en bolívares para mantener la consistencia de los precios en toda la aplicación.
    Cualquier parte del código que actualice precio_base sin usar esta función 
    causará inconsistencias en los precios.
    
    Args:
        precio_bs (Decimal): Precio en bolívares
        
    Returns:
        Decimal: Precio redondeado según reglas especiales
    """
    # Asegurarse de que sea un número
    if not precio_bs:
        return Decimal('0')
    
    # Primero redondeamos a 2 decimales para evitar problemas de precisión
    precio_bs = round(precio_bs * 100) / 100
    
    # Convertir a entero para trabajar con la parte entera
    entero = int(precio_bs)
    decimal = precio_bs - entero
    
    # Verificar si el número ya termina en 0 o 5
    residuo = entero % 10
    termina_en_5o0 = residuo == 0 or residuo == 5
    
    # Si ya termina en 0 o 5 y no tiene decimales, mantenerlo igual
    if termina_en_5o0 and decimal == 0:
        return Decimal(entero)
    
    # Para precios menores a 20
    if entero < 20:
        if entero < 5:
            # Números menores a 5
            if entero <= 2:
                # 1 y 2 se mantienen igual
                return Decimal(entero)
            else:
                # 3 y 4 se redondean a 5
                return Decimal('5')
        elif entero < 10:
            # Números entre 5 y 9
            if entero == 5 or entero == 6:
                return Decimal('5')
            else:
                # 7, 8, 9 se redondean a 10
                return Decimal('10')
        elif entero < 15:
            # Números entre 10 y 14
            if entero == 10 or entero == 11:
                return Decimal('10')
            else:
                # 12, 13, 14 se redondean a 15
                return Decimal('15')
        else:
            # Números entre 15 y 19
            if entero == 15 or entero == 16:
                return Decimal('15')
            else:
                # 17, 18, 19 se redondean a 20
                return Decimal('20')
    else:
        # Para precios mayores o iguales a 20
        # Redondear al 5 o 0 más cercano
        if residuo < 5:
            # Números terminados en 0, 1, 2, 3, 4 se redondean al siguiente 5
            # Si ya termina en 0, se mantiene igual
            if residuo == 0:
                return Decimal(entero)
            return Decimal(entero - residuo + 5)
        else:
            # Números terminados en 5, 6, 7, 8, 9 se redondean al siguiente 0
            # Si ya termina en 5, se mantiene igual
            if residuo == 5:
                return Decimal(entero)
            return Decimal(entero - residuo + 10)

def exportar_precios(opciones=None):
    """
    Exporta precios calculados desde BodegaClick hacia Loyverse.
    
    Args:
        opciones (dict): Opciones de filtrado y configuración:
            - categorias (list): Lista de categorías a exportar
            - tipo_tasa (str): Exportar solo productos con este tipo de tasa (BCV o PARALELO)
            - ids (list): IDs específicos de productos a exportar
            - tamaño_lote (int): Número de productos por lote (default: 100)
            
    Returns:
        dict: Estadísticas de la operación
    """
    if opciones is None:
        opciones = {}
    
    # Definir tamaño del lote (por defecto 100 productos por lote para mayor velocidad)
    tamaño_lote = opciones.get('tamaño_lote', 100)
    
    # Construir filtros
    filtros = Q(loyverse_id__isnull=False)
    
    if opciones.get('categorias'):
        filtros &= Q(categoria__in=opciones.get('categorias'))
    
    if opciones.get('tipo_tasa'):
        filtros &= Q(tipo_tasa=opciones.get('tipo_tasa'))
    
    if opciones.get('ids'):
        filtros &= Q(id__in=opciones.get('ids'))
    
    # Obtener últimas tasas de cambio
    try:
        tasa_bcv = TasaCambio.objects.filter(tipo='BCV').latest('fecha')
    except TasaCambio.DoesNotExist:
        logger.error("❌ No hay tasa BCV disponible para calcular precios")
        tasa_bcv = None
        
    try:
        tasa_paralelo = TasaCambio.objects.filter(tipo='PARALELO').latest('fecha')
    except TasaCambio.DoesNotExist:
        logger.error("❌ No hay tasa PARALELO disponible para calcular precios")
        tasa_paralelo = None
    
    # Obtener productos según filtros
    productos = Producto.objects.filter(filtros)
    total_productos = productos.count()
    
    logger.info(f"🔄 Exportando precios para {total_productos} productos en lotes de {tamaño_lote}")
    
    # Contadores
    stats = {
        'actualizados': 0,
        'fallidos': 0,
        'sin_precio': 0,
        'sin_tasa': 0,
        'total': total_productos,
        'lotes_procesados': 0
    }
    
    # Procesar productos en lotes
    for i in range(0, total_productos, tamaño_lote):
        lote_actual = productos[i:i+tamaño_lote]
        stats['lotes_procesados'] += 1
        
        logger.info(f"🔄 Procesando lote {stats['lotes_procesados']}: productos {i+1}-{min(i+tamaño_lote, total_productos)} de {total_productos}")
        
        # Procesar cada producto en el lote actual
        for producto in lote_actual:
            # Si no tiene precio_base_usd, no podemos actualizar
            if not producto.precio_base_usd or producto.precio_base_usd <= 0:
                logger.warning(f"⚠️ Producto {producto.nombre} no tiene precio_base_usd válido")
                stats['sin_precio'] += 1
                continue
            
            # Obtener tasa correspondiente
            if producto.tipo_tasa == 'BCV':
                tasa = tasa_bcv
            else:  # PARALELO
                tasa = tasa_paralelo
                
            if not tasa:
                logger.warning(f"⚠️ No hay tasa {producto.tipo_tasa} disponible para {producto.nombre}")
                stats['sin_tasa'] += 1
                continue
            
            # Calcular precio en Bs con el redondeo especial
            precio_bs_sin_redondeo = producto.precio_base_usd * tasa.valor
            precio_calculado = aplicar_redondeo_especial(precio_bs_sin_redondeo)
            
            try:
                # Obtener datos completos del producto de Loyverse
                loyverse_product = get_product_by_id(producto.loyverse_id)
                
                # Verificar que existan variantes
                if 'variants' in loyverse_product and loyverse_product['variants']:
                    # Crear copia para la actualización
                    update_data = loyverse_product.copy()
                    
                    # Actualizar precio en todas las variantes
                    for variant in update_data['variants']:
                        precio_anterior = variant.get('default_price', 0)
                        logger.info(f"🔄 Actualizando precio de {producto.nombre} " +
                                  f"de {precio_anterior} a {float(precio_calculado)} Bs " +
                                  f"(USD {float(producto.precio_base_usd)} * {tasa.tipo} {float(tasa.valor)}, con redondeo especial)")
                        
                        variant['default_price'] = float(precio_calculado)
                        
                        # Actualizar precio en tiendas
                        if 'stores' in variant:
                            for store in variant['stores']:
                                store['price'] = float(precio_calculado)
                    
                    # Enviar actualización a Loyverse
                    update_product_price(update_data)
                    
                    # Actualizar precio_base en el modelo para mantener coherencia
                    producto.precio_base = precio_calculado
                    producto.ultima_actualizacion_precio = datetime.datetime.now()
                    producto.save()
                    
                    stats['actualizados'] += 1
                    logger.info(f"✅ Precio actualizado para {producto.nombre}")
                else:
                    logger.warning(f"⚠️ Producto {producto.nombre} no tiene variantes en Loyverse")
                    stats['fallidos'] += 1
                    
            except Exception as e:
                logger.exception(f"❌ Error actualizando precio para {producto.nombre}: {str(e)}")
                stats['fallidos'] += 1
    
    logger.info(f"✅ Exportación completada en {stats['lotes_procesados']} lotes. " +
               f"Actualizados: {stats['actualizados']}, " +
               f"Fallidos: {stats['fallidos']}, " +
               f"Sin precio: {stats['sin_precio']}, " +
               f"Sin tasa: {stats['sin_tasa']}")
    
    return stats 