#!/usr/bin/env python
import os
import sys
import django
import argparse
from decimal import Decimal
from django.db import connection

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importar los modelos después de configurar Django
from facturacion.models import Producto, TasaCambio, Factura, DetalleFactura, Webhook

def listar_productos(limit=10, offset=0, buscar=None):
    """Listar productos con paginación y filtro opcional."""
    queryset = Producto.objects.all()
    
    if buscar:
        queryset = queryset.filter(nombre__icontains=buscar)
    
    total = queryset.count()
    productos = queryset.order_by('nombre')[offset:offset+limit]
    
    print(f"\n=== PRODUCTOS ({total} encontrados) ===")
    print(f"{'ID':<5} {'NOMBRE':<30} {'PRECIO BASE':<12} {'STOCK':<8} {'CATEGORÍA':<20}")
    print("-" * 80)
    
    for producto in productos:
        print(f"{producto.id:<5} {producto.nombre[:28]:<30} {producto.precio_base:<12} {producto.stock_actual:<8} {(producto.categoria or '')[:18]:<20}")
    
    print("-" * 80)

def listar_tasas_cambio(limit=10):
    """Listar últimas tasas de cambio."""
    tasas = TasaCambio.objects.all().order_by('-fecha')[:limit]
    
    print(f"\n=== TASAS DE CAMBIO (últimas {limit}) ===")
    print(f"{'ID':<5} {'TIPO':<10} {'VALOR':<10} {'FECHA':<20}")
    print("-" * 50)
    
    for tasa in tasas:
        print(f"{tasa.id:<5} {tasa.tipo:<10} {tasa.valor:<10} {tasa.fecha.strftime('%Y-%m-%d %H:%M'):<20}")
    
    print("-" * 50)

def listar_facturas(limit=10, offset=0):
    """Listar facturas con paginación."""
    total = Factura.objects.count()
    facturas = Factura.objects.all().order_by('-fecha')[offset:offset+limit]
    
    print(f"\n=== FACTURAS ({total} total) ===")
    print(f"{'ID':<5} {'NÚMERO':<15} {'FECHA':<20} {'MONEDA':<8} {'TOTAL BS':<12} {'TOTAL USD':<12}")
    print("-" * 80)
    
    for factura in facturas:
        print(f"{factura.id:<5} {factura.numero:<15} {factura.fecha.strftime('%Y-%m-%d %H:%M'):<20} {factura.moneda:<8} {factura.total_bs:<12} {factura.total_usd:<12}")
    
    print("-" * 80)

def ver_detalles_factura(factura_id):
    """Ver detalles de una factura específica."""
    try:
        factura = Factura.objects.get(id=factura_id)
        detalles = DetalleFactura.objects.filter(factura=factura)
        
        print(f"\n=== DETALLES DE FACTURA #{factura.numero} ===")
        print(f"Fecha: {factura.fecha.strftime('%Y-%m-%d %H:%M')}")
        print(f"Moneda: {factura.moneda}")
        print(f"Tasa de cambio: {factura.tasa_cambio.valor if factura.tasa_cambio else 'N/A'}")
        print(f"Total BS: {factura.total_bs}")
        print(f"Total USD: {factura.total_usd}")
        print(f"Sincronizado con Loyverse: {'Sí' if factura.sincronizado_loyverse else 'No'}")
        
        print("\nProductos:")
        print(f"{'PRODUCTO':<30} {'CANTIDAD':<10} {'PRECIO UNIT.':<15} {'TOTAL':<15}")
        print("-" * 75)
        
        for detalle in detalles:
            print(f"{detalle.producto.nombre[:28]:<30} {detalle.cantidad:<10} {detalle.precio_unitario:<15} {detalle.total:<15}")
        
        print("-" * 75)
        print(f"TOTAL: {factura.total_bs if factura.moneda == 'BS' else factura.total_usd}")
        
    except Factura.DoesNotExist:
        print(f"Error: No se encontró la factura con ID {factura_id}")

