import React, { createContext, useState, useContext, useEffect } from 'react';

// Crear el contexto de autenticación
const AuthContext = createContext(null);

// Proveedor del contexto de autenticación
export const AuthProvider = ({ children }) => {
  // Estado para almacenar si el usuario está autenticado
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Comprobar si hay una sesión guardada al cargar la aplicación
  useEffect(() => {
    const storedAuth = localStorage.getItem('isAuthenticated');
    if (storedAuth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  // Función para iniciar sesión
  const login = (password) => {
    // Contraseña simple para autenticación
    // En un entorno de producción real, esto debería usar un sistema más seguro
    if (password === 'bodegaclick123') {
      setIsAuthenticated(true);
      localStorage.setItem('isAuthenticated', 'true');
      return true;
    }
    return false;
  };

  // Función para cerrar sesión
  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
  };

  // Proporcionar el contexto a los componentes hijos
  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook personalizado para usar el contexto de autenticación
export const useAuth = () => {
  return useContext(AuthContext);
};
