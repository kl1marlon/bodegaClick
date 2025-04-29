#!/usr/bin/env python
import os
import sys
import psycopg2
import time
import datetime
from decimal import Decimal
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

# Obtener variables de conexión a la base de datos
DB_HOST = os.getenv('POSTGRES_HOST')
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Configuración de logs
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'actualizacion_precios.log')
VERBOSE = True  # Mostrar logs detallados en consola

def log_mensaje(mensaje, escribir_archivo=True):
    """Registra un mensaje en el archivo de log y en consola."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {mensaje}"
    
    # Mostrar en consola
    if VERBOSE:
        print(log_line)
    
    # Escribir en archivo
    if escribir_archivo:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')

def conectar_bd():
    """Establece conexión con la base de datos PostgreSQL."""
    try:
        log_mensaje(f"Intentando conectar a {DB_NAME} en {DB_HOST}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        log_mensaje(f"Conexión exitosa a la base de datos: {DB_NAME}")
        return conn
    except Exception as e:
        log_mensaje(f"ERROR al conectar a la base de datos: {e}")
        sys.exit(1)

def obtener_tasa_paralelo():
    """Solicita y confirma la tasa paralelo a utilizar."""
    tasa = input('Introduce la tasa paralelo a usar: ')
    try:
        tasa = Decimal(tasa)
    except Exception:
        log_mensaje('Tasa inválida. Debe ser un número decimal.')
        sys.exit(1)
    
    confirm = input(f'¿Confirmas la tasa {tasa}? (s/n): ')
    if confirm.lower() != 's':
        log_mensaje('Operación cancelada por el usuario.')
        sys.exit(0)
    
    log_mensaje(f"Tasa confirmada: {tasa}")
    return tasa

def aplicar_redondeo_especial(precio):
    """
    Aplica reglas de redondeo especiales a precios en bolívares, imitando la lógica del frontend.
    """
    from math import floor
    try:
        precio = float(precio)
    except Exception:
        return precio
    # Redondear a 2 decimales
    precio = round(precio, 2)
    entero = floor(precio)
    decimal = precio - entero
    residuo = entero % 10
    termina_en_5o0 = residuo == 0 or residuo == 5
    # Si termina en 0 o 5 y no tiene decimales, mantener igual
    if termina_en_5o0 and decimal == 0:
        return float(entero)
    # Precios menores a 20
    if entero < 20:
        if entero < 5:
            if entero <= 2:
                return float(entero)
            else:
                return 5.0
        elif entero < 10:
            if entero == 5:
                return 5.0
            elif decimal > 0 and entero == 5:
                return 10.0
            elif entero > 5:
                return 10.0
        elif entero < 15:
            if entero == 10 or entero == 11:
                return 10.0
            else:
                return 15.0
        else:  # 15 <= entero < 20
            if entero == 15 or entero == 16:
                return 15.0
            else:
                return 20.0
    # Para 20 o más, redondear al múltiplo de 5 más cercano hacia arriba
    resto = entero % 5
    if resto == 0 and decimal == 0:
        return float(entero)
    proximo_multiplo_5 = entero + (5 - resto) if resto != 0 else entero
    return float(proximo_multiplo_5)

def actualizar_precios(conn, tasa):
    """Actualiza los precios base de todos los productos usando la tasa indicada."""
    try:
        cursor = conn.cursor()
        
        # Primero, obtener todos los productos con precio_base_usd > 0
        log_mensaje("Consultando productos con precio_base_usd > 0...")
        cursor.execute("""
            SELECT id, precio_base_usd, precio_base 
            FROM facturacion_producto 
            WHERE precio_base_usd > 0
        """)
        
        productos = cursor.fetchall()
        total_productos = len(productos)
        log_mensaje(f"Se encontraron {total_productos} productos para revisar")
        
        # Preparar para actualización
        actualizados = 0
        sin_cambios = 0
        start_time = time.time()
        
        # Actualizar cada producto si es necesario
        for i, (producto_id, precio_base_usd, precio_base_actual) in enumerate(productos):
            # Calcular nuevo precio
            nuevo_precio = float(precio_base_usd) * float(tasa)
            nuevo_precio_redondeado = aplicar_redondeo_especial(nuevo_precio)
            
            # Mostrar progreso cada 50 productos o al 25%, 50%, 75% y 100%
            if (i+1) % 50 == 0 or (i+1) / total_productos in [0.25, 0.5, 0.75, 1.0]:
                porcentaje = ((i+1) / total_productos) * 100
                tiempo_transcurrido = time.time() - start_time
                log_mensaje(f"Progreso: {i+1}/{total_productos} ({porcentaje:.1f}%) - Tiempo: {tiempo_transcurrido:.2f}s")
            
            # Solo actualizar si hay cambio
            if float(precio_base_actual) != float(nuevo_precio_redondeado):
                cursor.execute("""
                    UPDATE facturacion_producto 
                    SET precio_base = %s 
                    WHERE id = %s
                """, (nuevo_precio_redondeado, producto_id))
                
                # Registrar detalle del cambio
                log_mensaje(f"Actualizado: Producto ID {producto_id}: {precio_base_actual} → {nuevo_precio_redondeado}", 
                           escribir_archivo=True)
                actualizados += 1
            else:
                sin_cambios += 1
        
        # Confirmar cambios
        conn.commit()
        
        # Calcular tiempo total
        tiempo_total = time.time() - start_time
        
        # Resumen final
        log_mensaje(f"==== RESUMEN DE ACTUALIZACIÓN ====")
        log_mensaje(f"Total productos revisados: {total_productos}")
        log_mensaje(f"Productos actualizados: {actualizados}")
        log_mensaje(f"Productos sin cambios: {sin_cambios}")
        log_mensaje(f"Tasa aplicada: {tasa}")
        log_mensaje(f"Tiempo total: {tiempo_total:.2f} segundos")
        log_mensaje(f"Velocidad: {total_productos/tiempo_total:.2f} productos/segundo")
        
    except Exception as e:
        conn.rollback()
        log_mensaje(f"ERROR al actualizar precios: {e}")
    finally:
        cursor.close()

def main():
    """Función principal del script."""
    log_mensaje("=== INICIO DE ACTUALIZACIÓN DE PRECIOS BASE ===")
    
    # Conectar a la base de datos
    conn = conectar_bd()
    
    # Obtener y confirmar la tasa
    tasa = obtener_tasa_paralelo()
    
    # Actualizar precios
    actualizar_precios(conn, tasa)
    
    # Cerrar conexión
    conn.close()
    log_mensaje("Conexión cerrada. Proceso completado.")
    log_mensaje("=== FIN DE ACTUALIZACIÓN DE PRECIOS BASE ===")
    
    # Mostrar ubicación del archivo de log
    print(f"\nSe ha generado un archivo de log en: {LOG_FILE}")

if __name__ == '__main__':
    main()