def ver_detalle_producto(producto_id):
    """Ver información detallada de un producto específico."""
    try:
        producto = Producto.objects.get(id=producto_id)
        
        print(f"\n=== DETALLE DEL PRODUCTO ===")
        print(f"ID: {producto.id}")
        print(f"ID Loyverse: {producto.loyverse_id}")
        print(f"Nombre: {producto.nombre}")
        print(f"Descripción: {producto.descripcion or 'N/A'}")
        print(f"Categoría: {producto.categoria or 'N/A'}")
        print(f"Precio base: {producto.precio_base}")
        print(f"Precio de compra: {producto.precio_compra}")
        print(f"Precio de compra USD: {producto.precio_compra_usd}")
        print(f"Precio de venta calculado: {producto.precio_venta_calculado}")
        print(f"Stock actual: {producto.stock_actual}")
        print(f"Última actualización stock: {producto.ultima_actualizacion_stock}")
        print(f"Última actualización precio: {producto.ultima_actualizacion_precio}")
        print(f"Unidades por paquete: {producto.unidades_paquete}")
        print(f"Unidades de compra: {producto.unidades_compra}")
        print(f"Aplicar IVA: {'Sí' if producto.aplicar_iva else 'No'}")
        print(f"Porcentaje de ganancia: {producto.porcentaje_ganancia}%")
        print(f"Tipo de tasa: {producto.tipo_tasa}")
        print(f"Es precio variable: {'Sí' if producto.es_precio_variable else 'No'}")
        print(f"Fuente de actualización: {producto.fuente_actualizacion}")
        print(f"Creado: {producto.created_at}")
        print(f"Actualizado: {producto.updated_at}")
        
    except Producto.DoesNotExist:
        print(f"Error: No se encontró el producto con ID {producto_id}")

