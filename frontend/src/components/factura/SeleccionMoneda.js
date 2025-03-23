import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid
} from '@mui/material';

/**
 * Componente para selección de moneda en el sistema de facturación
 * 
 * @param {Object} props - Propiedades del componente
 * @param {string} props.moneda - Moneda seleccionada ('USD' o 'BS')
 * @param {function} props.onMonedaChange - Función a llamar cuando cambia la selección de moneda
 * @returns {JSX.Element} - Componente de selección de moneda
 */
const SeleccionMoneda = ({ moneda, onMonedaChange }) => {
  // Estado para controlar el diálogo de confirmación al cambiar moneda
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [monedaTemp, setMonedaTemp] = React.useState('');

  // Manejador de cambio de moneda con confirmación
  const handleMonedaChange = (event) => {
    // Si ya hay una moneda seleccionada y es diferente, pedir confirmación
    if (moneda && event.target.value !== moneda) {
      setMonedaTemp(event.target.value);
      setDialogOpen(true);
    } else {
      // Si es la primera selección, aplicar directamente
      onMonedaChange(event.target.value);
    }
  };

  // Confirmar el cambio de moneda
  const confirmCambioMoneda = () => {
    onMonedaChange(monedaTemp);
    setDialogOpen(false);
  };

  // Cancelar el cambio de moneda
  const cancelCambioMoneda = () => {
    setDialogOpen(false);
  };

  return (
    <>
      <FormControl fullWidth variant="outlined">
        <InputLabel>Moneda</InputLabel>
        <Select 
          value={moneda} 
          onChange={handleMonedaChange}
          label="Moneda"
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
          <MenuItem value="USD">Dólares (USD)</MenuItem>
          <MenuItem value="BS">Bolívares (BS)</MenuItem>
        </Select>
      </FormControl>
      
      {/* Información adicional sobre la selección de moneda */}
      {moneda && (
        <Typography 
          variant="body2" 
          sx={{ 
            mt: 1, 
            color: '#64748b',
            fontSize: '0.875rem',
            fontStyle: 'italic'
          }}
        >
          {moneda === 'USD' 
            ? 'Los precios se manejarán en dólares y se convertirán a bolívares según la tasa.' 
            : 'Los precios se manejarán directamente en bolívares.'}
        </Typography>
      )}

      {/* Diálogo de confirmación para cambio de moneda */}
      <Dialog 
        open={dialogOpen} 
        onClose={cancelCambioMoneda}
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: 24
          }
        }}
      >
        <DialogTitle sx={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#334155' }}>
            Cambiar moneda de facturación
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ p: 3, mt: 2 }}>
          <Typography variant="body1" sx={{ color: '#475569' }}>
            ¿Está seguro de cambiar la moneda de facturación? 
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b', mt: 2 }}>
            Si cambia la moneda, se reiniciarán todos los productos seleccionados y cálculos realizados hasta ahora.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, backgroundColor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button 
            onClick={cancelCambioMoneda} 
            sx={{ 
              color: '#64748b',
              fontWeight: 500,
              borderRadius: 1,
              '&:hover': {
                backgroundColor: '#f1f5f9'
              }
            }}
          >
            Cancelar
          </Button>
          <Button 
            onClick={confirmCambioMoneda} 
            variant="contained"
            sx={{ 
              backgroundColor: '#3b82f6',
              fontWeight: 500,
              borderRadius: 1,
              textTransform: 'none',
              '&:hover': {
                backgroundColor: '#2563eb'
              }
            }}
          >
            Cambiar moneda
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SeleccionMoneda; 