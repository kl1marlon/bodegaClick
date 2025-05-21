import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

// Crear el contexto de autenticación
const AuthContext = createContext(null);

// Proveedor del contexto de autenticación
export const AuthProvider = ({ children }) => {
  // Estados para la autenticación
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Comprobar si hay una sesión guardada al cargar la aplicación
  useEffect(() => {
    const checkAuth = async () => {
      setLoading(true);
      
      // Verificar si hay tokens JWT almacenados
      const accessToken = localStorage.getItem('access_token');
      const userId = localStorage.getItem('user_id');
      const username = localStorage.getItem('username');
      
      if (accessToken) {
        // Configurar el token en los headers para futuras peticiones
        axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
        
        try {
          // Verificar si el token es válido y la conexión con Loyverse está activa
          await axios.get('/api/check-loyverse-connection/');
          
          // Si llegamos aquí, el token es válido y la conexión está activa
          setIsAuthenticated(true);
          setUser({ id: userId, username });
        } catch (error) {
          // Si hay un error de autenticación o la conexión con Loyverse no está activa
          console.error('Error verificando autenticación:', error);
          
          // Si es un error de conexión con Loyverse, mantener la autenticación
          if (error.response && error.response.status === 401 && error.response.data.loyverse_connection_required) {
            setIsAuthenticated(true);
            setUser({ id: userId, username });
            // No redirigimos aquí, eso se maneja en los componentes
          } else {
            // Otro tipo de error, limpiar la autenticación
            logout();
          }
        }
      } else {
        // También verificar el método antiguo de autenticación
        const storedAuth = localStorage.getItem('isAuthenticated');
        if (storedAuth === 'true') {
          setIsAuthenticated(true);
        }
      }
      
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  // Función para iniciar sesión con JWT
  const loginWithJWT = async (username, password) => {
    try {
      const response = await axios.post('/api/token/', {
        username,
        password
      });
      
      const { access, refresh, user_id } = response.data;
      
      // Guardar tokens y datos de usuario
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_id', user_id);
      localStorage.setItem('username', username);
      
      // Configurar el token en los headers para futuras peticiones
      axios.defaults.headers.common['Authorization'] = `Bearer ${access}`;
      
      setIsAuthenticated(true);
      setUser({ id: user_id, username });
      
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error en login JWT:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Error de autenticación'
      };
    }
  };
  
  // Función para iniciar sesión con la contraseña antigua
  const login = async (password) => {
    // Mantener compatibilidad con el sistema antiguo
    if (password === 'bodegaclick123') {
      setIsAuthenticated(true);
      localStorage.setItem('isAuthenticated', 'true');
      
      // Verificar la conexión con Loyverse
      try {
        const response = await axios.get('/api/check-loyverse-connection/');
        return true;
      } catch (error) {
        // Si hay un error pero es por la conexión con Loyverse, seguimos con el login
        if (error.response && error.response.status === 401 && error.response.data.loyverse_connection_required) {
          return true;
        }
        // Otro tipo de error
        return false;
      }
    }
    return false;
  };

  // Función para registrar un nuevo usuario
  const register = (userId, username) => {
    setIsAuthenticated(true);
    setUser({ id: userId, username });
    localStorage.setItem('user_id', userId);
    localStorage.setItem('username', username);
  };

  // Función para cerrar sesión
  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    
    // Limpiar todos los datos de autenticación
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    
    // Limpiar el token de los headers
    delete axios.defaults.headers.common['Authorization'];
  };

  // Proporcionar el contexto a los componentes hijos
  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      user,
      loading,
      login, 
      loginWithJWT,
      register,
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook personalizado para usar el contexto de autenticación
export const useAuth = () => {
  return useContext(AuthContext);
};
