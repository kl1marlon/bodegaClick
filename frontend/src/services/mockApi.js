import axios from 'axios';
import moment from 'moment';

// Función para interceptar las llamadas a la API de búsqueda de productos en facturas
// Esta función ya no emula la respuesta, ahora permite que pase al backend real
export const setupProductoFacturasInterceptor = () => {
  // Agregar un interceptor de respuesta para registrar respuestas (solo para depuración)
  axios.interceptors.response.use((response) => {
    if (response.config.url && response.config.url.includes('/facturas/buscar-por-producto/')) {
      console.log('Respuesta de búsqueda de productos en facturas:', response.data);
    }
    return response;
  }, (error) => {
    return Promise.reject(error);
  });
  
  console.log('Interceptor configurado: Las solicitudes de búsqueda de productos ahora se envían al backend real');
};

// Las siguientes funciones se mantienen como referencia, pero ya no se utilizan
// ===============================================================================

// Función para simular la búsqueda de un producto en las facturas
const mockBuscarProductoEnFacturas = async (productoId) => {
  console.log(`Simulando búsqueda para el producto ID: ${productoId}`);
  
  // Obtener facturas existentes (podríamos usar el store de Redux en una implementación real)
  try {
    // Intentar obtener facturas reales si están disponibles
    const facturas = await getFacturasFromStore();
    return procesarFacturasParaProducto(facturas, productoId);
  } catch (error) {
    console.log('No se pudieron obtener facturas reales, usando datos simulados');
    // Si no podemos obtener facturas reales, devolver datos simulados
    return getFacturasSimuladas(productoId);
  }
};

// Función para obtener las facturas desde el store o API si están disponibles
const getFacturasFromStore = async () => {
  // Aquí intentaríamos obtener las facturas del store de Redux
  // Como solución temporal, intentaremos obtenerlas de la API
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  try {
    const response = await axios.get(`${API_URL}/facturas/listado_simple/`, {
      params: {
        page_size: 100 // Solicitar un número grande para tener más datos
      }
    });
    
    if (response.data && response.data.results) {
      return response.data.results;
    }
    throw new Error('No se pudieron obtener facturas reales');
  } catch (error) {
    throw error;
  }
};

// Función para procesar facturas existentes y buscar un producto específico
const procesarFacturasParaProducto = (facturas, productoId) => {
  // Lista para almacenar las apariciones del producto en facturas
  const apariciones = [];
  
  // Iterar sobre cada factura
  facturas.forEach(factura => {
    // Si la factura tiene detalles, buscar el producto
    if (factura.detalles && Array.isArray(factura.detalles)) {
      factura.detalles.forEach(detalle => {
        if (detalle.producto_id === parseInt(productoId) || detalle.producto_id === productoId) {
          apariciones.push({
            id: detalle.id,
            factura_id: factura.id,
            fecha: factura.fecha,
            numero: factura.numero,
            cantidad: detalle.cantidad,
            precio_unitario: detalle.precio_unitario,
            total: detalle.total
          });
        }
      });
    }
  });
  
  // Si no encontramos apariciones con el método anterior, verificar si es porque no pudimos acceder a los detalles
  if (apariciones.length === 0) {
    console.log('No se encontraron apariciones en los detalles, regresando datos simulados');
    return getFacturasSimuladas(productoId);
  }
  
  return apariciones;
};

// Función para generar datos simulados de compras
const getFacturasSimuladas = (productoId) => {
  // Generar entre 0 y 5 registros de compras simuladas para este producto
  const numRegistros = Math.floor(Math.random() * 6);
  const registros = [];
  
  for (let i = 0; i < numRegistros; i++) {
    // Fecha aleatoria en los últimos 6 meses
    const fechaRandom = moment()
      .subtract(Math.floor(Math.random() * 180), 'days')
      .format('YYYY-MM-DD');
    
    // Precio unitario aleatorio entre 2 y 50
    const precioUnitario = Math.random() * 48 + 2;
    
    // Cantidad aleatoria entre 1 y 10
    const cantidad = Math.floor(Math.random() * 10) + 1;
    
    registros.push({
      id: `sim-${productoId}-${i}`,
      factura_id: `sim-f-${Math.floor(Math.random() * 1000)}`,
      fecha: fechaRandom,
      numero: `F-${Math.floor(Math.random() * 10000)}`,
      cantidad: cantidad,
      precio_unitario: precioUnitario.toFixed(2),
      total: (precioUnitario * cantidad).toFixed(2)
    });
  }
  
  // Ordenar por fecha (más reciente primero)
  registros.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
  
  return registros;
}; 