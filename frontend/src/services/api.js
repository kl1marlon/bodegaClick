import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

export const fetchProductosAPI = () => api.get('/api/productos/');
export const fetchTasaCambioAPI = (tipo) => api.get(`/api/tasas-cambio/?tipo=${tipo}`);
export const createFacturaAPI = (data) => api.post('/api/facturas/', data);

// Cliente WebSocket para notificaciones
export const conectarWebSocketNotificaciones = (onMensaje, onError) => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const wsUrl = `${wsProtocol}//${baseUrl.replace(/^https?:\/\//, '')}/ws/notificaciones/`;
  
  const socket = new WebSocket(wsUrl);
  
  socket.onopen = () => {
    console.log('Conexión WebSocket establecida');
  };
  
  socket.onmessage = (event) => {
    const datos = JSON.parse(event.data);
    if (onMensaje) onMensaje(datos);
  };
  
  socket.onerror = (error) => {
    console.error('Error en WebSocket:', error);
    if (onError) onError(error);
  };
  
  socket.onclose = () => {
    console.log('Conexión WebSocket cerrada');
    // Reconectar automáticamente después de 5 segundos
    setTimeout(() => conectarWebSocketNotificaciones(onMensaje, onError), 5000);
  };
  
  // Retornar el socket para permitir cerrar la conexión manualmente
  return socket;
};

export default api; 