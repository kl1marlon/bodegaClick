import requests
import json
import os
import time
import copy # Para hacer copias profundas de los diccionarios

# --- Configuración ---
# !! IMPORTANTE: USA EL TOKEN DE TU CUENTA DE DESTINO (NUEVA) !!
# Carga el token desde una variable de entorno para seguridad
# O reemplaza directamente: DESTINATION_API_TOKEN = "tu_token_api_destino_aqui"
DESTINATION_API_TOKEN = os.environ.get('DESTINATION_API_TOKEN')
SNAPSHOT_DIR = "loyverse_snapshot" # Directorio con los JSON extraídos
BASE_URL = "https://api.loyverse.com/v1.0"

# !! IMPORTANTE: IDs de las tiendas en la CUENTA DE DESTINO !!
# Necesitas saber los IDs de las tiendas donde quieres que los productos
# estén disponibles y tengan precios/stock. Obtenlos manualmente desde la
# interfaz de Loyverse (Ajustes > Tiendas) o usando la API /stores en la cuenta destino.
# Si solo tienes una tienda, pon su ID aquí. Si tienes varias y quieres
# mapear, necesitarás una lógica más compleja.
DESTINATION_STORE_IDS = ["1b91c62c-fe7e-4998-a2f6-200e3a082f34"] # Reemplaza/añade IDs

