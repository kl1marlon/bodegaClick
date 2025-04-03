import React, { useState, useEffect } from 'react';
import { Button, Box, Typography, Paper, List, ListItem, ListItemText, Alert, CircularProgress, Divider, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { detectApiUrl } from '../../utils/apiTest';
import axios from 'axios';

const ConexionAPI = () => {
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState([]);
  const [apiUrl, setApiUrl] = useState(null);
  const [workerUrl, setWorkerUrl] = useState(null);
  const [dbState, setDbState] = useState(null);

  // Función para verificar la conexión a la API
  const testConnection = async () => {
    setTesting(true);
    setResults([]);
    
    try {
      // Registrar configuración actual
      const configInfo = {
        api: window.ENV?.API_URL || 'No definido',
        worker: window.ENV?.WORKER_URL || 'No definido',
        reactEnv: process.env.REACT_APP_API_URL || 'No definido'
      };
      
      setResults(prev => [...prev, {
        success: true,
        message: 'Configuración actual detectada',
        details: configInfo
      }]);
      
      // Probar detectando la URL de la API principal
      const result = await detectApiUrl();
      setApiUrl(result.url);
      
      setResults(prev => [...prev, {
        success: result.success,
        message: result.success 
          ? `Conexión exitosa a API: ${result.url}` 
          : 'No se pudo conectar a la API principal',
        details: result
      }]);
      
      // Probar detectando la URL del worker
      try {
        // Si estamos usando rutas relativas, intenta worker-api directamente
        const workerUrlToTry = window.ENV?.WORKER_URL || '/worker-api';
        console.log(`Probando conexión al worker: ${workerUrlToTry}`);
        
        // Probar usando el endpoint de estado de tareas
        const workerResponse = await axios.get(`${workerUrlToTry}/tareas/listado/?_=${Date.now()}`, {
          timeout: 5000
        });
        
        setWorkerUrl(workerUrlToTry);
        setResults(prev => [...prev, {
          success: true,
          message: `Conexión exitosa al Worker: ${workerUrlToTry}`,
          details: { tareas: workerResponse.data.length }
        }]);
      } catch (workerError) {
        console.error('Error conectando con worker:', workerError);
        setResults(prev => [...prev, {
          success: false,
          message: 'Error al conectar con el worker',
          details: workerError.message
        }]);
      }
      
      if (result.success) {
        // Probar la salud del backend
        try {
          const healthResponse = await axios.get(`${result.url.replace(/\/api\/?$/, '')}/health/`);
          setResults(prev => [...prev, {
            success: true,
            message: 'Verificación de salud del backend exitosa',
            details: healthResponse.data
          }]);
        } catch (error) {
          setResults(prev => [...prev, {
            success: false,
            message: 'No se pudo verificar la salud del backend',
            details: error.message
          }]);
        }
        
        // Verificar el estado de la base de datos
        try {
          const dbResponse = await axios.get(`${result.url}/info/database/`);
          setDbState(dbResponse.data);
          setResults(prev => [...prev, {
            success: true,
            message: 'Conexión a base de datos verificada',
            details: dbResponse.data
          }]);
        } catch (error) {
          setResults(prev => [...prev, {
            success: false,
            message: 'No se pudo verificar el estado de la base de datos',
            details: error.message
          }]);
        }
        
        // Probar endoint de facturas específicamente
        try {
          const facturasResponse = await axios.get(`${result.url}/facturas/`, {
            params: { limit: 1, _: Date.now() }
          });
          setResults(prev => [...prev, {
            success: true,
            message: `Conexión a endpoint de facturas exitosa (${facturasResponse.data.length} registros)`,
            details: facturasResponse.data.length > 0 
              ? `Se encontraron ${facturasResponse.data.length} facturas`
              : 'No hay facturas en la base de datos'
          }]);
        } catch (error) {
          setResults(prev => [...prev, {
            success: false,
            message: 'Error al consultar facturas',
            details: error.message
          }]);
        }
      }
    } catch (error) {
      setResults(prev => [...prev, {
        success: false,
        message: 'Error durante el diagnóstico',
        details: error.message
      }]);
    } finally {
      setTesting(false);
    }
  };

  // Ejecutar la prueba al cargar
  useEffect(() => {
    testConnection();
  }, []);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Diagnóstico de conexión a la API
      </Typography>
      
      <Box sx={{ mb: 2 }}>
        <Alert severity={apiUrl ? "success" : "warning"}>
          {apiUrl 
            ? `API principal detectada: ${apiUrl}`
            : 'No se ha detectado una API principal funcional'
          }
        </Alert>
        
        <Alert severity={workerUrl ? "success" : "warning"} sx={{ mt: 1 }}>
          {workerUrl 
            ? `Worker API detectada: ${workerUrl}`
            : 'No se ha detectado una conexión al worker'
          }
        </Alert>
      </Box>
      
      <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
        {results.map((result, index) => (
          <React.Fragment key={index}>
            {index > 0 && <Divider variant="inset" component="li" />}
            <ListItem alignItems="flex-start">
              {result.success 
                ? <CheckCircleIcon color="success" sx={{ mr: 2 }} /> 
                : <ErrorIcon color="error" sx={{ mr: 2 }} />
              }
              <ListItemText
                primary={result.message}
                secondary={
                  <Typography
                    sx={{ display: 'inline' }}
                    component="span"
                    variant="body2"
                    color="text.primary"
                  >
                    {typeof result.details === 'object' 
                      ? JSON.stringify(result.details, null, 2)
                      : result.details}
                  </Typography>
                }
              />
            </ListItem>
          </React.Fragment>
        ))}
        
        {testing && (
          <ListItem>
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <ListItemText primary="Realizando pruebas..." />
          </ListItem>
        )}
      </List>
      
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={testConnection}
          disabled={testing}
        >
          {testing ? 'Probando...' : 'Probar conexión nuevamente'}
        </Button>
        
        <Chip 
          label={testing ? "Probando..." : "Última prueba: " + new Date().toLocaleTimeString()} 
          color={apiUrl && workerUrl ? "success" : apiUrl ? "warning" : "error"}
          variant="outlined"
        />
      </Box>
    </Paper>
  );
};

export default ConexionAPI; 