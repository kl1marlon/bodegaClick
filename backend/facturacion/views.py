from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Producto, TasaCambio, Factura, Webhook
from .serializers import (
    ProductoSerializer,
    TasaCambioSerializer,
    FacturaSerializer,
    CrearFacturaSerializer,
    ActualizarPreciosSerializer,
    WebhookSerializer,
    CreateWebhookSerializer
)
from .services import LoyverseService
import json
import hmac
import hashlib
import base64
import uuid
from django.conf import settings
import datetime
from asgiref.sync import async_to_sync
# Importar la función sync_products
import sys
import os
sys.path.append(os.path.join(settings.BASE_DIR))
from sync_products import sync_products
import logging
from loyverse_sync.sync import sincronizar_desde_loyverse

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    
    @action(detail=False, methods=['post'])
    def sync_from_loyverse(self, request):
        """
        Endpoint para sincronizar productos desde Loyverse.
        
        Permite sincronización selectiva por categoría, tipo de tasa, y productos específicos,
        preservando los precios base en USD.
        
        Args:
            request.data (dict):
                - actualizar_precios (bool): Si es True, exporta precios a Loyverse
                - categorias (list): Lista de categorías a sincronizar
                - tipo_tasa (str): Filtrar por tipo de tasa (BCV o PARALELO)
                - productos_ids (list): IDs específicos de productos a exportar
                - tamaño_lote (int): Número de productos por lote para exportación
        """
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 Iniciando sync_from_loyverse desde API con datos: {request.data}")
        
        # Procesar parámetros de la petición
        opciones = {
            'solo_importar': not request.data.get('actualizar_precios', True),
            'categorias': request.data.get('categorias'),
            'tipo_tasa': request.data.get('tipo_tasa'),
            'productos_ids': request.data.get('productos_ids')
        }
        
        # Procesar tamaño del lote si se proporciona
        if 'tamaño_lote' in request.data:
            try:
                tamaño_lote = int(request.data.get('tamaño_lote'))
                if 5 <= tamaño_lote <= 100:  # Validar rango
                    opciones['tamaño_lote'] = tamaño_lote
                    logger.info(f"📊 Tamaño de lote personalizado: {tamaño_lote}")
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Valor de tamaño_lote inválido: {request.data.get('tamaño_lote')}")
        
        try:
            # Ejecutar sincronización con las opciones especificadas
            result = sincronizar_desde_loyverse(opciones)
            
            # Construir mensaje informativo para el usuario
            if 'error' in result:
                return Response({
                    'error': f"Error en sincronización: {result['error']}",
                    'detalles': result
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Preparar mensaje de éxito
            mensaje = "Sincronización completada exitosamente. "
            
            # Detalles de productos específicos si es modo prueba
            if opciones.get('productos_ids'):
                mensaje = "PRUEBA DE SINCRONIZACIÓN: " + mensaje
                mensaje += f"Se procesaron los productos específicos seleccionados. "
            
            mensaje += f"Creados: {result['importacion'].get('creados', 0)}, "
            mensaje += f"Actualizados: {result['importacion'].get('actualizados', 0)}"
            
            if result.get('exportacion_realizada'):
                mensaje += f", Precios actualizados: {result['exportacion'].get('actualizados', 0)}"
            
            # Todos los productos tienen aplicar_iva=false por defecto
            mensaje += " Todos los productos tienen aplicar_iva=false por defecto."
            
            # Incluir filtros aplicados en la respuesta
            filtros_aplicados = []
            if opciones.get('categorias'):
                filtros_aplicados.append(f"categorías: {opciones['categorias']}")
            if opciones.get('tipo_tasa'):
                filtros_aplicados.append(f"tipo de tasa: {opciones['tipo_tasa']}")
            if opciones.get('productos_ids'):
                filtros_aplicados.append(f"productos específicos: {len(opciones['productos_ids'])}")
            
            if filtros_aplicados:
                mensaje += f" Filtros aplicados: {', '.join(filtros_aplicados)}."
            
            # Construir respuesta de éxito con estadísticas
            response_data = {
                'message': mensaje,
                'tiempo_total': result['tiempo_total'],
                'created': result['importacion'].get('creados', 0),
                'updated': result['importacion'].get('actualizados', 0),
                'exportacion_realizada': result.get('exportacion_realizada', False),
                'total_processed': result['importacion'].get('total_procesados', 0),
                'modo_prueba': bool(opciones.get('productos_ids'))
            }
            
            # Incluir estadísticas de exportación si se realizó
            if result.get('exportacion_realizada'):
                response_data.update({
                    'precios_actualizados': result['exportacion'].get('actualizados', 0),
                    'precios_fallidos': result['exportacion'].get('fallidos', 0),
                    'sin_precio_base': result['exportacion'].get('sin_precio', 0)
                })
            
            return Response(response_data)
            
        except Exception as e:
            logger.exception(f"❌ Error en sincronización: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def sync_to_loyverse(self, request):
        service = LoyverseService()
        products = Producto.objects.all()
        result = service.sync_prices(products)
        
        if result['success']:
            return Response({
                'message': f"Precios sincronizados correctamente. Actualizados: {result['updated']}"
            })
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def calcular_precios(self, request):
        serializer = ActualizarPreciosSerializer(data=request.data)
        if serializer.is_valid():
            service = LoyverseService()
            
            # Si se proporciona ID de factura, procesar desde factura
            if 'factura_id' in serializer.validated_data:
                result = service.actualizar_precios_desde_factura(
                    serializer.validated_data['factura_id']
                )
            else:
                # Procesar un producto específico o todos si no se especifica
                producto_id = serializer.validated_data.get('producto_id')
                porcentaje = serializer.validated_data.get('porcentaje_ganancia')
                
                result = service.calcular_precios_venta(producto_id, porcentaje)
                
                # Si el cálculo fue exitoso, sincronizar con Loyverse
                if result['success'] and producto_id:
                    producto = Producto.objects.get(id=producto_id)
                    service.sync_prices([producto])
            
            if result['success']:
                return Response(result)
            
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TasaCambioViewSet(viewsets.ModelViewSet):
    queryset = TasaCambio.objects.all().order_by('-fecha')
    serializer_class = TasaCambioSerializer
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        tipo = request.query_params.get('tipo', 'BCV')
        try:
            tasa = TasaCambio.objects.filter(tipo=tipo).latest('fecha')
            serializer = self.get_serializer(tasa)
            return Response(serializer.data)
        except TasaCambio.DoesNotExist:
            return Response({
                'error': f'No hay tasa de cambio {tipo} registrada'
            }, status=status.HTTP_404_NOT_FOUND)

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all().order_by('-fecha')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrearFacturaSerializer
        return FacturaSerializer
    
    def create(self, request, *args, **kwargs):
        print("Datos recibidos:", request.data)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Errores de validación:", serializer.errors)
            
            # Mejora en el manejo de errores para campos decimales
            errores_formateados = {}
            
            for campo, errores in serializer.errors.items():
                # Manejar errores específicos para detalles
                if campo == 'detalles' and isinstance(errores, list):
                    errores_detalles = []
                    for idx, error_detalle in enumerate(errores):
                        if isinstance(error_detalle, dict):
                            detalle_formateado = {}
                            for subcampo, suberrores in error_detalle.items():
                                # Formatear mensajes específicos para campos con restricciones decimales
                                if 'decimal' in str(suberrores).lower() or 'válido' in str(suberrores).lower():
                                    if subcampo == 'unidades_paquete':
                                        detalle_formateado[subcampo] = [
                                            "Este campo debe ser un número decimal con máximo 2 decimales. Ejemplo: 5.54"
                                        ]
                                    elif subcampo in ['precio_compra_usd', 'precio_unitario', 'precio_base_usd']:
                                        detalle_formateado[subcampo] = [
                                            "Este campo debe ser un número decimal con máximo 2 decimales. Ejemplo: 10.50"
                                        ]
                                    else:
                                        detalle_formateado[subcampo] = suberrores
                                else:
                                    detalle_formateado[subcampo] = suberrores
                            errores_detalles.append(detalle_formateado)
                        else:
                            errores_detalles.append(error_detalle)
                    errores_formateados[campo] = errores_detalles
                else:
                    errores_formateados[campo] = errores
            
            # Agregamos un mensaje general para facilitar la comprensión
            mensaje_error = "No se pudo crear la factura debido a errores en los datos. "
            if 'detalles' in serializer.errors:
                mensaje_error += "Verifique que los campos numéricos no exceden el máximo de 2 decimales permitidos."
            
            return Response({
                "error": mensaje_error,
                "detalles_error": errores_formateados
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = serializer.save()
            return Response(FacturaSerializer(instance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Error al crear factura:", str(e))
            return Response({
                "error": "Error al crear la factura",
                "detalle": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def procesar_factura(self, request, pk=None):
        """
        Procesa una factura existente para actualizar precios e inventario en Loyverse
        
        NOTA: Esta implementación combina la actualización de precios existente con
        la nueva funcionalidad de actualización de inventario.
        """
        import sys
        print(f"\n🔄 INICIANDO procesar_factura para ID: {pk}")
        sys.stdout.flush()
        service = LoyverseService()
        
        # Actualizar precios (funcionalidad existente)
        print(f"💲 Llamando a actualizar_precios_desde_factura")
        sys.stdout.flush()
        result_precios = service.actualizar_precios_desde_factura(pk)
        print(f"💲 Resultado de actualizar_precios_desde_factura: {result_precios['success']}")
        sys.stdout.flush()
        
        # Actualizar inventario (nueva funcionalidad)
        print(f"📦 Llamando a actualizar_inventario_desde_factura")
        sys.stdout.flush()
        result_inventario = service.actualizar_inventario_desde_factura(pk)
        print(f"📦 Resultado de actualizar_inventario_desde_factura: {result_inventario['success']}")
        sys.stdout.flush()
        
        if result_precios['success'] and result_inventario['success']:
            print(f"✅ Ambos procesos ejecutados con éxito")
            sys.stdout.flush()
            return Response({
                'message': f"Factura procesada correctamente. Productos con precios actualizados: {result_precios['productos_actualizados']}, Productos con inventario actualizado: {result_inventario['productos_actualizados']}",
                'detalle_precios': result_precios,
                'detalle_inventario': result_inventario
            })
        
        errores = []
        if not result_precios['success']:
            errores.append(result_precios['error'])
        if not result_inventario['success']:
            errores.append(result_inventario['error'])
        
        print(f"❌ Errores en el proceso: {errores}")
        sys.stdout.flush()
        return Response({
            'error': "Error al procesar la factura: " + ", ".join(errores)
        }, status=status.HTTP_400_BAD_REQUEST)

class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateWebhookSerializer
        return WebhookSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Generar UUID si no se proporciona
            if not serializer.validated_data.get('id'):
                serializer.validated_data['id'] = str(uuid.uuid4())
            
            # Agregar el merchant_id (asumiendo que está en configuración o se obtiene de alguna manera)
            webhook = serializer.save(merchant_id=settings.LOYVERSE_MERCHANT_ID)
            
            return Response(
                WebhookSerializer(webhook).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Envía una solicitud de prueba al webhook
        """
        webhook = self.get_object()
        service = LoyverseService()
        result = service.test_webhook(webhook)
        
        if result['success']:
            return Response({
                'message': 'Webhook probado correctamente',
                'details': result
            })
        
        return Response({
            'error': result['error']
        }, status=status.HTTP_400_BAD_REQUEST)

class WebhookReceiveView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self, request):
        """
        Endpoint para recibir notificaciones de webhook desde Loyverse
        """
        print("🔔 Webhook recibido!")
        print(f"Headers: {dict(request.headers)}")
        
        try:
            data = json.loads(request.body)
            print(f"Datos recibidos: {data}")
            
            event_type = data.get('type')
            print(f"Tipo de evento: {event_type}")
            
            # Manejar el evento según su tipo
            if event_type == 'inventory_levels.update':
                self._handle_inventory_update(data)
            elif event_type == 'items.update':
                self._handle_items_update(data)
            # Otros tipos se pueden manejar aquí
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Loguear error pero devolver 200 para evitar reintentos
            print(f"Error procesando webhook: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Siempre responder con éxito para evitar reintentos
            return Response({'status': 'processed', 'warning': str(e)}, status=status.HTTP_200_OK)
    
    def _verify_signature(self, payload, signature):
        """
        Verifica la firma del webhook usando HMAC con SHA-1 (según documentación de Loyverse)
        """
        # Calcular firma esperada
        expected = base64.b64encode(
            hmac.new(
                settings.LOYVERSE_WEBHOOK_SECRET.encode('utf-8'),
                payload,
                hashlib.sha1  # Loyverse usa SHA-1, no SHA-256
            ).digest()
        ).decode('utf-8')
        
        # Comparar con la firma recibida
        return hmac.compare_digest(expected, signature)
    
    def _handle_inventory_update(self, data):
        """
        Maneja la actualización de inventario
        """
        inventory_levels = data.get('inventory_levels', [])
        service = LoyverseService()
        
        for level in inventory_levels:
            variant_id = level.get('variant_id')
            store_id = level.get('store_id')
            in_stock = level.get('in_stock')
            
            # Buscar el producto correspondiente
            try:
                producto = Producto.objects.get(loyverse_id=variant_id)
                
                # Guardar el stock anterior para comparar
                stock_anterior = producto.stock_actual
                
                # Actualizar el stock del producto
                producto.stock_actual = in_stock
                producto.ultima_actualizacion_stock = datetime.datetime.now()
                producto.save()
                
                print(f"Inventario actualizado para {producto.nombre}: {in_stock} unidades")
                
            except Producto.DoesNotExist:
                # Si el producto no existe, sincronizar desde Loyverse
                print(f"Producto con ID {variant_id} no encontrado. Sincronizando productos...")
                service.fetch_products()
                
    def _handle_items_update(self, data):
        """
        Maneja la actualización de productos
        """
        items = data.get('items', [])
        service = LoyverseService()
        
        if items:
            # Sincronizar productos desde Loyverse
            print(f"Recibida actualización de {len(items)} productos. Sincronizando...")
            service.fetch_products()

    # También aceptamos solicitudes GET para pruebas
    def get(self, request):
        """Endpoint para probar si el webhook está accesible"""
        return Response({'status': 'Webhook endpoint activo'}, status=status.HTTP_200_OK) 