import axios from 'axios';

// Usar la configuración dinámica si está disponible, o fallback a variables de entorno o localhost
const getApiBaseUrl = () => {
  // Primero intentar usar la configuración dinámica
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  // Si no está disponible, usar variable de entorno o localhost
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

// NOTA: La baseURL ya incluye el prefijo /api/ en la configuración del backend
// por lo que no debemos incluirlo nuevamente en las rutas de este archivo.

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  }
});

// Para depuración
console.log('API baseURL:', api.defaults.baseURL);

// Los endpoints ya tienen el prefijo /api/ en el backend
export const fetchProductosAPI = () => api.get('/productos/');
export const fetchTasaCambioAPI = (tipo) => api.get(`/tasas-cambio/?tipo=${tipo}`);
export const createFacturaAPI = (data) => api.post('/facturas/', data);

// Función para formatear fechas para la API
const formatFechaParaAPI = (fecha) => {
  if (!fecha) return null;
  // Si es un objeto Date, formatearlo a YYYY-MM-DD
  if (fecha instanceof Date) {
    const year = fecha.getFullYear();
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const day = String(fecha.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
  return fecha; // Si ya es string, devolverlo tal cual
};

/**
 * Obtiene facturas con filtros opcionales de fecha
 * @param {Object} filtros - Filtros para las facturas
 * @param {Date|string|null} filtros.fechaDesde - Fecha desde (opcional)
 * @param {Date|string|null} filtros.fechaHasta - Fecha hasta (opcional)
 * @returns {Promise} - Promesa con los datos de las facturas
 */
export const fetchFacturasAPI = (filtros = {}) => {
  const { fechaDesde, fechaHasta } = filtros;
  
  // Construir los parámetros de consulta
  const params = new URLSearchParams();
  
  if (fechaDesde) {
    params.append('fecha_desde', formatFechaParaAPI(fechaDesde));
  }
  
  if (fechaHasta) {
    params.append('fecha_hasta', formatFechaParaAPI(fechaHasta));
  }
  
  // Construir la URL con los parámetros
  const queryString = params.toString();
  const url = queryString ? `/facturas/?${queryString}` : '/facturas/';
  
  return api.get(url);
};

export default api; 