import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  Alert
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';

function Login() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { isAuthenticated, login } = useAuth();

  // Si ya está autenticado, redirigir a la página principal
  if (isAuthenticated) {
    return <Navigate to="/" />;
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!password) {
      setError('Por favor ingrese la contraseña');
      return;
    }

    const success = login(password);
    if (!success) {
      setError('Contraseña incorrecta');
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
            >
              Ingresar
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default Login;
