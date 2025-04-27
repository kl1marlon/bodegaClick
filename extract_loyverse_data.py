import requests
import json
import os
import time

# --- Configuración ---
# Carga el token desde una variable de entorno para seguridad
# O reemplaza directamente: API_TOKEN = "tu_token_api_aqui"
API_TOKEN = os.environ.get("LOYVERSE_API_TOKEN")
BASE_URL = "https://api.loyverse.com/v1.0"
OUTPUT_DIR = "loyverse_snapshot" # Directorio donde se guardarán los JSON

# --- Cabeceras para la autenticación ---
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

# --- Función para manejar la paginación ---
def fetch_paginated_data(endpoint, entity_key):
    """
    Obtiene todos los datos de un endpoint paginado usando cursor.

    Args:
        endpoint (str): El path del endpoint (ej: '/items').
        entity_key (str): La clave en la respuesta JSON que contiene la lista
                          de entidades (ej: 'items', 'categories').

    Returns:
        list: Una lista con todos los objetos obtenidos del endpoint.
              Retorna None si hay un error.
    """
    all_data = []
    url = f"{BASE_URL}{endpoint}"
    params = {'limit': 250} # Usar el límite máximo permitido

    print(f"Iniciando extracción desde {endpoint}...")
    total_fetched = 0

    while True:
        try:
            print(f"  Obteniendo lote (cursor={params.get('cursor', 'inicio')})...")
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status() # Lanza excepción para errores HTTP (4xx, 5xx)

            data = response.json()
            entities = data.get(entity_key, [])
            all_data.extend(entities)
            total_fetched += len(entities)
            print(f"  Obtenidos {len(entities)} {entity_key}. Total: {total_fetched}")

            cursor = data.get("cursor")
            if cursor:
                params['cursor'] = cursor
                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.5)
            else:
                # No hay más cursor, hemos terminado
                break

        except requests.exceptions.RequestException as e:
            print(f"Error durante la solicitud a {url}: {e}")
            print(f"Respuesta recibida (si existe): {response.text if 'response' in locals() else 'N/A'}")
            return None # Indicar fallo
        except json.JSONDecodeError:
            print(f"Error decodificando JSON desde {url}. Respuesta:")
            print(response.text)
            return None # Indicar fallo
        except Exception as e:
            print(f"Error inesperado obteniendo datos de {endpoint}: {e}")
            return None # Indicar fallo


    print(f"Extracción completa desde {endpoint}. Total final: {len(all_data)} {entity_key}.")
    return all_data

# --- Función para guardar datos en JSON ---
def save_to_json(data, filename):
    """Guarda los datos en un archivo JSON en el directorio de salida."""
    if data is None:
        print(f"No se guardará {filename} porque no se obtuvieron datos.")
        return False
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True) # Crea el directorio si no existe
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Datos guardados exitosamente en {filepath}")
        return True
    except Exception as e:
        print(f"Error guardando datos en {filename}: {e}")
        return False

# --- Proceso Principal ---
def main():
    if not API_TOKEN:
        print("Error: La variable de entorno LOYVERSE_API_TOKEN no está configurada.")
        print("Por favor, configura la variable o edita el script para incluir tu token.")
        return

    print("--- Iniciando Extracción de Datos de Loyverse ---")

    # 1. Extraer Categorías
    categories = fetch_paginated_data("/categories", "categories")
    save_to_json(categories, "categories.json")

    # 2. Extraer Impuestos (Taxes)
    taxes = fetch_paginated_data("/taxes", "taxes")
    save_to_json(taxes, "taxes.json")

    # 3. Extraer Modificadores (Opcional, descomentar si los usas)
    # modifiers = fetch_paginated_data("/modifiers", "modifiers")
    # save_to_json(modifiers, "modifiers.json")

    # 4. Extraer Proveedores (Opcional, descomentar si los usas)
    # suppliers = fetch_paginated_data("/suppliers", "suppliers")
    # save_to_json(suppliers, "suppliers.json")

    # 5. Extraer Items (con variantes y tiendas)
    items = fetch_paginated_data("/items", "items")
    save_to_json(items, "items.json")

    # 6. Extraer Tiendas (Stores) - Útil para mapear IDs de tienda si es necesario
    stores = fetch_paginated_data("/stores", "stores")
    save_to_json(stores, "stores.json")

    print("--- Extracción de Datos de Loyverse Completada ---")
    print(f"Los archivos JSON se encuentran en el directorio: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()