def mostrar_estructura_producto():
    """Muestra información detallada sobre la estructura del modelo Producto en la base de datos."""
    print("\n=== ESTRUCTURA DEL MODELO PRODUCTO ===")
    
    # Información del modelo desde Django
    print("\nCampos del modelo Producto:")
    print(f"{'CAMPO':<25} {'TIPO':<20} {'NULO':<8} {'DEFAULT':<15} {'DESCRIPCIÓN'}")
    print("-" * 100)
    
    for field in Producto._meta.fields:
        tipo = f"{field.get_internal_type()}"
        if hasattr(field, 'max_length') and field.max_length:
            tipo += f"({field.max_length})"
        
        nulo = "Sí" if field.null else "No"
        default = str(field.default) if field.default != django.db.models.fields.NOT_PROVIDED else ""
        help_text = field.help_text if field.help_text else ""
        
        print(f"{field.name:<25} {tipo:<20} {nulo:<8} {default[:15]:<15} {help_text}")
    
    # Información del esquema real de la base de datos
    print("\n\nEstructura real en la base de datos PostgreSQL:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                   is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'facturacion_producto'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print(f"{'COLUMNA':<25} {'TIPO':<20} {'LONGITUD':<10} {'NULO':<8} {'DEFAULT'}")
        print("-" * 100)
        
        for col in columns:
            col_name, data_type, max_length, nullable, default = col
            max_length_str = str(max_length) if max_length is not None else "-"
            nullable_str = "Sí" if nullable == 'YES' else "No"
            default_str = str(default)[:20] if default is not None else ""
            
            print(f"{col_name:<25} {data_type:<20} {max_length_str:<10} {nullable_str:<8} {default_str}")
    
    # Contar registros
    total_productos = Producto.objects.count()
    print(f"\nTotal de registros en la tabla de Productos: {total_productos}")
    
    # Información sobre campos con valores únicos
    print("\nValores únicos por categoría:")
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT categoria FROM facturacion_producto WHERE categoria IS NOT NULL ORDER BY categoria;")
        categorias = [row[0] for row in cursor.fetchall()]
        
        for cat in categorias:
            count = Producto.objects.filter(categoria=cat).count()
            print(f" - {cat}: {count} productos")
    
    # Estadísticas básicas sobre algunos campos numéricos
    print("\nEstadísticas sobre precios:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                MIN(precio_base) as min_precio, 
                MAX(precio_base) as max_precio,
                AVG(precio_base) as avg_precio,
                MIN(stock_actual) as min_stock,
                MAX(stock_actual) as max_stock,
                AVG(stock_actual) as avg_stock
            FROM facturacion_producto;
        """)
        stats = cursor.fetchone()
        
        if stats:
            min_precio, max_precio, avg_precio, min_stock, max_stock, avg_stock = stats
            print(f" - Precio mínimo: {min_precio}")
            print(f" - Precio máximo: {max_precio}")
            print(f" - Precio promedio: {avg_precio:.2f}")
            print(f" - Stock mínimo: {min_stock}")
            print(f" - Stock máximo: {max_stock}")
            print(f" - Stock promedio: {avg_stock:.2f}")
    
    # Mostrar algunos campos de ejemplo
    print("\nEjemplo de datos (primer producto):")
    try:
        primer_producto = Producto.objects.first()
        if primer_producto:
            for field in Producto._meta.fields:
                value = getattr(primer_producto, field.name)
                print(f" - {field.name}: {value}")
    except Exception as e:
        print(f"Error al obtener ejemplo: {e}")

def menu_principal():
    """Menú principal interactivo."""
    while True:
        print("\n====== CONSULTA DE BASE DE DATOS ======")
        print("1. Listar productos")
        print("2. Ver detalle de un producto")
        print("3. Listar tasas de cambio")
        print("4. Listar facturas")
        print("5. Ver detalles de una factura")
        print("6. Mostrar estructura del modelo Producto")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            limit = int(input("Número de productos a mostrar (default 10): ") or 10)
            offset = int(input("Desde qué posición (default 0): ") or 0)
            buscar = input("Buscar por nombre (deje vacío para mostrar todos): ")
            listar_productos(limit=limit, offset=offset, buscar=buscar)
        
        elif opcion == "2":
            producto_id = input("Ingrese el ID del producto: ")
            ver_detalle_producto(int(producto_id))
        
        elif opcion == "3":
            limit = int(input("Número de tasas a mostrar (default 10): ") or 10)
            listar_tasas_cambio(limit=limit)
        
        elif opcion == "4":
            limit = int(input("Número de facturas a mostrar (default 10): ") or 10)
            offset = int(input("Desde qué posición (default 0): ") or 0)
            listar_facturas(limit=limit, offset=offset)
        
        elif opcion == "5":
            factura_id = input("Ingrese el ID de la factura: ")
            ver_detalles_factura(int(factura_id))
            
        elif opcion == "6":
            mostrar_estructura_producto()
        
        elif opcion == "0":
            print("¡Hasta pronto!")
            break
        
        else:
            print("Opción no válida. Intente nuevamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Consultar datos de la base de datos de facturación')
    parser.add_argument('--menu', action='store_true', help='Mostrar menú interactivo')
    parser.add_argument('--productos', action='store_true', help='Listar productos')
    parser.add_argument('--producto', type=int, help='Ver detalle de un producto por ID')
    parser.add_argument('--tasas', action='store_true', help='Listar tasas de cambio')
    parser.add_argument('--facturas', action='store_true', help='Listar facturas')
    parser.add_argument('--factura', type=int, help='Ver detalle de una factura por ID')
    parser.add_argument('--estructura', action='store_true', help='Mostrar estructura del modelo Producto')
    parser.add_argument('--limit', type=int, default=10, help='Límite de registros a mostrar')
    parser.add_argument('--offset', type=int, default=0, help='Desde qué registro empezar')
    parser.add_argument('--buscar', type=str, help='Buscar productos por nombre')
    
    args = parser.parse_args()
    
    # Si no se proporciona ningún argumento o se especifica --menu, mostrar el menú interactivo
    if len(sys.argv) == 1 or args.menu:
        menu_principal()
    else:
        if args.productos:
            listar_productos(limit=args.limit, offset=args.offset, buscar=args.buscar)
        
        if args.producto is not None:
            ver_detalle_producto(args.producto)
        
        if args.tasas:
            listar_tasas_cambio(limit=args.limit)
        
        if args.facturas:
            listar_facturas(limit=args.limit, offset=args.offset)
        
        if args.factura is not None:
            ver_detalles_factura(args.factura)
            
        if args.estructura:
            mostrar_estructura_producto() 