import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Componente que protege las rutas que requieren autenticación
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();

  // Si no está autenticado, redirigir a la página de login
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  // Si está autenticado, mostrar el contenido protegido
  return children;
}

export default ProtectedRoute;
