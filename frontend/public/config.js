// Configuración dinámica para entornos de producción
// En producción, este archivo será reemplazado por un script generado en el entrypoint del contenedor
window.ENV = { 
  API_URL: process.env.REACT_APP_API_URL || "http://localhost:8000/api" 
}; 