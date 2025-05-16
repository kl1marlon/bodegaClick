import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Paper, 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Grid, 
  FormControlLabel, 
  Checkbox, 
  Alert, 
  CircularProgress, 
  Divider 
} from '@mui/material';
import SyncIcon from '@mui/icons-material/Sync';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ShopIcon from '@mui/icons-material/Storefront';

import { 
  getLoyverseStatusAPI, 
  getSyncOptionsAPI, 
  getLoyverseConnectionUrlAPI, 
  syncPricesToLoyverseAPI 
} from '../services/api';

const LoyverseDashboard = () => {
  const [connection, setConnection] = useState(null);
  const [syncOptions, setSyncOptions] = useState({});
  const [selectedOptions, setSelectedOptions] = useState({
    check_only: false,
    force_lower_price: false,
    recalculate_first: false
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    fetchConnectionStatus();
    fetchSyncOptions();
  }, []);

  const fetchConnectionStatus = async () => {
    try {
      setIsLoading(true);
      const { data } = await getLoyverseStatusAPI();
      setConnection(data);
      setError(null);
    } catch (err) {
      console.error('Error al obtener estado de conexión:', err);
      setError('No se pudo cargar el estado de la conexión con Loyverse.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSyncOptions = async () => {
    try {
      const { data } = await getSyncOptionsAPI();
      setSyncOptions(data);
    } catch (err) {
      console.error('Error al obtener opciones de sincronización:', err);
    }
  };

  const handleOptionChange = (event) => {
    setSelectedOptions({
      ...selectedOptions,
      [event.target.name]: event.target.checked
    });
  };

  const handleConnect = async () => {
    try {
      const { data } = await getLoyverseConnectionUrlAPI();
      window.location.href = data.connect_url;
    } catch (err) {
      console.error('Error al obtener URL de conexión:', err);
      setError('No se pudo iniciar el proceso de conexión con Loyverse.');
    }
  };

  const handleSyncPrices = async () => {
    try {
      setIsSyncing(true);
      setSyncResult(null);
      setError(null);
      
      const { data } = await syncPricesToLoyverseAPI(selectedOptions);
      
      setSyncResult({
        success: true,
        message: data.message,
        taskIds: data.task_ids,
        options: data.options
      });
      
      // Refrescar estado después de iniciar sincronización
      setTimeout(fetchConnectionStatus, 2000);
    } catch (err) {
      console.error('Error al sincronizar precios:', err);
      const errorMessage = err.response?.data?.error || 'Ocurrió un error al sincronizar los precios con Loyverse.';
      setError(errorMessage);
      setSyncResult({
        success: false,
        message: errorMessage
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const renderConnectionStatus = () => {
    if (!connection) return null;

    if (!connection.is_connected) {
      return (
        <Card sx={{ mb: 3, bgcolor: '#f5f5f5' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <ErrorIcon color="warning" sx={{ mr: 1, verticalAlign: 'middle' }} />
              Sin conexión a Loyverse
            </Typography>
            <Typography variant="body1" paragraph>
              No has conectado tu cuenta de BodegaClick con Loyverse. Conecta tu cuenta para sincronizar precios automáticamente.
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleConnect}
              startIcon={<ShopIcon />}
            >
              Conectar con Loyverse
            </Button>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card sx={{ mb: 3, bgcolor: '#f8f8ff' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <CheckCircleIcon color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
            Conectado a Loyverse
          </Typography>
          
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">Cuenta:</Typography>
              <Typography variant="body1">{connection.account_name}</Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">Email:</Typography>
              <Typography variant="body1">{connection.email}</Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">Estado del token:</Typography>
              <Typography variant="body1">
                {connection.token_status === 'valid' && 'Válido'}
                {connection.token_status === 'expired' && 'Expirado (Se renovará automáticamente)'}
                {connection.token_status === 'inactive' && 'Inactivo'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">Última sincronización:</Typography>
              <Typography variant="body1">
                {connection.last_sync_time ? new Date(connection.last_sync_time).toLocaleString() : 'Nunca'}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="textSecondary">Estado de sincronización:</Typography>
              <Typography variant="body1">
                {connection.price_sync_status === 'IDLE' && 'Inactivo'}
                {connection.price_sync_status === 'QUEUED' && 'En cola'}
                {connection.price_sync_status === 'SYNCING' && 'Sincronizando...'}
                {connection.price_sync_status === 'COMPLETED' && 'Completado'}
                {connection.price_sync_status === 'FAILED' && 'Fallido'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const renderSyncOptions = () => {
    if (!connection?.is_connected) return null;
    
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Opciones de sincronización
          </Typography>
          
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {Object.keys(syncOptions).map((option) => (
              <Grid item xs={12} key={option}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedOptions[option] || false}
                      onChange={handleOptionChange}
                      name={option}
                      disabled={isSyncing}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body1">{syncOptions[option].label}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {syncOptions[option].help_text}
                      </Typography>
                    </Box>
                  }
                />
              </Grid>
            ))}
          </Grid>
          
          <Box mt={3}>
            <Button
              variant="contained"
              color="primary"
              disabled={isSyncing || connection.price_sync_status === 'SYNCING' || connection.price_sync_status === 'QUEUED'}
              onClick={handleSyncPrices}
              startIcon={isSyncing ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
              fullWidth
            >
              {isSyncing ? 'Iniciando sincronización...' : 'Sincronizar precios con Loyverse'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Integración con Loyverse
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="body1" paragraph>
          Desde este panel puedes gestionar la conexión de tu cuenta con Loyverse y sincronizar los precios de tus productos.
        </Typography>
      </Paper>
      
      {isLoading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {syncResult && (
            <Alert 
              severity={syncResult.success ? "success" : "error"} 
              sx={{ mb: 3 }}
              onClose={() => setSyncResult(null)}
            >
              {syncResult.message}
            </Alert>
          )}
          
          {renderConnectionStatus()}
          
          {renderSyncOptions()}
        </>
      )}
    </Container>
  );
};

export default LoyverseDashboard;
