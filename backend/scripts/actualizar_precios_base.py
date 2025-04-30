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

def obtener_tasas_actuales(conn):
    """Obtiene las tasas actuales (BCV y PARALELO) desde la base de datos."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tipo, valor 
            FROM facturacion_tasacambio 
            WHERE tipo IN ('BCV', 'PARALELO')
            ORDER BY fecha DESC
            LIMIT 2
        """)
        
        tasas = {}
        for tipo, valor in cursor.fetchall():
            tasas[tipo] = valor
        
        cursor.close()
        
        # Verificar que se obtuvieron ambas tasas
        if 'BCV' not in tasas:
            log_mensaje("ADVERTENCIA: No se encontró la tasa BCV en la base de datos.")
            tasas['BCV'] = Decimal('0.0')
        if 'PARALELO' not in tasas:
            log_mensaje("ADVERTENCIA: No se encontró la tasa PARALELO en la base de datos.")
            tasas['PARALELO'] = Decimal('0.0')
            
        return tasas
    except Exception as e:
        log_mensaje(f"ERROR al obtener tasas actuales: {e}")
        return {'BCV': Decimal('0.0'), 'PARALELO': Decimal('0.0')}

def actualizar_tasa(conn, tipo, valor):
    """Actualiza o crea una tasa en la base de datos."""
    try:
        cursor = conn.cursor()
        # Verificar si ya existe una tasa de este tipo
        cursor.execute("""
            SELECT id FROM facturacion_tasacambio 
            WHERE tipo = %s
            ORDER BY fecha DESC
            LIMIT 1
        """, (tipo,))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Actualizar la tasa existente
            tasa_id = resultado[0]
            cursor.execute("""
                UPDATE facturacion_tasacambio 
                SET valor = %s, fecha = NOW()
                WHERE id = %s
            """, (valor, tasa_id))
            log_mensaje(f"Tasa {tipo} actualizada a {valor}")
        else:
            # Crear una nueva tasa
            cursor.execute("""
                INSERT INTO facturacion_tasacambio (tipo, valor, fecha)
                VALUES (%s, %s, NOW())
            """, (tipo, valor))
            log_mensaje(f"Nueva tasa {tipo} creada con valor {valor}")
        
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        conn.rollback()
        log_mensaje(f"ERROR al actualizar tasa {tipo}: {e}")
        return False

def obtener_y_confirmar_tasas(conn):
    """Solicita y confirma las tasas a utilizar."""
    # Obtener tasas actuales
    tasas_actuales = obtener_tasas_actuales(conn)
    
    log_mensaje(f"Tasas actuales: BCV = {tasas_actuales.get('BCV', 'No disponible')}, PARALELO = {tasas_actuales.get('PARALELO', 'No disponible')}")
    
    # Solicitar nuevas tasas
    nuevas_tasas = {}
    
    # Tasa BCV
    tasa_bcv = input(f'Introduce la tasa BCV (actual: {tasas_actuales.get("BCV", "No disponible")}): ')
    if tasa_bcv:
        try:
            nuevas_tasas['BCV'] = Decimal(tasa_bcv)
        except Exception:
            log_mensaje('Tasa BCV inválida. Debe ser un número decimal.')
            sys.exit(1)
    else:
        nuevas_tasas['BCV'] = tasas_actuales.get('BCV', Decimal('0.0'))
    
    # Tasa PARALELO
    tasa_paralelo = input(f'Introduce la tasa PARALELO (actual: {tasas_actuales.get("PARALELO", "No disponible")}): ')
    if tasa_paralelo:
        try:
            nuevas_tasas['PARALELO'] = Decimal(tasa_paralelo)
        except Exception:
            log_mensaje('Tasa PARALELO inválida. Debe ser un número decimal.')
            sys.exit(1)
    else:
        nuevas_tasas['PARALELO'] = tasas_actuales.get('PARALELO', Decimal('0.0'))
    
    # Confirmar tasas
    log_mensaje(f"Tasas a utilizar: BCV = {nuevas_tasas['BCV']}, PARALELO = {nuevas_tasas['PARALELO']}")
    confirm = input('¿Confirmas estas tasas? (s/n): ')
    if confirm.lower() != 's':
        log_mensaje('Operación cancelada por el usuario.')
        sys.exit(0)
    
    # Actualizar tasas en la base de datos
    for tipo, valor in nuevas_tasas.items():
        actualizar_tasa(conn, tipo, valor)
    
    return nuevas_tasas

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

