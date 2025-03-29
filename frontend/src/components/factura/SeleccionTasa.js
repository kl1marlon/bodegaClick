import React, { useState, useEffect } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Paper,
  Grid
} from '@mui/material';
import EditAttributesIcon from '@mui/icons-material/EditAttributes';
import { useDispatch } from 'react-redux';
import { fetchLatestTasa, createTasaCambio } from '../../store/tasasCambioSlice';

/**
 * Componente para selección y edición de tasas de cambio
 * 
 * @param {Object} props - Propiedades del componente
 * @param {string} props.tipoTasa - Tipo de tasa seleccionada ('BCV' o 'PARALELO')
 * @param {function} props.onTipoTasaChange - Función a llamar cuando cambia el tipo de tasa
 * @param {Object} props.tasaCambio - Objeto con la información de la tasa de cambio actual
 * @param {function} props.onTasaUpdated - Función a llamar cuando se actualiza la tasa
 * @param {function} props.onError - Función para manejar errores
 * @returns {JSX.Element} - Componente de selección de tasa
 */
const SeleccionTasa = ({ tipoTasa, onTipoTasaChange, tasaCambio, onTasaUpdated, onError }) => {
  const dispatch = useDispatch();
  
  // Estados locales
  const [tasaDialogOpen, setTasaDialogOpen] = useState(false);
  const [nuevaTasaValor, setNuevaTasaValor] = useState('');

  // Actualizar el valor inicial del campo cuando cambia la tasa
  useEffect(() => {
    if (tasaCambio) {
      setNuevaTasaValor(tasaCambio.valor);
    }
  }, [tasaCambio]);
  
  // Abrir el diálogo de edición de tasa
  const handleOpenTasaDialog = () => {
    setNuevaTasaValor(tasaCambio ? tasaCambio.valor : '');
    setTasaDialogOpen(true);
  };
  
  // Cerrar el diálogo de edición de tasa
  const handleCloseTasaDialog = () => {
    setTasaDialogOpen(false);
  };
  
  // Guardar la nueva tasa de cambio
  const handleSaveTasa = () => {
    if (!nuevaTasaValor || nuevaTasaValor <= 0) {
      onError('Por favor ingrese un valor válido para la tasa de cambio');
      return;
    }

    const tasaData = {
      tipo: tipoTasa,
      valor: parseFloat(nuevaTasaValor),
      fecha: new Date().toISOString().split('T')[0]
    };

    dispatch(createTasaCambio(tasaData))
      .then(response => {
        if (onTasaUpdated) {
          onTasaUpdated(`Tasa de cambio ${tipoTasa} actualizada correctamente`);
        }
        setTasaDialogOpen(false);
      })
      .catch(error => {
        onError('Error al actualizar la tasa de cambio: ' + (error.response?.data?.error || error.message));
      });
  };

  return (
    <Box>
      <Box display="flex" alignItems="center">
        <FormControl fullWidth variant="outlined">
          <InputLabel>Tipo de Tasa</InputLabel>
          <Select 
            value={tipoTasa} 
            onChange={(e) => onTipoTasaChange(e.target.value)}
            label="Tipo de Tasa"
            sx={{
              borderRadius: 1,
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#cbd5e1'
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#94a3b8'
              }
            }}
          >
            <MenuItem value="BCV">Tasa BCV</MenuItem>
            <MenuItem value="PARALELO">Tasa Paralelo</MenuItem>
          </Select>
        </FormControl>
        
        {tipoTasa && 
          <Tooltip title="Editar valor de tasa" arrow>
            <IconButton 
              color="primary" 
              onClick={handleOpenTasaDialog}
              sx={{ 
                ml: 1,
                backgroundColor: '#f1f5f9',
                '&:hover': {
                  backgroundColor: '#e2e8f0'
                }
              }}
            >
              <EditAttributesIcon />
            </IconButton>
          </Tooltip>
        }
      </Box>
      
      {tipoTasa && tasaCambio && (
        <Typography 
          variant="body2" 
          sx={{ 
            mt: 1, 
            color: '#64748b',
            fontSize: '0.875rem',
            fontStyle: 'italic'
          }}
        >
          Tasa actual: {tipoTasa} = {tasaCambio.valor} Bs/USD 
          (última actualización: {new Date(tasaCambio.fecha).toLocaleDateString()})
        </Typography>
      )}

      {/* Diálogo para editar tasa de cambio */}
      <Dialog 
        open={tasaDialogOpen} 
        onClose={handleCloseTasaDialog}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: 24
          }
        }}
      >
        <DialogTitle 
          sx={{ 
            backgroundColor: '#f8fafc', 
            borderBottom: '1px solid #e2e8f0',
            px: 3,
            py: 2
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#334155' }}>
            Editar Tasa de Cambio {tipoTasa}
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          <Grid container spacing={3} sx={{ mt: 0 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={`Valor actual de la tasa ${tipoTasa}`}
                type="number"
                value={nuevaTasaValor}
                onChange={(e) => setNuevaTasaValor(Number(e.target.value))}
                inputProps={{ min: 0, step: 0.01 }}
                helperText={`Valor actual: ${tasaCambio?.valor || 'No disponible'} Bs/USD`}
                variant="outlined"
                sx={{
                  mt: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2, 
                  backgroundColor: '#f8fafc', 
                  borderRadius: 1,
                  border: '1px solid #e2e8f0'
                }}
              >
                <Typography sx={{ fontSize: '0.875rem', color: '#64748b' }}>
                  Al guardar se creará un nuevo registro con la fecha actual. Este valor será utilizado para todos los cálculos.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions 
          sx={{ 
            px: 3, 
            py: 2, 
            backgroundColor: '#f8fafc',
            borderTop: '1px solid #e2e8f0'
          }}
        >
          <Button 
            onClick={handleCloseTasaDialog} 
            sx={{ 
              color: '#64748b',
              fontWeight: 500,
              borderRadius: 1,
              px: 3,
              '&:hover': {
                backgroundColor: '#f1f5f9'
              }
            }}
          >
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveTasa} 
            variant="contained"
            sx={{ 
              backgroundColor: '#3b82f6',
              fontWeight: 500,
              borderRadius: 1,
              textTransform: 'none',
              px: 3,
              '&:hover': {
                backgroundColor: '#2563eb'
              }
            }}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SeleccionTasa; 