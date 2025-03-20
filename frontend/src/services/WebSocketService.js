/**
 * Servicio para gestionar las conexiones de WebSockets
 */
class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = {};
  }

  // Conectar al WebSocket
  connect() {
    if (this.socket) {
      this.disconnect();
    }

    // URL del WebSocket (usando la misma base que la API pero con ws:// o wss://)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_API_URL 
      ? new URL(process.env.REACT_APP_API_URL).host 
      : window.location.host;
    
    this.socket = new WebSocket(`${protocol}//${host}/ws/notificaciones/`);

    this.socket.onopen = () => {
      console.log('Conexión WebSocket establecida');
      this.notifyListeners('connected', { message: 'Conexión establecida' });
    };

    this.socket.onclose = (event) => {
      console.log('Conexión WebSocket cerrada');
      this.notifyListeners('disconnected', { code: event.code, reason: event.reason });
      
      // Reintentar conexión después de 5 segundos
      setTimeout(() => {
        this.connect();
      }, 5000);
    };

    this.socket.onerror = (error) => {
      console.error('Error en WebSocket:', error);
      this.notifyListeners('error', { error });
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Mensaje recibido:', data);
        this.notifyListeners(data.type, data);
      } catch (error) {
        console.error('Error al procesar mensaje:', error);
      }
    };
  }

  // Desconectar el WebSocket
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  // Añadir un listener para eventos
  addListener(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = [];
    }
    this.listeners[eventType].push(callback);

    // Devolver una función para eliminar el listener
    return () => {
      this.removeListener(eventType, callback);
    };
  }

  // Eliminar un listener
  removeListener(eventType, callback) {
    if (this.listeners[eventType]) {
      this.listeners[eventType] = this.listeners[eventType].filter(
        (cb) => cb !== callback
      );
    }
  }

  // Notificar a todos los listeners de un evento
  notifyListeners(eventType, data) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].forEach((callback) => {
        callback(data);
      });
    }
  }
}

// Exportar una instancia única
export default new WebSocketService(); 