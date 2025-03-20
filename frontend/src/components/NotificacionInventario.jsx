import React, { useEffect, useState } from 'react';
import WebSocketService from '../services/WebSocketService';

const NotificacionInventario = () => {
  const [notificaciones, setNotificaciones] = useState([]);
  const [conectado, setConectado] = useState(false);

  useEffect(() => {
    // Iniciar conexión al WebSocket
    WebSocketService.connect();

    // Escuchar eventos de conexión
    const connectedListener = WebSocketService.addListener('connected', () => {
      setConectado(true);
    });

    const disconnectedListener = WebSocketService.addListener('disconnected', () => {
      setConectado(false);
    });

    // Escuchar eventos de actualización de inventario
    const inventoryListener = WebSocketService.addListener('inventory_update', (data) => {
      // Agregar nueva notificación
      const nuevaNotificacion = {
        id: Date.now(), // ID único basado en timestamp
        producto: data.producto.nombre,
        mensaje: data.message,
        fecha: new Date().toLocaleTimeString(),
        leida: false
      };

      setNotificaciones((prev) => [nuevaNotificacion, ...prev].slice(0, 10)); // Mantener solo las 10 últimas
      
      // Mostrar notificación nativa si está disponible
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Actualización de Inventario', {
          body: data.message,
          icon: '/logo.png'
        });
      }
    });

    // Solicitar permiso para notificaciones
    if ('Notification' in window && Notification.permission !== 'denied') {
      Notification.requestPermission();
    }

    // Limpiar listeners al desmontar
    return () => {
      connectedListener();
      disconnectedListener();
      inventoryListener();
      WebSocketService.disconnect();
    };
  }, []);

  // Marcar notificación como leída
  const marcarLeida = (id) => {
    setNotificaciones(notificaciones.map(n => 
      n.id === id ? { ...n, leida: true } : n
    ));
  };

  // Eliminar notificación
  const eliminarNotificacion = (id) => {
    setNotificaciones(notificaciones.filter(n => n.id !== id));
  };

  // Si no hay notificaciones, no renderizar nada
  if (notificaciones.length === 0) {
    return null;
  }

  return (
    <div className="notificaciones-container">
      <div className="notificaciones-header">
        <h3>Notificaciones de Inventario {conectado ? 
          <span className="estado-conectado">●</span> : 
          <span className="estado-desconectado">●</span>}
        </h3>
        {notificaciones.length > 0 && (
          <button 
            className="clear-all" 
            onClick={() => setNotificaciones([])}>
            Limpiar Todo
          </button>
        )}
      </div>
      
      <div className="notificaciones-lista">
        {notificaciones.map((notif) => (
          <div 
            key={notif.id} 
            className={`notificacion-item ${notif.leida ? 'leida' : 'no-leida'}`}
            onClick={() => marcarLeida(notif.id)}
          >
            <div className="notificacion-contenido">
              <span className="notificacion-producto">{notif.producto}</span>
              <p className="notificacion-mensaje">{notif.mensaje}</p>
              <span className="notificacion-fecha">{notif.fecha}</span>
            </div>
            <button 
              className="eliminar-notificacion" 
              onClick={(e) => {
                e.stopPropagation();
                eliminarNotificacion(notif.id);
              }}>
              ✖
            </button>
          </div>
        ))}
      </div>
      
      <style jsx>{`
        .notificaciones-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          width: 300px;
          max-height: 400px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        
        .notificaciones-header {
          padding: 10px 15px;
          background: #f1f1f1;
          border-bottom: 1px solid #ddd;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .notificaciones-header h3 {
          margin: 0;
          font-size: 14px;
          display: flex;
          align-items: center;
        }
        
        .estado-conectado {
          color: green;
          margin-left: 5px;
        }
        
        .estado-desconectado {
          color: red;
          margin-left: 5px;
        }
        
        .clear-all {
          background: none;
          border: none;
          font-size: 12px;
          color: #666;
          cursor: pointer;
        }
        
        .notificaciones-lista {
          overflow-y: auto;
          max-height: 350px;
        }
        
        .notificacion-item {
          padding: 10px 15px;
          border-bottom: 1px solid #eee;
          cursor: pointer;
          display: flex;
          justify-content: space-between;
          transition: background-color 0.2s;
        }
        
        .notificacion-item:hover {
          background-color: #f9f9f9;
        }
        
        .notificacion-item.no-leida {
          background-color: #f0f7ff;
        }
        
        .notificacion-item.leida {
          opacity: 0.7;
        }
        
        .notificacion-contenido {
          flex: 1;
        }
        
        .notificacion-producto {
          font-weight: bold;
          font-size: 13px;
          display: block;
        }
        
        .notificacion-mensaje {
          margin: 5px 0;
          font-size: 12px;
        }
        
        .notificacion-fecha {
          font-size: 11px;
          color: #888;
          display: block;
        }
        
        .eliminar-notificacion {
          background: none;
          border: none;
          color: #999;
          cursor: pointer;
          font-size: 12px;
          align-self: flex-start;
        }
        
        .eliminar-notificacion:hover {
          color: #ff3333;
        }
      `}</style>
    </div>
  );
};

export default NotificacionInventario; 