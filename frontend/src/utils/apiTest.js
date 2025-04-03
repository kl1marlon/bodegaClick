import axios from 'axios';

// Función para detectar la URL base correcta
const detectApiUrl = async () => {
  // URLs a probar en orden de prioridad - usando rutas relativas cuando sea posible
  const urlsToTry = [
    window.ENV?.API_URL, 
    window.ENV?.WORKER_URL,  // Añadir la URL del worker para probar
    '/api',  // Ruta relativa para proxy local
    '/worker-api',  // Ruta relativa para proxy local del worker
    process.env.REACT_APP_API_URL,
    'https://bodegaclick-production.up.railway.app/api',
    'https://backend-production-a8d3.up.railway.app/api',
    'http://localhost:8000/api'
  ];
  
  // Filtrar URLs nulas o indefinidas
  const validUrls = urlsToTry.filter(url => url);
  
  console.log('🔍 URLs a probar:', validUrls);
  
  // Probar cada URL y devolver la primera que funcione
  for (const url of validUrls) {
    try {
      console.log(`⏳ Probando conexión a: ${url}`);
      // Añadir un parámetro de timestamp para evitar caché
      const response = await axios.get(`${url}/tasas-cambio/latest/?_=${Date.now()}`, {
        timeout: 5000 // Timeout de 5 segundos
      });
      
      console.log(`✅ Conexión exitosa a ${url}`, response.data);
      return { url, success: true, data: response.data };
    } catch (error) {
      console.error(`❌ Error al conectar con ${url}:`, error.message);
      // Registrar detalles adicionales del error
      if (error.response) {
        console.error('Detalles de respuesta:', {
          data: error.response.data,
          status: error.response.status,
          headers: error.response.headers
        });
      } else if (error.request) {
        console.error('No se recibió respuesta del servidor');
      }
    }
  }
  
  return { success: false, message: 'No se pudo conectar a ninguna API' };
};

export { detectApiUrl }; 