# --- Cabeceras para la autenticación (Cuenta Destino) ---
HEADERS = {
    "Authorization": f"Bearer {DESTINATION_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Mapeo de IDs (Original -> Nuevo) ---
# Este diccionario guardará la relación entre los IDs de producción y los nuevos IDs de destino
id_mapping = {
    "categories": {},
    "taxes": {},
    "modifiers": {},
    "suppliers": {},
    "items": {},
    "variants": {},
    "stores": {} # Podríamos mapear tiendas si fuera necesario un mapeo complejo
}

# --- Funciones Auxiliares ---

def load_json_file(filename):
    """Carga datos desde un archivo JSON en el directorio snapshot."""
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    if not os.path.exists(filepath):
        print(f"Advertencia: Archivo {filepath} no encontrado. Saltando...")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Archivo {filepath} cargado exitosamente.")
            return data
    except Exception as e:
        print(f"Error cargando archivo {filepath}: {e}")
        return None

def send_post_request(endpoint, payload, original_id_type, original_id):
    """Envía una solicitud POST y maneja la respuesta, guardando el mapeo de ID."""
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"  Enviando POST a {endpoint} para ID original ({original_id_type}): {original_id}")
        # Descomentar la línea siguiente para depurar el payload exacto que se envía
        # print(f"  Payload: {json.dumps(payload, indent=2)}")
        response = requests.post(url, headers=HEADERS, json=payload, timeout=45)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx, 5xx)

        response_data = response.json()
        new_id = None

        # Intentar obtener el ID principal de la respuesta (para item, category, tax)
        if isinstance(response_data, dict):
            new_id = response_data.get("id")

        # Lógica específica para variantes:
        # Las variantes se crean junto con el item, sus nuevos IDs están en la respuesta del item.
        # El mapeo de variantes se hará después de la llamada POST al item.
        if not new_id and original_id_type == "variants":
             print(f"  Advertencia: No se encontró 'id' directo para variante {original_id}. Se mapeará después desde la respuesta del item.")
             # No retornamos la data aquí, el mapeo ocurre tras el POST del item.
             return response_data # Devolver la data del item para el mapeo posterior de variantes

        if new_id:
            print(f"  Éxito! Nuevo ID ({original_id_type}): {new_id} (Original: {original_id})")
            id_mapping[original_id_type][original_id] = new_id
            return response_data # Devolver la respuesta completa por si se necesita más info
        elif original_id_type != "variants": # Si no es variante y no hay ID, es raro
            print(f"  Advertencia/Error: No se encontró 'id' en la respuesta para {original_id_type} {original_id}. Respuesta: {response_data}")
            return response_data # Devolver respuesta para posible análisis

        return response_data # Retornar respuesta en caso de variantes (o si no hubo ID pero no fue error)

    except requests.exceptions.RequestException as e:
        print(f"Error en request a {url} para ID original {original_id}: {e}")
        if 'response' in locals() and response is not None:
            # Intentar decodificar el error de Loyverse si es JSON
            try:
                error_details = response.json()
                print(f"  Respuesta de error ({response.status_code}): {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"  Respuesta de error ({response.status_code}) (No JSON): {response.text}")
        else:
            print(f"  No hubo respuesta del servidor.")
        return None
    except Exception as e:
        print(f"Error inesperado procesando {original_id_type} {original_id}: {e}")
        return None

# --- Funciones de Procesamiento por Tipo de Entidad ---

def process_categories(categories_data):
    print("\n--- Procesando Categorías ---")
    if not categories_data:
        print("No hay datos de categorías para procesar.")
        return
    for category in categories_data:
        original_id = category.get("id")
        if not original_id: continue

        payload = {
            "name": category.get("name"),
            "color": category.get("color")
            # Nota: El manejo de parent_id (subcategorías) requeriría crearlas
            # en el orden correcto o hacer una segunda pasada para actualizar parent_id.
            # Por simplicidad, aquí no se maneja parent_id.
        }
        # Eliminar claves con valor None para evitar posibles errores
        payload = {k: v for k, v in payload.items() if v is not None}

        send_post_request("/categories", payload, "categories", original_id)
        time.sleep(0.5) # Pausa para evitar rate limiting

def process_taxes(taxes_data):
    print("\n--- Procesando Impuestos ---")
    if not taxes_data:
        print("No hay datos de impuestos para procesar.")
        return
    for tax in taxes_data:
        original_id = tax.get("id")
        if not original_id: continue

        payload = {
            "name": tax.get("name"),
            "type": tax.get("type"),
            "rate": tax.get("rate"),
            "is_default": tax.get("is_default", False), # Asegurar valor booleano
            "included_in_price": tax.get("included_in_price", False) # Asegurar valor booleano
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        send_post_request("/taxes", payload, "taxes", original_id)
        time.sleep(0.5)

# Aquí podrías añadir process_modifiers, process_suppliers si los necesitas

def process_items(items_data):
    print("\n--- Procesando Items ---")
    if not items_data:
        print("No hay datos de items para procesar.")
        return

    for item_index, item in enumerate(items_data):
        original_item_id = item.get("id")
        if not original_item_id:
            print(f"Advertencia: Se encontró un item sin ID en el índice {item_index}. Saltando...")
            continue

        print(f"\n[{item_index + 1}/{len(items_data)}] Procesando Item: {item.get('item_name')} (Original ID: {original_item_id})")

        # Preparar payload base del item
        item_payload = copy.deepcopy(item) # Copia profunda para no modificar el original

        # --- Eliminar campos que no se envían o se manejan diferente ---
        # Claves generadas por API, manejadas separadamente, o problemáticas en POST inicial
        keys_to_remove = [
            "id",               # Se genera nuevo ID
            "handle",           # Se genera nuevo handle
            "created_at",       # Fecha de creación original
            "updated_at",       # Fecha de actualización original
            "deleted_at",       # Fecha de borrado original
            "image_url",        # Las imágenes no se migran vía API estándar
            "variants",         # Se procesarán y añadirán separadamente al payload
            "components"        # !!! IMPORTANTE: Eliminar para evitar error 400 en POST inicial !!!
        ]
        for key in keys_to_remove:
            item_payload.pop(key, None) # pop eliminará la clave si existe

        # --- Establecer reference_id ---
        item_payload["reference_id"] = original_item_id

        # --- Mapear IDs de dependencias ---
        # Categoría
        original_cat_id = item.get("category_id")
        if original_cat_id:
            new_cat_id = id_mapping["categories"].get(original_cat_id)
            if new_cat_id:
                item_payload["category_id"] = new_cat_id
                print(f"  Mapeado category_id: {original_cat_id} -> {new_cat_id}")
            else:
                print(f"  Advertencia: No se encontró mapeo para category_id {original_cat_id}. Se establecerá a null.")
                item_payload["category_id"] = None # O quitar la clave: item_payload.pop("category_id", None)
        else:
             item_payload["category_id"] = None # Asegurarse que sea null si no existe o no se quiere

        # Impuestos (tax_ids)
        original_tax_ids = item.get("tax_ids", [])
        new_tax_ids = []
        if original_tax_ids:
            print(f"  Mapeando tax_ids: {original_tax_ids}")
            for tax_id in original_tax_ids:
                new_id = id_mapping["taxes"].get(tax_id)
                if new_id:
                    new_tax_ids.append(new_id)
                    print(f"    - Mapeado: {tax_id} -> {new_id}")
                else:
                    print(f"    - Advertencia: No se encontró mapeo para tax_id {tax_id}. Se omitirá.")
        item_payload["tax_ids"] = new_tax_ids

        # Modificadores (modifiers_ids) - Asegúrate que la key 'modifiers_ids' sea correcta según tu JSON
        original_mod_ids = item.get("modifiers_ids", [])
        new_mod_ids = []
        if original_mod_ids:
            print(f"  Mapeando modifiers_ids: {original_mod_ids}")
            for mod_id in original_mod_ids:
                # Asegúrate que la clave 'modifiers' existe en id_mapping si procesaste modificadores
                new_id = id_mapping.get("modifiers", {}).get(mod_id)
                if new_id:
                    new_mod_ids.append(new_id)
                    print(f"    - Mapeado: {mod_id} -> {new_id}")
                else:
                    print(f"    - Advertencia: No se encontró mapeo para modifier_id {mod_id}. Se omitirá.")
        item_payload["modifiers_ids"] = new_mod_ids


        # --- Preparar Variantes ---
        item_payload["variants"] = []
        original_variants = item.get("variants", [])
        if not original_variants:
             print("  Advertencia: El item no tiene variantes definidas en el JSON original.")
             # Considera si necesitas crear una variante por defecto si la API lo requiere

        print(f"  Preparando {len(original_variants)} variantes...")
        for variant_index, variant in enumerate(original_variants):
            original_variant_id = variant.get("variant_id")
            if not original_variant_id:
                print(f"  Advertencia: Variante índice {variant_index} no tiene 'variant_id'. Saltando.")
                continue

            print(f"    - Preparando variante original {original_variant_id} (SKU: {variant.get('sku', 'N/A')})")
            variant_payload = copy.deepcopy(variant)

            # Eliminar campos no necesarios o generados por la API para el payload de variante DENTRO del item
            variant_keys_to_remove = [
                "variant_id",       # Se genera nuevo
                "item_id",          # Se asocia al crear el item
                "created_at",
                "updated_at",
                "deleted_at",
                "stores"            # Se reconstruirá para las tiendas de destino
            ]
            for key in variant_keys_to_remove:
                variant_payload.pop(key, None)

            # Establecer reference_variant_id (útil para referencia futura)
            variant_payload["reference_variant_id"] = original_variant_id

            # Añadir configuración de tiendas de DESTINO
            variant_payload["stores"] = []
            original_store_configs = variant.get("stores", [])
            base_store_config = {}

            # Intentar obtener una config base (precio, tipo) de la primera tienda original si existe
            if original_store_configs:
                 first_orig_store = original_store_configs[0]
                 base_store_config = {
                     "pricing_type": first_orig_store.get("pricing_type"), # Mantener null si no está
                     "price": first_orig_store.get("price"), # Mantener null si no está o es variable
                     "available_for_sale": first_orig_store.get("available_for_sale", True)
                     # optimal_stock y low_stock no suelen copiarse directamente
                 }
                 print(f"      Config base de tienda original: {base_store_config}")

            # Usar default_price/default_pricing_type como fallback si no hay info en stores originales
            if base_store_config.get("pricing_type") is None:
                base_store_config["pricing_type"] = variant.get("default_pricing_type", "FIXED")
                print(f"      Usando default_pricing_type: {base_store_config['pricing_type']}")
            if base_store_config.get("price") is None and base_store_config["pricing_type"] != "VARIABLE":
                 base_store_config["price"] = variant.get("default_price")
                 print(f"      Usando default_price: {base_store_config['price']}")

            # Aplicar config base a todas las tiendas de destino configuradas
            print(f"      Aplicando a tiendas destino: {DESTINATION_STORE_IDS}")
            for store_id in DESTINATION_STORE_IDS:
                # Validar que el ID de tienda destino no sea un placeholder
                if "tu_id_tienda_destino" in store_id:
                    print(f"      ERROR CRÍTICO: ID de tienda destino '{store_id}' no configurado. Abortando item.")
                    # Puedes decidir abortar todo el script o solo este item
                    # return # Descomentar para abortar todo si un ID de tienda es inválido
                    item_payload = None # Marcar para saltar el POST de este item
                    break # Salir del loop de tiendas destino

                store_config = copy.deepcopy(base_store_config)
                store_config["store_id"] = store_id
                # Asegurar que el precio sea null si el tipo es VARIABLE
                if store_config.get("pricing_type") == "VARIABLE":
                    store_config["price"] = None
                # Asegurar que available_for_sale sea booleano
                store_config["available_for_sale"] = bool(store_config.get("available_for_sale", True))

                variant_payload["stores"].append(store_config)

            if item_payload is None: # Si hubo error crítico de tienda, saltar al siguiente item
                 break

            item_payload["variants"].append(variant_payload)
            # Fin del loop de variantes

        if item_payload is None: # Si hubo error crítico de tienda, saltar al siguiente item
             print(f"  SALTANDO POST para item {original_item_id} debido a error de configuración de tienda.")
             continue

        # --- Enviar Solicitud POST para Crear Item y sus Variantes ---
        response_data = send_post_request("/items", item_payload, "items", original_item_id)

        # --- Mapear IDs de Variantes (si el POST del item fue exitoso y devolvió variantes) ---
        if response_data and isinstance(response_data, dict) and response_data.get("variants"):
            newly_created_variants = response_data.get("variants", [])
            print(f"  Procesando mapeo para {len(newly_created_variants)} variantes creadas...")
            # Es más fiable mapear por el reference_variant_id que por índice
            original_variants_map = {v.get("variant_id"): v for v in original_variants if v.get("variant_id")}

            for new_variant in newly_created_variants:
                new_variant_id = new_variant.get("variant_id")
                ref_variant_id = new_variant.get("reference_variant_id") # El ID original que pusimos

                if new_variant_id and ref_variant_id:
                     if ref_variant_id in original_variants_map:
                         id_mapping["variants"][ref_variant_id] = new_variant_id
                         print(f"    - Mapeado variant_id (vía ref): {ref_variant_id} -> {new_variant_id}")
                     else:
                         print(f"    - Advertencia: Se encontró reference_variant_id {ref_variant_id} en respuesta, pero no en variantes originales del item {original_item_id}.")
                elif new_variant_id:
                     # Intentar mapear por índice si falta reference_variant_id (menos fiable)
                     print(f"    - Advertencia: Variante creada {new_variant_id} no devolvió reference_variant_id. Mapeo podría ser incorrecto si el orden cambió.")
                     # Lógica de mapeo por índice (omitida por complejidad y menor fiabilidad)
                else:
                     print(f"    - Advertencia: Variante en respuesta no tiene nuevo ID. Respuesta parcial: {new_variant}")
        elif response_data:
            print(f"  Advertencia: Respuesta del POST para item {original_item_id} no contenía 'variants' o no era un diccionario. No se mapearon variantes.")
        else:
             print(f"  Fallo al crear item {original_item_id}. No se mapearon variantes.")


        # --- Mensaje sobre componentes (Informativo, ya no causa error) ---
        if item.get("is_composite") and item.get("components"):
             print(f"  INFO: Item {original_item_id} es compuesto. Componentes originales: {item.get('components')}. Estos NO fueron vinculados. Requiere actualización posterior.")

        time.sleep(1) # Pausa más larga después de crear un item con variantes

# --- Proceso Principal de Recreación ---
def main():
    print("--- Verificación Inicial ---")
    abort_script = False
    if not DESTINATION_API_TOKEN:
        print("ERROR CRÍTICO: La variable de entorno LOYVERSE_DESTINATION_API_TOKEN no está configurada.")
        abort_script = True
    if not DESTINATION_STORE_IDS or any("tu_id_tienda_destino" in s_id for s_id in DESTINATION_STORE_IDS):
         print(f"ERROR CRÍTICO: La lista DESTINATION_STORE_IDS ({DESTINATION_STORE_IDS}) contiene placeholders o está vacía. Debes configurarla con los IDs de tienda REALES de tu cuenta de DESTINO.")
         abort_script = True
    if not os.path.isdir(SNAPSHOT_DIR):
         print(f"ERROR CRÍTICO: El directorio de snapshots '{SNAPSHOT_DIR}' no existe o no es un directorio.")
         abort_script = True

    if abort_script:
        print("Abortando script debido a errores de configuración.")
        return

    print("Configuración verificada.")
    print("--- Iniciando Recreación de Cuenta Loyverse (Destino) ---")

    # Cargar datos desde los archivos JSON
    categories_data = load_json_file("categories.json")
    taxes_data = load_json_file("taxes.json")
    # modifiers_data = load_json_file("modifiers.json") # Descomentar si aplica
    # suppliers_data = load_json_file("suppliers.json") # Descomentar si aplica
    items_data = load_json_file("items.json")
    # stores_data = load_json_file("stores.json") # Cargar si se necesita mapeo complejo de tiendas

    # Procesar en orden de dependencia
    process_categories(categories_data)
    process_taxes(taxes_data)
    # process_modifiers(modifiers_data) # Descomentar si aplica
    # process_suppliers(suppliers_data) # Descomentar si aplica
    process_items(items_data) # Este es el más complejo

    print("\n--- Recreación de Cuenta Loyverse Completada ---")

    # Guardar el mapeo de IDs resultante para referencia futura o depuración
    map_filename = "id_mapping_prod_to_dest.json"
    try:
        os.makedirs(os.path.dirname(map_filename) or '.', exist_ok=True) # Asegura que el directorio existe
        with open(map_filename, 'w', encoding='utf-8') as f:
            json.dump(id_mapping, f, ensure_ascii=False, indent=4)
        print(f"\nMapeo de IDs guardado exitosamente en: {map_filename}")
    except Exception as e:
        print(f"\nError guardando el mapeo de IDs en {map_filename}: {e}")

if __name__ == "__main__":
    main()