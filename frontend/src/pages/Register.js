import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Link,
  Divider
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import StorefrontIcon from '@mui/icons-material/Storefront';
import { useAuth } from '../context/AuthContext';
import { Navigate, useNavigate, Link as RouterLink } from 'react-router-dom';
import axios from 'axios';

function Register() {
  // Estados para el formulario
  const [activeStep, setActiveStep] = useState(0);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loyverseRedirectUrl, setLoyverseRedirectUrl] = useState(null);
  
  const { isAuthenticated, register } = useAuth();
  const navigate = useNavigate();

  // Función para iniciar registro directo con Loyverse
  const handleRegisterWithLoyverse = () => {
    setIsLoading(true);
    // Redireccionar al endpoint de registro con Loyverse
    window.location.href = process.env.REACT_APP_API_URL + '/loyverse/register/';
  };

  // Si ya está autenticado, redirigir a la página principal
  if (isAuthenticated) {
    return <Navigate to="/" />;
  }
  
  // Si hay una URL de redirección a Loyverse, redirigir al usuario
  if (loyverseRedirectUrl) {
    window.location.href = loyverseRedirectUrl;
    return <CircularProgress />;
  }

  // Pasos del registro
  const steps = ['Información de cuenta', 'Conectar con Loyverse'];

  // Validar el formulario
  const validateForm = () => {
    if (!username || !email || !password || !confirmPassword || !businessName) {
      setError('Por favor complete todos los campos');
      return false;
    }
    
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return false;
    }
    
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return false;
    }
    
    // Validación básica de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Por favor ingrese un email válido');
      return false;
    }
    
    return true;
  };

  // Manejar el envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      // Simulamos un registro exitoso mientras el backend se actualiza
      // En lugar de enviar datos al backend, usamos la contraseña fija
      if (password === 'bodegaclick123') {
        // Simulamos un registro exitoso
        const user_id = '1'; // ID simulado
        
        // Registrar en el contexto
        register(user_id, username);
        
        // Guardar datos para simular un usuario registrado
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('username', username);
        localStorage.setItem('email', email);
        localStorage.setItem('business_name', businessName);
        
        // Redirigir a la conexión con Loyverse
        setLoyverseRedirectUrl('/loyverse/connect/');
        setActiveStep(1);
        
        // Esperar un poco para mostrar el progreso
        setTimeout(() => {
          window.location.href = '/loyverse/connect/';
        }, 2000);
      } else {
        setError('La contraseña debe ser "bodegaclick123" para este demo');
        setIsLoading(false);
        return;
      }
      
      /* Código original comentado para referencia futura
      // Enviar datos de registro al backend
      const response = await axios.post('/api/register/', {
        username,
        email,
        password,
        business_name: businessName
      });
      
      // Si el registro fue exitoso, iniciar sesión automáticamente
      if (response.data.access) {
        // Guardar tokens
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        
        // Registrar en el contexto
        register(response.data.user_id, response.data.username);
        
        // Verificar si se requiere conexión con Loyverse
        if (response.data.loyverse_connection_required) {
          setLoyverseRedirectUrl(response.data.loyverse_connect_url);
          setActiveStep(1);
        } else {
          // Si no se necesita conexión, redirigir a la página principal
          navigate('/');
        }
      }
      */
    } catch (error) {
      // Manejar errores
      console.error('Error en registro:', error);
      setError('Error al registrar: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
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
            <PersonAddIcon />
          </Box>
          <Typography component="h1" variant="h5" sx={{ mb: 1 }}>
            BodegaClick
          </Typography>
          <Typography component="h2" variant="h6" sx={{ mb: 3 }}>
            Crear Cuenta
          </Typography>
          
          <Stepper activeStep={activeStep} sx={{ width: '100%', mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {activeStep === 0 && (
            <>
              <Box sx={{ width: '100%', mb: 3 }}>
                <Button
                  fullWidth
                  variant="contained"
                  color="secondary"
                  startIcon={<StorefrontIcon />}
                  onClick={handleRegisterWithLoyverse}
                  disabled={isLoading}
                  sx={{ py: 1.5 }}
                >
                  {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Registrarse con Loyverse'}
                </Button>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
                  La manera más rápida de comenzar: conecta directamente con tu cuenta de Loyverse
                </Typography>
              </Box>
              
              <Divider sx={{ width: '100%', mb: 3 }}>
                <Typography variant="body2" color="text.secondary">o registrarse manualmente</Typography>
              </Divider>
              
              <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
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
                  id="email"
                  label="Correo electrónico"
                  name="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="businessName"
                  label="Nombre del negocio"
                  name="businessName"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                />
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  name="password"
                  label="Contraseña"
                  type="password"
                  id="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  name="confirmPassword"
                  label="Confirmar contraseña"
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 3, mb: 2 }}
                  disabled={isLoading}
                >
                  {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Registrarse'}
                </Button>
              </Box>
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Typography variant="body2">
                  ¿Ya tienes una cuenta?{' '}
                  <Link component={RouterLink} to="/login" variant="body2">
                    Iniciar sesión
                  </Link>
                </Typography>
              </Box>
            </>
          )}
          
          {activeStep === 1 && (
            <Box sx={{ width: '100%', textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 3 }}>
                Para completar el registro, necesitas conectar tu cuenta con Loyverse.
                Serás redirigido a Loyverse para autorizar la conexión.
              </Typography>
              
              <CircularProgress sx={{ mb: 3 }} />
              
              <Typography variant="body2" color="text.secondary">
                Si no eres redirigido automáticamente, haz clic en el botón de abajo.
              </Typography>
              
              <Button
                variant="contained"
                sx={{ mt: 3 }}
                onClick={() => window.location.href = loyverseRedirectUrl}
              >
                Conectar con Loyverse
              </Button>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
}

export default Register;
