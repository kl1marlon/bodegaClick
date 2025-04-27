import requests
import json
import os
import time
import copy # Usaremos deepcopy por si acaso

# --- Configuración ---
# !! IMPORTANTE: USA EL TOKEN DE TU CUENTA DE DESTINO (NUEVA) !!
DESTINATION_API_TOKEN = os.environ.get("LOYVERSE_DESTINATION_API_TOKEN")
SNAPSHOT_DIR = "loyverse_snapshot" # Directorio con los JSON originales
MAPPING_FILE = "id_mapping_prod_to_dest.json" # Archivo con el mapeo Prod -> Dest
BASE_URL = "https://api.loyverse.com/v1.0"

# --- Cabeceras para la autenticación (Cuenta Destino) ---
HEADERS_GET = {
    "Authorization": f"Bearer {DESTINATION_API_TOKEN}",
    "Accept": "application/json"
}
HEADERS_POST = {
    "Authorization": f"Bearer {DESTINATION_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Contadores ---
update_success_count = 0
update_skipped_no_item_map = 0
update_skipped_no_category = 0
update_skipped_no_cat_map = 0
update_skipped_fetch_failed = 0
update_error_count_post = 0


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

def fetch_item_data(destination_item_id):
    """Obtiene los datos completos de un item desde la cuenta de destino."""
    url = f"{BASE_URL}/items/{destination_item_id}"
    print(f"    Obteniendo datos actuales de item ID (Dest): {destination_item_id}...")
    try:
        response = requests.get(url, headers=HEADERS_GET, timeout=30)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx, 5xx)
        print(f"      -> Datos obtenidos.")
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"      -> ERROR HTTP al obtener datos ({e.response.status_code}):")
        if e.response.status_code == 404:
             print(f"        Item ID {destination_item_id} no encontrado en la cuenta de destino.")
        else:
            try:
                error_details = e.response.json()
                print(f"        Respuesta de error detallada: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"        Respuesta de error (No JSON): {e.response.text}")
        return None # Indicar fallo
    except requests.exceptions.RequestException as e:
        print(f"      -> ERROR DE RED/CONEXIÓN al obtener datos: {e}")
        return None
    except Exception as e:
        print(f"      -> ERROR INESPERADO al obtener datos: {e}")
        return None

def send_full_item_update(item_payload):
    """Envía una solicitud POST con el payload completo del item para actualizarlo."""
    global update_success_count, update_error_count_post
    destination_item_id = item_payload.get("id")
    item_name = item_payload.get("item_name", "Nombre Desconocido")
    target_category_id = item_payload.get("category_id") # La categoría ya modificada

    url = f"{BASE_URL}/items"
    try:
        print(f"    Enviando actualización completa para item ID (Dest): {destination_item_id} ({item_name}) con category_id: {target_category_id}")
        # Descomentar para ver el payload completo enviado:
        # print(f"      Payload Completo: {json.dumps(item_payload, indent=2)}")
        response = requests.post(url, headers=HEADERS_POST, json=item_payload, timeout=45)

        if not response.ok: # Verificar si la respuesta NO fue exitosa (4xx, 5xx)
             print(f"      -> ERROR ({response.status_code}) al enviar actualización para item ID {destination_item_id}:")
             try:
                 error_details = response.json()
                 print(f"        Respuesta de error detallada: {json.dumps(error_details, indent=2)}")
             except json.JSONDecodeError:
                 print(f"        Respuesta de error (No JSON): {response.text}")
             update_error_count_post += 1
             return False # Indicar fallo

        print(f"      -> Éxito!")
        update_success_count += 1
        return True

    except requests.exceptions.RequestException as e:
        print(f"      -> ERROR DE RED/CONEXIÓN al enviar actualización: {e}")
        update_error_count_post += 1
        return False
    except Exception as e:
        print(f"      -> ERROR INESPERADO al enviar actualización: {e}")
        update_error_count_post += 1
        return False


# --- Proceso Principal de Actualización ---
def main():
    global update_skipped_no_item_map, update_skipped_no_category
    global update_skipped_no_cat_map, update_skipped_fetch_failed

    print("--- Verificación Inicial ---")
    # ... (mismas verificaciones iniciales que el script anterior) ...
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

    # Extraer mapeos específicos
    item_id_map = id_mappings.get("items", {})
    category_id_map = id_mappings.get("categories", {})
    # ... (advertencias si los mapas están vacíos) ...

    print("\n--- Iniciando Actualización de Categorías (Fetch-First) ---")
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

        # 2. Determinar el ID de categoría correcto en la cuenta de DESTINO (TARGET)
        target_destination_category_id = None # Por defecto, ninguna categoría
        if original_category_id:
            print(f"  Item original tenía category_id: {original_category_id}")
            target_destination_category_id = category_id_map.get(original_category_id)
            if target_destination_category_id:
                print(f"    -> Mapeado a ID de categoría destino (TARGET): {target_destination_category_id}")
            else:
                print(f"    -> ADVERTENCIA: No se encontró mapeo para la categoría original {original_category_id}. Se asignará SIN categoría (null).")
                update_skipped_no_cat_map += 1
        else:
            print(f"  Item original NO tenía categoría asignada. Se asignará SIN categoría (null).")
            update_skipped_no_category += 1

        # 3. Obtener los datos ACTUALES del item desde la cuenta DESTINO
        current_item_data = fetch_item_data(destination_item_id)
        if not current_item_data:
            print(f"  SALTANDO: No se pudieron obtener los datos actuales del item destino {destination_item_id}.")
            update_skipped_fetch_failed += 1
            continue # Saltar al siguiente item

        # 4. Preparar el Payload Modificado
        # Usar deepcopy para evitar modificar accidentalmente otras referencias si las hubiera
        update_payload = copy.deepcopy(current_item_data)

        # --- Eliminar campos de solo lectura o problemáticos para POST ---
        # La API a veces rechaza campos que solo devuelve en GET pero no acepta en POST/PUT
        # Es más seguro eliminar los campos de timestamp y handle.
        keys_to_remove_before_post = ["handle", "created_at", "updated_at", "deleted_at", "image_url"]
        # También eliminar 'components' si no los estamos manejando explícitamente
        if 'components' in update_payload and not update_payload.get('components'): # Si está presente pero vacío
             keys_to_remove_before_post.append('components')
        # Eliminar timestamps de las variantes también
        if "variants" in update_payload and isinstance(update_payload["variants"], list):
             for variant in update_payload["variants"]:
                 variant.pop("created_at", None)
                 variant.pop("updated_at", None)
                 variant.pop("deleted_at", None)
                 # Considerar si hay que quitar store_id de variantes si no se maneja
                 # Por ahora lo dejamos, ya que GET lo devuelve

        print(f"    Eliminando campos solo lectura/problemáticos antes de POST: {keys_to_remove_before_post}")
        for key in keys_to_remove_before_post:
            update_payload.pop(key, None)
        # ****************************************************************

        # --- Modificar SOLO la categoría ---
        print(f"    Modificando 'category_id' de '{current_item_data.get('category_id')}' a '{target_destination_category_id}'")
        update_payload['category_id'] = target_destination_category_id
        # ***********************************

        # 5. Enviar la solicitud de actualización con el payload completo
        send_full_item_update(update_payload)

        # 6. Pausa
        time.sleep(0.6) # Un poco más de pausa quizás

    print("\n--- Actualización de Categorías (Fetch-First) Completada ---")
    print(f"Resumen:")
    print(f"- Items procesados del archivo original: {total_items_original}")
    print(f"- Actualizaciones (POST) exitosas:      {update_success_count}")
    print(f"- Errores durante el POST:              {update_error_count_post}")
    print(f"- Items saltados (sin mapeo de item):   {update_skipped_no_item_map}")
    print(f"- Items saltados (fallo al obtenerlos): {update_skipped_fetch_failed}")
    print(f"- Items asignados sin categoría porque:")
    print(f"  - Originalmente no tenían categoría:    {update_skipped_no_category}")
    print(f"  - No se encontró mapeo para su cat.:   {update_skipped_no_cat_map}")


# --- Punto de Entrada ---
if __name__ == "__main__":
    main()