import requests
import json
import os
import time

# --- Configuración ---
# !! IMPORTANTE: USA EL TOKEN DE TU CUENTA DE DESTINO (NUEVA) !!
# Carga el token desde una variable de entorno para seguridad
# O reemplaza directamente: DESTINATION_API_TOKEN = "tu_token_api_destino_aqui"
DESTINATION_API_TOKEN = os.environ.get("LOYVERSE_DESTINATION_API_TOKEN")
SNAPSHOT_DIR = "loyverse_snapshot" # Directorio con los JSON originales
MAPPING_FILE = "id_mapping_prod_to_dest.json" # Archivo con el mapeo Prod -> Dest
BASE_URL = "https://api.loyverse.com/v1.0"

# --- Cabeceras para la autenticación (Cuenta Destino) ---
HEADERS = {
    "Authorization": f"Bearer {DESTINATION_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Contadores ---
update_success_count = 0
update_skipped_no_item_map = 0
update_skipped_no_category = 0
update_skipped_no_cat_map = 0
update_error_count = 0

# --- Funciones Auxiliares ---

def load_json_file(filename):
    """Carga datos desde un archivo JSON."""
    if not os.path.exists(filename):
        print(f"ERROR CRÍTICO: Archivo requerido '{filename}' no encontrado.")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Archivo '{filename}' cargado exitosamente.")
            return data
    except Exception as e:
        print(f"Error crítico cargando archivo '{filename}': {e}")
        return None

def send_category_update(destination_item_id, destination_category_id, item_name):
    """Envía una solicitud POST para actualizar la categoría de un item existente."""
    global update_success_count, update_error_count

    url = f"{BASE_URL}/items"
    # ***** CORRECCIÓN: Añadir item_name al payload *****
    payload = {
        "id": destination_item_id,
        "item_name": item_name, # <--- AÑADIR ESTA LÍNEA
        "category_id": destination_category_id
    }
    # **************************************************

    try:
        # Solo imprimir el nombre una vez, ya no es necesario aquí si se imprime antes
        # print(f"  Intentando actualizar item ID (Dest): {destination_item_id} ({item_name}) -> category_id: {destination_category_id}") # Quitar o comentar
        print(f"  Enviando actualización para item ID (Dest): {destination_item_id} ({item_name}) con category_id: {destination_category_id}") # Más claro
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx, 5xx)

        print(f"    -> Éxito!")
        update_success_count += 1
        return True

    # ... (resto de la función sin cambios) ...
    except requests.exceptions.RequestException as e:
        print(f"    -> ERROR actualizando item ID {destination_item_id}: {e}")
        # ... (manejo de errores) ...
        update_error_count += 1
        return False
    except Exception as e:
        print(f"    -> ERROR inesperado actualizando item ID {destination_item_id}: {e}")
        update_error_count += 1
        return False

# --- Proceso Principal de Actualización ---
def main():
    global update_skipped_no_item_map, update_skipped_no_category, update_skipped_no_cat_map

    print("--- Verificación Inicial ---")
    abort_script = False
    if not DESTINATION_API_TOKEN:
        print("ERROR CRÍTICO: La variable de entorno LOYVERSE_DESTINATION_API_TOKEN no está configurada.")
        abort_script = True

    original_items_file = os.path.join(SNAPSHOT_DIR, "items.json")
    if not os.path.exists(original_items_file):
        print(f"ERROR CRÍTICO: El archivo de items originales '{original_items_file}' no existe.")
        abort_script = True

    if not os.path.exists(MAPPING_FILE):
        print(f"ERROR CRÍTICO: El archivo de mapeo '{MAPPING_FILE}' no existe.")
        abort_script = True

    if abort_script:
        print("Abortando script debido a errores de configuración o archivos faltantes.")
        return

    print("Configuración y archivos verificados.")

    # Cargar datos
    original_items_data = load_json_file(original_items_file)
    id_mappings = load_json_file(MAPPING_FILE)

    if not original_items_data or not id_mappings:
        print("Error cargando datos necesarios. Abortando.")
        return

    # Extraer mapeos específicos para facilitar acceso
    item_id_map = id_mappings.get("items", {})
    category_id_map = id_mappings.get("categories", {})

    if not item_id_map:
        print("Advertencia: No se encontraron mapeos de 'items' en el archivo de mapeo.")
    if not category_id_map:
        print("Advertencia: No se encontraron mapeos de 'categories' en el archivo de mapeo.")

    print("\n--- Iniciando Actualización de Categorías de Items (Cuenta Destino) ---")
    total_items_original = len(original_items_data)
    print(f"Se procesarán {total_items_original} items del archivo original...")

    for item_index, original_item in enumerate(original_items_data):
        original_item_id = original_item.get("id")
        original_item_name = original_item.get("item_name", "Nombre Desconocido")
        original_category_id = original_item.get("category_id") # Puede ser None

        print(f"\n[{item_index + 1}/{total_items_original}] Procesando item original: {original_item_name} (ID Orig: {original_item_id})")

        # 1. Encontrar el ID del item en la cuenta de DESTINO
        destination_item_id = item_id_map.get(original_item_id)
        if not destination_item_id:
            print(f"  SALTANDO: No se encontró mapeo para este item ID original en '{MAPPING_FILE}'.")
            update_skipped_no_item_map += 1
            continue

        print(f"  Encontrado ID de item destino: {destination_item_id}")

        # 2. Determinar el ID de categoría correcto en la cuenta de DESTINO
        destination_category_id = None # Por defecto, ninguna categoría
        if original_category_id:
            print(f"  Item original tenía category_id: {original_category_id}")
            # Buscar el ID de categoría original en el mapeo de categorías
            destination_category_id = category_id_map.get(original_category_id)
            if destination_category_id:
                print(f"    -> Mapeado a ID de categoría destino: {destination_category_id}")
            else:
                # El item original tenía categoría, pero no encontramos mapeo para ella
                print(f"    -> ADVERTENCIA: No se encontró mapeo para la categoría original {original_category_id} en '{MAPPING_FILE}'. Se asignará SIN categoría (null).")
                update_skipped_no_cat_map += 1
                # destination_category_id ya es None, así que la acción es desasignar
        else:
            # El item original NO tenía categoría
            print(f"  Item original NO tenía categoría asignada (category_id era null). Se asignará SIN categoría (null).")
            update_skipped_no_category += 1
            # destination_category_id ya es None

        # 3. Enviar la solicitud de actualización
        send_category_update(destination_item_id, destination_category_id, original_item_name)

        # 4. Pausa para evitar rate limiting
        time.sleep(0.5) # Ajusta si es necesario

    print("\n--- Actualización de Categorías Completada ---")
    print(f"Resumen:")
    print(f"- Items procesados del archivo original: {total_items_original}")
    print(f"- Actualizaciones exitosas:            {update_success_count}")
    print(f"- Errores durante la actualización:     {update_error_count}")
    print(f"- Items saltados (sin mapeo de item): {update_skipped_no_item_map}")
    print(f"- Items asignados sin categoría porque:")
    print(f"  - Originalmente no tenían categoría:  {update_skipped_no_category}")
    print(f"  - No se encontró mapeo para su cat.: {update_skipped_no_cat_map}")

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()