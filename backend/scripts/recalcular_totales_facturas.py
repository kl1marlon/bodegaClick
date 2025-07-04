#!/usr/bin/env python
"""
Script para recalcular los totales de las facturas según la nueva lógica.
Fecha: 2025-04-30
"""

import os
import sys
import logging
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carga variables de entorno desde el archivo .env
def cargar_variables_entorno():
    # Cargar desde la raíz del proyecto (2 niveles arriba)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    # Verificar que todas las variables necesarias estén definidas
    variables_requeridas = [
        'POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'
    ]
    
    for var in variables_requeridas:
        if not os.getenv(var):
            logger.error(f"Variable de entorno {var} no encontrada")
            sys.exit(1)
    
    logger.info("Variables de entorno cargadas correctamente")

# Conectar a la base de datos
def conectar_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        logger.info("Conexión a la base de datos establecida")
        return conn
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        sys.exit(1)

# Obtener todas las facturas con sus detalles
def obtener_facturas(conn):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Consulta para obtener todas las facturas con su tasa de cambio
            query = """
            SELECT 
                f.id, 
                f.numero, 
                f.moneda, 
                f.tasa_cambio_id,
                f.total_bs,
                f.total_usd,
                tc.valor as tasa_valor
            FROM 
                facturacion_factura f
            JOIN 
                facturacion_tasacambio tc ON f.tasa_cambio_id = tc.id
            ORDER BY 
                f.fecha DESC
            """
            cursor.execute(query)
            facturas = cursor.fetchall()
            logger.info(f"Se encontraron {len(facturas)} facturas")
            
            # Para cada factura, obtenemos sus detalles
            for factura in facturas:
                query_detalles = """
                SELECT 
                    id,
                    factura_id,
                    precio_compra_usd
                FROM 
                    facturacion_detallefactura
                WHERE 
                    factura_id = %s
                """
                cursor.execute(query_detalles, (factura['id'],))
                detalles = cursor.fetchall()
                factura['detalles'] = detalles
                
            return facturas
    except Exception as e:
        logger.error(f"Error al obtener facturas: {e}")
        conn.rollback()
        return []

# Recalcular los totales de una factura según la nueva lógica
def recalcular_totales(factura):
    try:
        total_bs = Decimal('0')
        total_usd = Decimal('0')
        
        # Asegurarse que tasa_valor no sea None
        if factura['tasa_valor'] is None:
            logger.warning(f"Factura #{factura['numero']} tiene tasa_valor None. Usando 1 como valor predeterminado.")
            tasa_cambio = Decimal('1')
        else:
            tasa_cambio = Decimal(str(factura['tasa_valor']))
        
        # Sumar los precio_compra_usd de todos los detalles, manejando posibles valores None
        suma_detalles = Decimal('0')
        for detalle in factura['detalles']:
            if detalle['precio_compra_usd'] is not None:
                suma_detalles += Decimal(str(detalle['precio_compra_usd']))
            else:
                logger.warning(f"Detalle id {detalle['id']} de factura #{factura['numero']} tiene precio_compra_usd None.")
        
        # Aplicar la lógica según la moneda
        if factura['moneda'] == 'BS':
            # Si la moneda es BS, el precio_compra_usd representa un monto en bolívares
            total_bs = suma_detalles
            total_usd = total_bs / tasa_cambio if tasa_cambio != Decimal('0') else Decimal('0')
        else:  # USD
            # Si la moneda es USD, el precio_compra_usd representa un monto en dólares
            total_usd = suma_detalles
            total_bs = total_usd * tasa_cambio
        
        return {
            'total_bs': total_bs.quantize(Decimal('0.01')),
            'total_usd': total_usd.quantize(Decimal('0.01'))
        }
    except Exception as e:
        logger.error(f"Error al recalcular totales para factura #{factura['numero']}: {e}")
        # Devolver los totales originales
        return {
            'total_bs': Decimal(str(factura['total_bs'])).quantize(Decimal('0.01')),
            'total_usd': Decimal(str(factura['total_usd'])).quantize(Decimal('0.01'))
        }

# Actualizar los totales de la factura en la base de datos
def actualizar_factura(conn, factura_id, nuevos_totales):
    try:
        with conn.cursor() as cursor:
            query = """
            UPDATE facturacion_factura
            SET 
                total_bs = %s,
                total_usd = %s
            WHERE 
                id = %s
            """
            cursor.execute(
                query, 
                (nuevos_totales['total_bs'], nuevos_totales['total_usd'], factura_id)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error al actualizar factura {factura_id}: {e}")
        conn.rollback()
        return False

# Función principal
def main():
    # Cargar variables de entorno
    cargar_variables_entorno()
    
    # Conectar a la base de datos
    conn = conectar_db()
    
    try:
        # Obtener todas las facturas
        facturas = obtener_facturas(conn)
        
        # Contador para facturas actualizadas
        facturas_actualizadas = 0
        
        # Para cada factura
        for factura in facturas:
            # Calcular nuevos totales
            nuevos_totales = recalcular_totales(factura)
            
            # Verificar si los totales han cambiado
            total_bs_actual = Decimal(str(factura['total_bs'])).quantize(Decimal('0.01'))
            total_usd_actual = Decimal(str(factura['total_usd'])).quantize(Decimal('0.01'))
            
            if (nuevos_totales['total_bs'] != total_bs_actual or 
                nuevos_totales['total_usd'] != total_usd_actual):
                
                # Actualizar la factura en la base de datos
                if actualizar_factura(conn, factura['id'], nuevos_totales):
                    facturas_actualizadas += 1
                    logger.info(f"Factura #{factura['numero']} actualizada: "
                                f"BS {total_bs_actual} -> {nuevos_totales['total_bs']}, "
                                f"USD {total_usd_actual} -> {nuevos_totales['total_usd']}")
        
        logger.info(f"Proceso completado. {facturas_actualizadas} facturas actualizadas de un total de {len(facturas)}")
    
    finally:
        # Cerrar la conexión a la base de datos
        if conn:
            conn.close()
            logger.info("Conexión a la base de datos cerrada")

if __name__ == "__main__":
    main()