def actualizar_precios(conn, tasas):
    """Actualiza los precios base de todos los productos usando la tasa correspondiente según tipo_tasa."""
    try:
        cursor = conn.cursor()
        
        # Obtener todos los productos con precio_base_usd > 0
        log_mensaje("Consultando productos con precio_base_usd > 0...")
        cursor.execute("""
            SELECT id, nombre, precio_base_usd, precio_base, tipo_tasa 
            FROM facturacion_producto 
            WHERE precio_base_usd > 0
        """)
        
        productos = cursor.fetchall()
        total_productos = len(productos)
        log_mensaje(f"Se encontraron {total_productos} productos para revisar")
        
        # Preparar para actualización
        actualizados = 0
        sin_cambios = 0
        productos_sin_cambios = []
        start_time = time.time()
        
        # Estadísticas por tipo de tasa
        stats_por_tasa = {'BCV': 0, 'PARALELO': 0, 'DESCONOCIDO': 0}
        
        # Actualizar cada producto si es necesario
        for i, (producto_id, nombre, precio_base_usd, precio_base_actual, tipo_tasa) in enumerate(productos):
            # Normalizar tipo_tasa a mayúsculas y asegurarse que sea uno de los tipos válidos
            if tipo_tasa:
                tipo_tasa_norm = tipo_tasa.upper()
            else:
                tipo_tasa_norm = None
            
            # Determinar qué tasa usar
            if tipo_tasa_norm in tasas:
                tasa_a_usar = tasas[tipo_tasa_norm]
                stats_por_tasa[tipo_tasa_norm] += 1
            else:
                # Si el tipo_tasa no es válido o es None, usar BCV por defecto
                tasa_a_usar = tasas['BCV']
                stats_por_tasa['DESCONOCIDO'] += 1
                log_mensaje(f"ADVERTENCIA: Producto ID {producto_id} tiene tipo_tasa '{tipo_tasa}' no reconocido. Usando tasa BCV.")
            
            # Calcular nuevo precio
            nuevo_precio = float(precio_base_usd) * float(tasa_a_usar)
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
                log_mensaje(f"Actualizado: Producto ID {producto_id} (Tasa: {tipo_tasa_norm}): {precio_base_actual} → {nuevo_precio_redondeado}", 
                           escribir_archivo=True)
                actualizados += 1
            else:
                sin_cambios += 1
                productos_sin_cambios.append({
                    'id': producto_id,
                    'nombre': nombre,
                    'precio_base_actual': precio_base_actual,
                    'tipo_tasa': tipo_tasa_norm,
                    'tasa_aplicada': tasa_a_usar
                })
        
        # Confirmar cambios
        conn.commit()
        
        # Calcular tiempo total
        tiempo_total = time.time() - start_time
        
        # Resumen final
        log_mensaje(f"==== RESUMEN DE ACTUALIZACIÓN ====")
        log_mensaje(f"Total productos revisados: {total_productos}")
        log_mensaje(f"Productos actualizados: {actualizados}")
        log_mensaje(f"Productos sin cambios: {sin_cambios}")
        log_mensaje(f"Tasas aplicadas: BCV = {tasas['BCV']}, PARALELO = {tasas['PARALELO']}")
        log_mensaje(f"Productos por tipo de tasa: BCV = {stats_por_tasa['BCV']}, PARALELO = {stats_por_tasa['PARALELO']}, DESCONOCIDO = {stats_por_tasa['DESCONOCIDO']}")
        log_mensaje(f"Tiempo total: {tiempo_total:.2f} segundos")
        log_mensaje(f"Velocidad: {total_productos/tiempo_total:.2f} productos/segundo")
        
        # Registrar lista de productos sin cambios en el log
        if productos_sin_cambios:
            log_mensaje(f"==== LISTA DE PRODUCTOS SIN CAMBIOS ({len(productos_sin_cambios)}) ====")
            for prod in productos_sin_cambios:
                log_mensaje(f"ID: {prod['id']} | Nombre: {prod['nombre']} | Precio actual: {prod['precio_base_actual']} | Tipo tasa: {prod['tipo_tasa']} | Tasa aplicada: {prod['tasa_aplicada']}")
        else:
            log_mensaje("No hubo productos sin cambios.")
        
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
    
    # Obtener y confirmar las tasas
    tasas = obtener_y_confirmar_tasas(conn)
    
    # Actualizar precios
    actualizar_precios(conn, tasas)
    
    # Cerrar conexión
    conn.close()
    log_mensaje("Conexión cerrada. Proceso completado.")
    log_mensaje("=== FIN DE ACTUALIZACIÓN DE PRECIOS BASE ===")
    
    # Mostrar ubicación del archivo de log
    print(f"\nSe ha generado un archivo de log en: {LOG_FILE}")

if __name__ == '__main__':
    main()
