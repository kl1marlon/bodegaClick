import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useAuth } from '../context/AuthContext';
import { Navigate, useNavigate, Link as RouterLink } from 'react-router-dom';
import axios from 'axios';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loyverseRedirectUrl, setLoyverseRedirectUrl] = useState(null);
  const { isAuthenticated, login, loginWithJWT } = useAuth();
  const navigate = useNavigate();

  // Si ya está autenticado, redirigir a la página principal
  if (isAuthenticated) {
    return <Navigate to="/" />;
  }
  
  // Si hay una URL de redirección a Loyverse, redirigir al usuario
  if (loyverseRedirectUrl) {
    window.location.href = loyverseRedirectUrl;
    return <CircularProgress />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validar campos
    if (!username && !password) {
      setError('Por favor ingrese nombre de usuario y contraseña');
      return;
    } else if (!username) {
      setError('Por favor ingrese nombre de usuario');
      return;
    } else if (!password) {
      setError('Por favor ingrese la contraseña');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      // Primero intentar con JWT si hay un nombre de usuario
      if (username) {
        const result = await loginWithJWT(username, password);
        
        if (result.success) {
          // Si el login fue exitoso, verificar la conexión con Loyverse
          try {
            const response = await axios.get('/api/check-loyverse-connection');
            
            // Si la respuesta indica que se necesita conectar con Loyverse
            if (response.data.loyverse_connection_required) {
              setLoyverseRedirectUrl(response.data.loyverse_connect_url);
            } else {
              // Si no se necesita conexión, redirigir a la página principal
              navigate('/');
            }
          } catch (error) {
            // Si hay un error 401 con información de redirección a Loyverse
            if (error.response && error.response.status === 401 && error.response.data.redirect_url) {
              setLoyverseRedirectUrl(error.response.data.redirect_url);
            } else {
              throw error; // Propagar el error para que se maneje abajo
            }
          }
        } else {
          // Si falla el login con JWT, mostrar el error
          setError(result.error || 'Credenciales incorrectas');
        }
      } else {
        // Intentar con el método antiguo si no hay nombre de usuario
        const success = await login(password);
        
        if (!success) {
          setError('Contraseña incorrecta');
          setIsLoading(false);
          return;
        }
        
        // Si el login fue exitoso, verificar la conexión con Loyverse
        try {
          const response = await axios.get('/api/check-loyverse-connection');
          
          // Si la respuesta indica que se necesita conectar con Loyverse
          if (response.data.loyverse_connection_required) {
            setLoyverseRedirectUrl(response.data.loyverse_connect_url);
          } else {
            // Si no se necesita conexión, redirigir a la página principal
            navigate('/');
          }
        } catch (error) {
          // Si hay un error 401 con información de redirección a Loyverse
          if (error.response && error.response.status === 401 && error.response.data.redirect_url) {
            setLoyverseRedirectUrl(error.response.data.redirect_url);
          } else {
            throw error; // Propagar el error para que se maneje abajo
          }
        }
      }
    } catch (error) {
      // Manejar cualquier otro error
      console.error('Error en login:', error);
      setError('Error al iniciar sesión: ' + (error.response?.data?.message || error.message || 'Error desconocido'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper 
          elevation={3} 
          sx={{ 
            p: 4, 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center',
            width: '100%'
          }}
        >
          <Box 
            sx={{ 
              backgroundColor: 'primary.main', 
              borderRadius: '50%', 
              p: 1, 
              mb: 2,
              color: 'white'
            }}
          >
            <LockOutlinedIcon />
          </Box>
          <Typography component="h1" variant="h5" sx={{ mb: 3 }}>
            BodegaClick
          </Typography>
          <Typography component="h2" variant="h6" sx={{ mb: 3 }}>
            Iniciar Sesión
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Nombre de usuario"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Contraseña"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoading}
            >
              {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Ingresar'}
            </Button>
            
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2">
                ¿No tienes una cuenta?{' '}
                <Link component={RouterLink} to="/register" variant="body2">
                  Regístrate aquí
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default Login;
