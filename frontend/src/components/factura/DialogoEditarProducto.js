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
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider
} from '@mui/material';
import { 
  calcularPrecioVenta, 
  calcularPrecioBaseUSD, 
  calcularPrecioDirectoEnBs,
  calcularPrecioVentaBs, 
  calcularPrecioBaseUSDDesdeBS,
  aplicarRedondeoEspecial,
  calcularPrecioBaseUSDConGanancia
} from '../../utils/calculosPrecios';

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
 * @param {boolean} props.esEdicionCompleta - Si se está editando desde ListadoProductos (más campos)
 * @returns {JSX.Element} - Componente de diálogo para editar productos
 */
const DialogoEditarProducto = ({ 
  open, 
  onClose, 
  productoEditando, 
  onChange, 
  onSave, 
  tasaCambio, 
  moneda,
  esEdicionCompleta = false
}) => {
  // Manejar cambios en el formulario
  const handleChange = (field, value) => {
    // Si es un campo numérico, validar el formato
    if (['precio_compra_usd', 'unidades_paquete', 'cantidad', 'porcentajeGanancia'].includes(field) && value !== '') {
      // Convertir a string para manejar decimales
      const valueStr = value.toString();
      
      // Verificar que no tenga más de 2 decimales
      if (valueStr.includes('.')) {
        const [parteEntera, parteDecimal] = valueStr.split('.');
        
        // Si tiene más de 2 decimales, truncar
        if (parteDecimal && parteDecimal.length > 2) {
          // Truncar a 2 decimales manteniendo solo los primeros 2 dígitos decimales
          const decimalTruncado = parteDecimal.substring(0, 2);
          value = parseFloat(`${parteEntera}.${decimalTruncado}`);
        }
      }
      
      // Si el valor es NaN, cero o negativo para campos que no deben serlo, corregir
      if (isNaN(value)) {
        value = '';
      } else if (field === 'unidades_paquete' && value <= 0) {
        value = 0.01; // Valor mínimo para unidades
      } else if (field === 'cantidad' && value <= 0) {
        value = 0.01; // Valor mínimo para cantidad
      }
    }
    
    // Si es un cambio en el producto mismo (para el modo edición completa)
    if (field.startsWith('producto.')) {
      const productoField = field.split('.')[1];
      onChange({
        ...productoEditando,
        producto: {
          ...productoEditando.producto,
          [productoField]: value
        }
      });
    } else {
      onChange({
        ...productoEditando,
        [field]: value
      });
    }
  };

  // Calcular el precio de venta basado en los datos actuales
  const calcularPrecioMostrado = () => {
    if (!productoEditando) return null;
    
    const precio_compra = Number(productoEditando.precio_compra_usd) || 0;
    const unidades = Number(productoEditando.unidades_paquete) || 1;
    const porcentaje = Number(productoEditando.porcentajeGanancia) || 0;
    
    if (precio_compra === 0 || unidades === 0 || !tasaCambio) return 0;
    
    if (moneda === 'BS') {
      // Para BS, calcular el precio de venta directamente en bolívares
      const precioVentaBs = calcularPrecioVentaBs(
        precio_compra, // Aquí precio_compra en realidad es el precio en bolívares
        unidades,
        porcentaje,
        productoEditando.aplicarIva
      );
      return precioVentaBs;
    } else {
      // Para USD, mantener la lógica existente
      return calcularPrecioVenta(
        precio_compra,
        unidades,
        tasaCambio.valor,
        porcentaje,
        productoEditando.aplicarIva
      );
    }
  };

  // Calcular el precio base USD dependiendo de la moneda
  const calcularPrecioBaseUSDMostrado = () => {
    if (!productoEditando) return 0;
    
    const precio_compra = Number(productoEditando.precio_compra_usd) || 0;
    const unidades = Number(productoEditando.unidades_paquete) || 1;
    const porcentaje = Number(productoEditando.porcentajeGanancia) || 0;
    
    if (precio_compra === 0 || unidades === 0) return 0;
    
    if (moneda === 'BS' && tasaCambio) {
      // Para BS, calcular primero el precio de venta en bolívares y luego dividir por la tasa
      const precioVentaBs = calcularPrecioVentaBs(
        precio_compra, // Precio en bolívares
        unidades,
        porcentaje,
        productoEditando.aplicarIva
      );
      return calcularPrecioBaseUSDDesdeBS(precioVentaBs, tasaCambio.valor);
    } else {
      // Para USD, usar la nueva función que incluye ganancia e IVA
      return calcularPrecioBaseUSDConGanancia(
        precio_compra,
        unidades,
        porcentaje,
        productoEditando.aplicarIva
      );
    }
  };

  // Calcular el precio final con redondeo
  const calcularPrecioFinal = () => {
    const precioCalculado = calcularPrecioMostrado();
    if (moneda === 'BS') {
      return aplicarRedondeoEspecial(precioCalculado);
    } else {
      return precioCalculado;
    }
  };

  // Validar antes de guardar
  const handleSave = () => {
    // Validar campos requeridos
    if (!productoEditando) return;
    
    const errores = [];
    
    // Validar precio de compra
    if (!productoEditando.precio_compra_usd) {
      errores.push('El precio de compra es obligatorio');
    }
    
    // Validar unidades por paquete
    if (!productoEditando.unidades_paquete) {
      errores.push('Las unidades por paquete son obligatorias');
    }
    
    // Solo validar cantidad si no es edición completa (modo factura)
    if (!esEdicionCompleta) {
      // Validar cantidad
      if (!productoEditando.cantidad || productoEditando.cantidad <= 0) {
        errores.push('La cantidad debe ser mayor a 0');
      }
    }
    
    // Validar que los campos numéricos no tengan más de 2 decimales
    const camposNumericos = [
      { nombre: 'Precio de compra', valor: productoEditando.precio_compra_usd },
      { nombre: 'Unidades por paquete', valor: productoEditando.unidades_paquete },
      { nombre: 'Cantidad', valor: productoEditando.cantidad },
      { nombre: 'Porcentaje de ganancia', valor: productoEditando.porcentajeGanancia }
    ];
    
    camposNumericos.forEach(campo => {
      if (campo.valor) {
        const valueStr = campo.valor.toString();
        if (valueStr.includes('.')) {
          const [, decimal] = valueStr.split('.');
          if (decimal && decimal.length > 2) {
            errores.push(`${campo.nombre} no debe tener más de 2 decimales`);
          }
        }
      }
    });
    
    // Si hay errores, mostrarlos
    if (errores.length > 0) {
      alert(`Por favor corrija los siguientes errores:\n${errores.join('\n')}`);
      return;
    }
    
    // Si todo está bien, guardar
    onSave();
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth={esEdicionCompleta ? "md" : "sm"}
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
          {esEdicionCompleta && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Nombre del Producto"
                value={productoEditando?.producto?.nombre || ''}
                onChange={(e) => handleChange('producto.nombre', e.target.value)}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1
                  }
                }}
              />
            </Grid>
          )}
          
          {esEdicionCompleta && (
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stock Actual"
                type="number"
                value={productoEditando?.producto?.stock_actual || 0}
                onChange={(e) => handleChange('producto.stock_actual', Number(e.target.value))}
                inputProps={{ min: 0, step: 0.01 }}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1
                  }
                }}
              />
            </Grid>
          )}
          
          {esEdicionCompleta && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="tipo-tasa-label">Tipo de Tasa</InputLabel>
                <Select
                  labelId="tipo-tasa-label"
                  value={productoEditando?.producto?.tipo_tasa || 'PARALELO'}
                  onChange={(e) => handleChange('producto.tipo_tasa', e.target.value)}
                  label="Tipo de Tasa"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 1
                    }
                  }}
                >
                  <MenuItem value="BCV">BCV</MenuItem>
                  <MenuItem value="PARALELO">Paralelo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
          
          {esEdicionCompleta && <Grid item xs={12}><Divider sx={{ my: 1 }} /></Grid>}
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label={moneda === 'BS' ? "Precio de Compra (BS)" : "Precio de Compra (USD)"}
              type="number"
              value={productoEditando?.precio_compra_usd || ''}
              onChange={(e) => handleChange('precio_compra_usd', Number(e.target.value))}
              onBlur={(e) => {
                // Formatear a 2 decimales al perder el foco
                if (e.target.value) {
                  handleChange('precio_compra_usd', parseFloat(parseFloat(e.target.value).toFixed(2)));
                }
              }}
              inputProps={{ min: 0, step: 0.01 }}
              variant="outlined"
              sx={{
                mt: esEdicionCompleta ? 0 : 2,
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
              onBlur={(e) => {
                // Formatear a 2 decimales al perder el foco
                if (e.target.value) {
                  handleChange('unidades_paquete', parseFloat(parseFloat(e.target.value).toFixed(2)));
                }
              }}
              inputProps={{ min: 0.01, step: 0.01 }}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1
                }
              }}
            />
          </Grid>
          {!esEdicionCompleta && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Cantidad a Facturar"
                type="number"
                value={productoEditando?.cantidad || ''}
                onChange={(e) => handleChange('cantidad', Number(e.target.value))}
                onBlur={(e) => {
                  // Formatear a 2 decimales al perder el foco
                  if (e.target.value) {
                    handleChange('cantidad', parseFloat(parseFloat(e.target.value).toFixed(2)));
                  }
                }}
                inputProps={{ min: 0.01, step: 0.01 }}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1
                  }
                }}
              />
            </Grid>
          )}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Porcentaje de Ganancia"
              type="number"
              value={productoEditando?.porcentajeGanancia || ''}
              onChange={(e) => handleChange('porcentajeGanancia', Number(e.target.value))}
              onBlur={(e) => {
                // Formatear a 2 decimales al perder el foco
                if (e.target.value) {
                  handleChange('porcentajeGanancia', parseFloat(parseFloat(e.target.value).toFixed(2)));
                }
              }}
              inputProps={{ min: 0, max: 100, step: 0.01 }}
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
                      ${calcularPrecioBaseUSDMostrado().toFixed(2)}
                    </Box>
                  </Typography>
                  <Typography sx={{ fontSize: '0.875rem', color: '#334155', mt: 1 }}>
                    Precio de venta calculado (sin redondeo): 
                    <Box component="span" sx={{ fontWeight: 600, color: '#0f766e', ml: 1 }}>
                      {moneda === 'BS' ? 
                        `${calcularPrecioMostrado().toFixed(2)} Bs` : 
                        `$${calcularPrecioMostrado().toFixed(2)}`
                      }
                      {productoEditando.aplicarIva && ' (incluye IVA 16%)'}
                    </Box>
                  </Typography>
                  {moneda === 'BS' && (
                    <Typography sx={{ fontSize: '0.875rem', color: '#334155', mt: 1 }}>
                      Precio de venta final (con redondeo): 
                      <Box component="span" sx={{ fontWeight: 600, color: '#0f766e', ml: 1 }}>
                        {`${calcularPrecioFinal().toFixed(2)} Bs`}
                      </Box>
                    </Typography>
                  )}
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
            textTransform: 'none',
            fontWeight: 500
          }}
        >
          Cancelar
        </Button>
        <Button 
          variant="contained" 
          onClick={handleSave}
          color="primary"
          sx={{ 
            textTransform: 'none', 
            fontWeight: 500,
            px: 3,
            py: 1,
            backgroundColor: '#0284c7',
            '&:hover': {
              backgroundColor: '#0369a1'
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