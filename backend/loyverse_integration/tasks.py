from celery import shared_task
from django.utils import timezone
import time
import requests
import os
import logging

from .models import LoyverseUserConnection

# It's better to have LOYVERSE_API_BASE_URL in settings or a constants file.
LOYVERSE_API_BASE_URL = os.environ.get('LOYVERSE_API_BASE_URL', 'https://api.loyverse.com/v1.0')

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5*60) # 5 minutes delay between retries
def sync_loyverse_prices_for_user(self, loyverse_connection_id):
    """
    Celery task to synchronize product prices for a user 
    from BodegaClick to their Loyverse account.
    """
    try:
        connection = LoyverseUserConnection.objects.get(id=loyverse_connection_id)
    except LoyverseUserConnection.DoesNotExist:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] LoyverseUserConnection with ID {loyverse_connection_id} not found.")
        return f"Error: Loyverse Connection ID {loyverse_connection_id} not found."

    logger.info(f"[Celery Task sync_loyverse_prices_for_user] Starting sync for connection ID {connection.id}, User: {connection.user.username}")
    
    connection.price_sync_status = LoyverseUserConnection.SyncStatus.SYNCING
    connection.last_price_sync_start_time = timezone.now()
    connection.last_price_sync_details = {'status': 'Initializing sync...', 'processed_items': 0, 'updated_items': 0, 'skipped_items': 0, 'errors': []}
    connection.save(update_fields=['price_sync_status', 'last_price_sync_start_time', 'last_price_sync_details'])

    access_token = connection.get_valid_access_token()

    if not access_token:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] Could not get a valid access token for connection ID {connection.id}. Marking as TOKEN_INVALID.")
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.TOKEN_INVALID
        connection.last_price_sync_end_time = timezone.now()
        connection.last_error_message = "Could not obtain or refresh Loyverse access token."
        # Mark connection as inactive if token fails persistently
        connection.is_active = False 
        connection.last_price_sync_details['status'] = 'Failed: Invalid token.'
        connection.last_price_sync_details['errors'].append({'item_sku': 'N/A', 'error': 'Invalid access token'})
        connection.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_error_message', 'is_active', 'last_price_sync_details'])
        return f"Sync failed: Invalid token for connection ID {connection.id}"

    sync_report = {
        'total_local_products': 0,
        'total_loyverse_items_fetched': 0, # If fetching Loyverse items is implemented
        'items_processed': 0,
        'items_updated_in_loyverse': 0,
        'items_skipped': 0,
        'errors': [],
        'status_message': 'Processing...' 
    }

    try:
        # --- 1. Get local products (Placeholder) ---
        # This logic will depend on how your local product models are structured
        # and how they relate to `connection.user`.
        # Example: local_products = Producto.objects.filter(usuario=connection.user, necesita_sinc_loyverse=True)
        logger.info(f"[Celery Task sync_loyverse_prices_for_user] Placeholder: Fetching local products for {connection.user.username}...")
        # For now, simulate an empty list to avoid entering the actual update loop without full logic.
        local_products = [] 
        sync_report['total_local_products'] = len(local_products)

        if not local_products:
            logger.info(f"[Celery Task sync_loyverse_prices_for_user] No local products found to sync for {connection.user.username}.")
            sync_report['status_message'] = "No local products marked for synchronization."
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED
            connection.last_price_sync_details.update(sync_report)
            connection.save(update_fields=['price_sync_status', 'last_price_sync_details'])
            # Fall through to finally block to set end_time

        # --- 2. (Optional) Fetch all items from Loyverse (Placeholder) ---
        # This could be useful for mapping SKUs or IDs before updating.
        # headers_get = {'Authorization': f'Bearer {access_token}'}
        # all_loyverse_items_url = f"{LOYVERSE_API_BASE_URL}/items"
        # try:
        #     loyverse_items_response = requests.get(all_loyverse_items_url, headers=headers_get)
        #     loyverse_items_response.raise_for_status()
        #     loyverse_items_data = loyverse_items_response.json().get('items', [])
        #     sync_report['total_loyverse_items_fetched'] = len(loyverse_items_data)
        #     # Process and map loyverse_items_data if necessary
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error fetching items from Loyverse: {e}")
        #     sync_report['errors'].append({'item_sku': 'N/A', 'error': f'Error fetching Loyverse item list: {str(e)}'})

        # --- 3. Loop through local products and update Loyverse (Placeholder) ---
        # This is where the core synchronization logic will go.
        # For each local_product:
        #   - Find corresponding Loyverse item_id (e.g., using SKU or a stored mapping).
        #   - Prepare payload for Loyverse API (e.g., new price).
        #   - Make a POST/PUT request to update the item in Loyverse.
        #   - Handle API rate limits (HTTP 429) with retries and backoff.
        #   - Update sync_report (processed, updated, skipped, errors).
        #   - time.sleep(1.05) # Respect rate limit between POST requests

        # Example of what the loop *might* look like (highly simplified):
        # for product in local_products:
        #     sync_report['items_processed'] += 1
        #     loyverse_item_id = get_loyverse_item_id_for_product(product) # Placeholder function
        #     if not loyverse_item_id:
        #         sync_report['items_skipped'] += 1
        #         sync_report['errors'].append({'product_sku': product.sku, 'error': 'Loyverse item ID not found'})
        #         continue
        #     
        #     update_url = f"{LOYVERSE_API_BASE_URL}/items/{loyverse_item_id}"
        #     payload = {'price': str(product.price_to_sync)} # Ensure price is a string if API expects
        #     headers_post = {
        #         'Authorization': f'Bearer {access_token}',
        #         'Content-Type': 'application/json' # Or 'application/x-www-form-urlencoded' depending on API
        #     }
        #     
        #     time.sleep(1.05) # Rate limit
        #     try:
        #         response = requests.post(update_url, json=payload, headers=headers_post) # or data=payload for form-urlencoded
        #         if response.status_code == 429: # Too Many Requests
        #             retry_after = int(response.headers.get("Retry-After", 60)) # seconds
        #             logger.warning(f"Rate limit hit. Retrying task for {loyverse_connection_id} after {retry_after}s")
        #             # Celery's self.retry will re-queue the task.
        #             # The 'exc' parameter takes an exception instance.
        #             raise self.retry(countdown=retry_after, exc=requests.exceptions.HTTPError("Rate limit hit", response=response))
        #         response.raise_for_status() # Raise HTTPError for other bad responses (4xx or 5xx)
        #         sync_report['items_updated_in_loyverse'] += 1
        #     except requests.exceptions.HTTPError as e:
        #         error_detail = str(e)
        #         if e.response is not None:
        #             error_detail = f"{e.response.status_code} - {e.response.text}"
        #         logger.error(f"HTTP error updating product {product.sku} in Loyverse: {error_detail}")
        #         sync_report['errors'].append({'product_sku': product.sku, 'error': f'Loyverse API error: {error_detail}'})
        #     except requests.exceptions.RequestException as e:
        #         logger.error(f"Request error updating product {product.sku} in Loyverse: {e}")
        #         sync_report['errors'].append({'product_sku': product.sku, 'error': f'Network/Request error: {str(e)}'})
        #     except Exception as e:
        #         logger.error(f"Unexpected error updating product {product.sku} in Loyverse: {e}", exc_info=True)
        #         sync_report['errors'].append({'product_sku': product.sku, 'error': f'Unexpected error: {str(e)}'})

        if not sync_report['errors'] and local_products: # Only if there were products and no errors during processing them
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED
            sync_report['status_message'] = 'Synchronization completed successfully.'
        elif sync_report['errors'] and local_products:
            connection.price_sync_status = LoyverseUserConnection.SyncStatus.COMPLETED_WITH_ERRORS
            sync_report['status_message'] = 'Synchronization completed with some errors.'
        # If no local_products, status already set to COMPLETED

    except requests.exceptions.HTTPError as e:
        # This handles HTTP errors not caught by the inner loop's 429 specific handling (e.g. during initial item fetch)
        # Or if self.retry within the loop raises an exception that isn't caught by Celery's retry mechanism (unlikely for HTTPError)
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] HTTP Error during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"HTTP Error during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'General HTTP Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to HTTP error.'
        # If a retry is raised from here, Celery handles it.
        # If max_retries is exceeded, Celery won't call the task again.
        # We might want to re-raise to let Celery know it was an exception if not using self.retry directly.
        # For now, we catch and log, then proceed to finally block.

    except requests.exceptions.RequestException as e:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] Request Exception during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"Network/Request Exception during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'General Request/Network Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to network/request error.'
        # Consider re-raising if Celery should retry based on this exception type.
        # raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"[Celery Task sync_loyverse_prices_for_user] Unexpected error during sync for connection {connection.id}: {e}", exc_info=True)
        connection.price_sync_status = LoyverseUserConnection.SyncStatus.FAILED
        connection.last_error_message = f"Unexpected error during sync: {str(e)}"
        sync_report['errors'].append({'item_sku': 'N/A', 'error': f'Unexpected Error: {str(e)}'})
        sync_report['status_message'] = 'Synchronization failed due to an unexpected error.'
        # No re-raise here, as it's an unexpected error. Let Celery handle based on task settings.

    finally:
        connection.last_price_sync_end_time = timezone.now()
        connection.last_price_sync_details.update(sync_report)
        connection.save(update_fields=['price_sync_status', 'last_price_sync_end_time', 'last_error_message', 'last_price_sync_details'])
        logger.info(f"[Celery Task sync_loyverse_prices_for_user] Sync finished for connection ID {connection.id}. Status: {connection.price_sync_status}")
        return f"Sync completed for {connection.id}. Status: {connection.price_sync_status}. Details: {connection.last_price_sync_details}"

# Example of how you might trigger this task (e.g., from a view or admin action):
# from .tasks import sync_loyverse_prices_for_user
# sync_loyverse_prices_for_user.delay(loyverse_connection_id=some_id)
