import os
import redis
import sys

def test_redis_connection():
    """Prueba la conexión a Redis usando las variables de entorno."""
    redis_url = os.environ.get('REDIS_URL')
    
    if not redis_url:
        print("Error: REDIS_URL no está definida en las variables de entorno.")
        sys.exit(1)
    
    print(f"Intentando conectar a Redis usando URL: {redis_url}")
    
    try:
        # Crear conexión a Redis
        r = redis.from_url(redis_url)
        
        # Probar operación de ping
        response = r.ping()
        
        if response:
            print("¡Conexión exitosa a Redis!")
            
            # Probar operaciones básicas
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            print(f"Prueba de operación set/get: {value.decode('utf-8')}")
            
            # Limpiar
            r.delete('test_key')
            return True
        else:
            print("Error: No se recibió respuesta al ping de Redis.")
            return False
    except redis.exceptions.ConnectionError as e:
        print(f"Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    test_redis_connection() 