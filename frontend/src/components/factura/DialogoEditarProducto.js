import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Typography,
  Paper,
  Box
} from '@mui/material';
import { calcularPrecioVenta, calcularPrecioBaseUSD, calcularPrecioDirectoEnBs } from '../../utils/calculosPrecios';

/**
 * Componente de diálogo para editar detalles de un producto
 * 
 * @param {Object} props - Propiedades del componente
 * @param {boolean} props.open - Si el diálogo está abierto
 * @param {function} props.onClose - Función para cerrar el diálogo
 * @param {Object} props.productoEditando - Objeto con los datos del producto en edición
 * @param {function} props.onChange - Función para actualizar los datos del producto
 * @param {function} props.onSave - Función para guardar los cambios
 * @param {Object} props.tasaCambio - Objeto con información de la tasa de cambio
 * @param {string} props.moneda - Moneda seleccionada ('USD' o 'BS')
 * @returns {JSX.Element} - Componente de diálogo para editar productos
 */
const DialogoEditarProducto = ({ open, onClose, productoEditando, onChange, onSave, tasaCambio, moneda }) => {
  // Manejar cambios en el formulario
  const handleChange = (field, value) => {
    onChange({
      ...productoEditando,
      [field]: value
    });
  };

  // Calcular el precio de venta basado en los datos actuales
  const calcularPrecioMostrado = () => {
    if (!productoEditando) return null;
    
    const precio_compra = Number(productoEditando.precio_compra_usd) || 0;
    const unidades = Number(productoEditando.unidades_paquete) || 1;
    const porcentaje = Number(productoEditando.porcentajeGanancia) || 0;
    
    if (precio_compra === 0 || unidades === 0 || !tasaCambio) return 0;
    
    if (moneda === 'BS') {
      return calcularPrecioVenta(
        precio_compra,
        unidades,
        tasaCambio.valor,
        porcentaje,
        productoEditando.aplicarIva
      );
    } else {
      // Para USD
      const precioDirectoBs = calcularPrecioDirectoEnBs(
        precio_compra,
        unidades,
        tasaCambio.valor,
        porcentaje,
        productoEditando.aplicarIva
      );
      return precioDirectoBs;
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
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
          {productoEditando?.producto ? productoEditando.producto.nombre : 'Editar Producto'}
        </Typography>
      </DialogTitle>
      <DialogContent sx={{ p: 3 }}>
        <Grid container spacing={3} sx={{ mt: 0 }}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Precio de Compra (USD)"
              type="number"
              value={productoEditando?.precio_compra_usd || ''}
              onChange={(e) => handleChange('precio_compra_usd', Number(e.target.value))}
              inputProps={{ min: 0, step: 0.01 }}
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
            <TextField
              fullWidth
              label="Unidades por Paquete"
              type="number"
              value={productoEditando?.unidades_paquete || ''}
              onChange={(e) => handleChange('unidades_paquete', Number(e.target.value))}
              inputProps={{ min: 1 }}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1
                }
              }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Cantidad a Facturar"
              type="number"
              value={productoEditando?.cantidad || ''}
              onChange={(e) => handleChange('cantidad', Number(e.target.value))}
              inputProps={{ min: 1 }}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1
                }
              }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Porcentaje de Ganancia"
              type="number"
              value={productoEditando?.porcentajeGanancia || ''}
              onChange={(e) => handleChange('porcentajeGanancia', Number(e.target.value))}
              inputProps={{ min: 0, max: 100, step: 1 }}
              helperText="Dejar vacío para usar el porcentaje global"
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1
                }
              }}
            />
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={productoEditando?.aplicarIva || false}
                  onChange={(e) => handleChange('aplicarIva', e.target.checked)}
                  color="primary"
                />
              }
              label="Aplicar IVA (16%)"
              sx={{ color: '#4b5563' }}
            />
          </Grid>
          {productoEditando && tasaCambio && (
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
                <Box>
                  <Typography sx={{ fontSize: '0.875rem', color: '#334155', fontWeight: 500 }}>
                    Información adicional:
                  </Typography>
                  <Typography sx={{ fontSize: '0.875rem', color: '#334155', mt: 1 }}>
                    Precio base USD: 
                    <Box component="span" sx={{ fontWeight: 600, color: '#0f766e', ml: 1 }}>
                      ${calcularPrecioBaseUSD(
                        productoEditando.precio_compra_usd,
                        productoEditando.unidades_paquete
                      ).toFixed(2)}
                    </Box>
                  </Typography>
                  <Typography sx={{ fontSize: '0.875rem', color: '#334155', mt: 1 }}>
                    Precio de venta calculado: 
                    <Box component="span" sx={{ fontWeight: 600, color: '#0f766e', ml: 1 }}>
                      {moneda === 'BS' ? 
                        `${calcularPrecioMostrado().toFixed(2)} Bs` : 
                        `${calcularPrecioMostrado().toFixed(2)} Bs`
                      }
                      {productoEditando.aplicarIva && ' (incluye IVA 16%)'}
                    </Box>
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          )}
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
          onClick={onClose} 
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
          onClick={onSave} 
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
  );
};

export default DialogoEditarProducto; 