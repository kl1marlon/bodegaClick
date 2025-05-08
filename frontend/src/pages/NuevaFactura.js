import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControlLabel,
  Switch,
  Snackbar,
  Alert
} from '@mui/material';

import { fetchProductos } from '../store/productosSlice';
import { fetchLatestTasa } from '../store/tasasCambioSlice';
import { createFactura } from '../store/facturasSlice';

// Componentes modularizados
import SeleccionMoneda from '../components/factura/SeleccionMoneda';
import SeleccionTasa from '../components/factura/SeleccionTasa';
import BuscadorProductos from '../components/factura/BuscadorProductos';
import TablaProductos from '../components/factura/TablaProductos';
import DialogoEditarProducto from '../components/factura/DialogoEditarProducto';

// Utilidades
import { 
  calcularPrecioVenta, 
  calcularPrecioBaseUSD, 
  aplicarRedondeoEspecial, 
  calcularPrecioBs,
  calcularPrecioVentaBs,
  calcularPrecioBaseUSDDesdeBS,
  calcularPrecioBaseUSDConGanancia
} from '../utils/calculosPrecios';

// Usar la misma URL base que en el resto de la aplicación
const getApiUrl = () => {
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const API_URL = getApiUrl();

const NuevaFactura = () => {
  const dispatch = useDispatch();
  const productos = useSelector((state) => state.productos.items);
  const tasaCambio = useSelector((state) => state.tasasCambio.latestTasa);
  const latestTasas = useSelector((state) => state.tasasCambio.latestTasas);
  
  // Estados principales
  const [moneda, setMoneda] = useState('');
  const [tipoTasa, setTipoTasa] = useState('');
  const [productosSeleccionados, setProductosSeleccionados] = useState([]);
  const [cantidad, setCantidad] = useState(1);
  
  // Estado para manejo de porcentaje de ganancia global
  const [porcentajeGanancia, setPorcentajeGanancia] = useState(30);
  const [actualizarPrecios, setActualizarPrecios] = useState(true);
  
  // Estados para manejo de dialogo de edición
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProductIndex, setEditingProductIndex] = useState(null);
  const [productoEditando, setProductoEditando] = useState({
    porcentajeGanancia: null,
    cantidad: 0,
    aplicarIva: false
  });
  
  // Estado para feedback al usuario
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  // Cargar productos al iniciar
  useEffect(() => {
    console.log('Iniciando carga de productos...');
    dispatch(fetchProductos());
  }, [dispatch]);
  
  // Añadir diagnóstico para ver cuando cambian las tasas
  useEffect(() => {
    console.log('Tipo de tasa seleccionada:', tipoTasa);
    console.log('Tasa actual:', tasaCambio);
    console.log('Tasas disponibles:', latestTasas);
  }, [tipoTasa, tasaCambio, latestTasas]);

  // Cargar tasa de cambio cuando se selecciona un tipo
  useEffect(() => {
    if (tipoTasa) {
      // Siempre cargar la tasa cuando cambia el tipo
      dispatch(fetchLatestTasa(tipoTasa));
    }
  }, [dispatch, tipoTasa]);

  // Manejar cambio de moneda
  const handleMonedaChange = (nuevaMoneda) => {
    setMoneda(nuevaMoneda);
    if (nuevaMoneda === 'BS' || nuevaMoneda === 'USD') {
      setTipoTasa('BCV');
    } else {
      setTipoTasa('');
    }
    
    // Limpiar productos seleccionados al cambiar de moneda
    setProductosSeleccionados([]);
  };

  // Manejar cambio de tipo de tasa
  const handleTipoTasaChange = (nuevoTipoTasa) => {
    // Si es el mismo tipo, no hacer nada
    if (nuevoTipoTasa === tipoTasa) return;
    
    setTipoTasa(nuevoTipoTasa);
  };

  // Manejar selección de producto
  const handleProductoSelect = (producto) => {
    setDialogOpen(true);
    setProductoEditando({
      producto: producto,
      cantidad: cantidad,
      precio_compra_usd: producto.precio_compra_usd ? Number(producto.precio_compra_usd) : 0,
      unidades_paquete: producto.unidades_paquete ? Number(producto.unidades_paquete) : 1,
      porcentajeGanancia: porcentajeGanancia,
      aplicarIva: false
    });
    setEditingProductIndex(null);
  };

  // Manejar eliminación de producto
  const handleRemoveProducto = (index) => {
    setProductosSeleccionados(productosSeleccionados.filter((_, i) => i !== index));
  };

  // Manejar edición de producto
  const handleEditProducto = (index) => {
    const producto = productosSeleccionados[index];
    setProductoEditando({
      ...producto,
      precio_compra_usd: producto.precio_compra_usd ? Number(producto.precio_compra_usd) : 0,
      unidades_paquete: producto.unidades_paquete ? Number(producto.unidades_paquete) : 1,
      porcentajeGanancia: producto.porcentajeGanancia || porcentajeGanancia,
    });
    setEditingProductIndex(index);
    setDialogOpen(true);
  };

  // Cerrar diálogo de edición
  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingProductIndex(null);
  };

  // Mostrar mensaje de error o éxito
  const handleShowMessage = (message, severity = 'success') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  // Guardar la edición de un producto
  const handleSaveProductEdit = () => {
    // Asegurarnos de que los valores sean numéricos
    const precio_compra = Number(productoEditando.precio_compra_usd) || 0;
    const unidades = Number(productoEditando.unidades_paquete) || 1;
    const porcentaje = Number(productoEditando.porcentajeGanancia) || Number(porcentajeGanancia) || 0;
    const cantidad = Number(productoEditando.cantidad) || 1;
    
    if (precio_compra === 0 || unidades === 0) {
      handleShowMessage('Por favor ingrese el precio de compra y las unidades por paquete', 'error');
      return;
    }

    let precio_venta;
    let precio_base_usd;

    if (moneda === 'BS') {
      // Para BS: El precio_compra_usd realmente contiene el precio en bolívares
      // Calcular precio de venta en bolívares sin redondeo
      const precio_venta_bs_sin_redondeo = calcularPrecioVentaBs(
        precio_compra, // Precio en bolívares
        unidades,
        porcentaje,
        productoEditando.aplicarIva
      );
      
      // Calcular precio_base_usd dividiendo el precio de venta en BS por la tasa
      precio_base_usd = calcularPrecioBaseUSDDesdeBS(precio_venta_bs_sin_redondeo, tasaCambio?.valor || 1);
      
      // Aplicar redondeo especial al precio en BS
      precio_venta = aplicarRedondeoEspecial(precio_venta_bs_sin_redondeo);
    } else {
      // Para USD: Mantener la lógica existente
      precio_venta = calcularPrecioVenta(
        precio_compra,
        unidades,
        tasaCambio?.valor || 1,
        porcentaje,
        productoEditando.aplicarIva
      );

      // Calcular precio_base_usd para almacenar en el producto, incluyendo ganancia e IVA
      precio_base_usd = calcularPrecioBaseUSDConGanancia(
        precio_compra, 
        unidades, 
        porcentaje,
        productoEditando.aplicarIva
      );

      // Aplicar redondeo especial si la moneda es BS (esta condición nunca se cumplirá aquí, pero mantengo el código para claridad)
      if (moneda === 'BS' && tasaCambio) {
        precio_venta = aplicarRedondeoEspecial(precio_venta);
      }
    }

    const nuevoProducto = {
      producto: productoEditando.producto,
      cantidad: cantidad,
      precio_compra_usd: precio_compra,
      unidades_paquete: unidades,
      precio_unitario: precio_venta,
      total: precio_venta * cantidad,
      porcentajeGanancia: porcentaje,
      aplicarIva: productoEditando.aplicarIva,
      precio_base_usd: precio_base_usd,  // Nuevo campo
      tipo_tasa: tipoTasa                // Guardar el tipo de tasa usado
    };

    if (editingProductIndex !== null) {
      const updatedProductos = [...productosSeleccionados];
      updatedProductos[editingProductIndex] = nuevoProducto;
      setProductosSeleccionados(updatedProductos);
    } else {
      setProductosSeleccionados([...productosSeleccionados, nuevoProducto]);
    }
    
    setDialogOpen(false);
    setEditingProductIndex(null);
    setCantidad(1);
  };

  // Guardar la factura
  const handleSubmit = () => {
    // Función para asegurar que los valores tengan exactamente 2 decimales
    const asegurarDosDecimales = (valor) => {
      if (valor === null || valor === undefined || isNaN(valor)) return 0;
      // Convertir a número, luego a string con 2 decimales fijos, y volver a número
      return parseFloat(parseFloat(valor).toFixed(2));
    };
    
    // Si la moneda es USD, convertimos los precios a BS para Loyverse
    const facturaData = {
      moneda: moneda,
      tasa_cambio: tasaCambio?.id,
      porcentaje_ganancia: asegurarDosDecimales(porcentajeGanancia),
      detalles: productosSeleccionados.map(item => {
        // Calcular precio unitario y total en BS si es en USD
        const precio_unitario_calculado = moneda === 'USD' && tasaCambio 
          ? calcularPrecioBs(item.precio_unitario, tasaCambio.valor) 
          : aplicarRedondeoEspecial(item.precio_unitario);
        
        // Asegurar 2 decimales en todos los valores numéricos
        const precio_unitario = asegurarDosDecimales(precio_unitario_calculado);
        const cantidad = asegurarDosDecimales(item.cantidad);
        const total = asegurarDosDecimales(precio_unitario * cantidad);
        
        return {
          producto: item.producto.id,
          cantidad: cantidad,
          precio_unitario: precio_unitario,
          porcentaje_ganancia: asegurarDosDecimales(item.porcentajeGanancia || porcentajeGanancia),
          precio_compra_usd: asegurarDosDecimales(item.precio_compra_usd),
          unidades_paquete: asegurarDosDecimales(item.unidades_paquete),
          total: total,
          aplicarIva: item.aplicarIva || false,
          precio_base_usd: asegurarDosDecimales(item.precio_base_usd),  
          tipo_tasa: item.tipo_tasa || tipoTasa   
        };
      })
    };

    console.log('Enviando datos de factura:', facturaData); // Para depuración
    
    dispatch(createFactura(facturaData))
      .then(response => {
        if (response.error) {
          // Manejar errores de la API
          console.error('Error en respuesta:', response.error);
          
          let mensajeError = 'Error al crear la factura';
          
          // Verificar si hay detalles de error
          if (response.payload && response.payload.detalles_error) {
            const detallesError = response.payload.detalles_error;
            
            // Verificar errores específicos en los detalles de la factura
            if (detallesError.detalles && Array.isArray(detallesError.detalles)) {
              const mensajesError = [];
              
              detallesError.detalles.forEach((detalle, index) => {
                Object.entries(detalle).forEach(([campo, errores]) => {
                  if (Array.isArray(errores)) {
                    errores.forEach(error => {
                      mensajesError.push(`Producto ${index + 1}, ${campo}: ${error}`);
                    });
                  }
                });
              });
              
              if (mensajesError.length > 0) {
                mensajeError = `Errores en los datos de la factura:\n${mensajesError.join('\n')}`;
              }
            } else if (response.payload.error) {
              mensajeError = response.payload.error;
            }
          } else if (response.payload && response.payload.error) {
            mensajeError = response.payload.error;
          }
          
          handleShowMessage(mensajeError, 'error');
          return;
        }
        
        // Mostrar mensaje de factura creada
        handleShowMessage('Factura creada correctamente');
        
        // Si está habilitada la opción de actualizar precios, procesamos la factura
        if (actualizarPrecios && response.payload && response.payload.id) {
          // Realizar la llamada al endpoint para procesar la factura usando axios
          axios.post(`${API_URL}/facturas/${response.payload.id}/procesar_factura/`)
            .then(res => {
              console.log('Procesamiento de factura:', res.data);
              
              // Construir mensaje detallado
              let mensajeExito = 'Factura procesada correctamente';
              
              if (res.data.detalle_precios && res.data.detalle_precios.productos_actualizados) {
                mensajeExito += `. ${res.data.detalle_precios.productos_actualizados} productos con precios actualizados`;
              }
              
              if (res.data.detalle_inventario && res.data.detalle_inventario.productos_actualizados) {
                mensajeExito += `, ${res.data.detalle_inventario.productos_actualizados} productos con inventario actualizado`;
              }
              
              // Mostrar mensaje de éxito
              handleShowMessage(mensajeExito);
              
              // Limpiar el formulario
              setProductosSeleccionados([]);
            })
            .catch(error => {
              console.error('Error al procesar factura:', error);
              // Mostrar mensaje de error
              handleShowMessage('Error al procesar factura: ' + (error.response?.data?.error || error.message), 'error');
            });
        } else {
          // Limpiar el formulario si no se van a actualizar precios
          setProductosSeleccionados([]);
        }
      })
      .catch(error => {
        console.error('Error al crear factura:', error);
        
        let mensajeError = 'Error al crear factura';
        
        // Intentar extraer mensaje de error detallado de la respuesta
        if (error.response && error.response.data) {
          if (error.response.data.error) {
            mensajeError = error.response.data.error;
          } else if (error.response.data.detalles_error) {
            const detallesError = error.response.data.detalles_error;
            const errores = [];
            
            // Extraer todos los mensajes de error
            const procesarErrores = (obj, prefijo = '') => {
              if (typeof obj === 'object' && obj !== null) {
                Object.entries(obj).forEach(([key, value]) => {
                  if (Array.isArray(value)) {
                    value.forEach(item => {
                      if (typeof item === 'string') {
                        errores.push(`${prefijo}${key}: ${item}`);
                      } else if (typeof item === 'object') {
                        procesarErrores(item, `${prefijo}${key} - `);
                      }
                    });
                  } else if (typeof value === 'object') {
                    procesarErrores(value, `${prefijo}${key} - `);
                  }
                });
              }
            };
            
            procesarErrores(detallesError);
            
            if (errores.length > 0) {
              mensajeError = `Errores en los datos:\n${errores.join('\n')}`;
            }
          }
        }
        
        handleShowMessage(mensajeError, 'error');
      });
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box sx={{ 
      maxWidth: 1200, 
      margin: '0 auto', 
      padding: 3, 
      backgroundColor: '#f8f9fa'
    }}>
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontSize: '2rem', 
          fontWeight: 600, 
          color: '#1e293b',
          mb: 4,
          borderBottom: '2px solid #e2e8f0',
          paddingBottom: 2
        }}
      >
        Nueva Factura
      </Typography>
      
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff',
          transition: 'all 0.3s ease'
        }}
      >
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <SeleccionMoneda
              moneda={moneda}
              onMonedaChange={handleMonedaChange}
            />
          </Grid>
          
          {(moneda === 'BS' || moneda === 'USD') && (
            <Grid item xs={12} md={4}>
              <SeleccionTasa
                tipoTasa={tipoTasa}
                onTipoTasaChange={handleTipoTasaChange}
                tasaCambio={tasaCambio}
                onTasaUpdated={(message) => handleShowMessage(message)}
                onError={(message) => handleShowMessage(message, 'error')}
              />
            </Grid>
          )}
          
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Porcentaje de Ganancia"
              type="number"
              value={porcentajeGanancia}
              onChange={(e) => setPorcentajeGanancia(Number(e.target.value))}
              inputProps={{ min: 0, max: 100, step: 1 }}
              helperText="Porcentaje global de ganancia"
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 1,
                  '& fieldset': {
                    borderColor: '#cbd5e1',
                  },
                  '&:hover fieldset': {
                    borderColor: '#94a3b8',
                  }
                }
              }}
            />
          </Grid>
        </Grid>
        
        <Box mt={3}>
          <FormControlLabel
            control={
              <Switch
                checked={actualizarPrecios}
                onChange={(e) => setActualizarPrecios(e.target.checked)}
                color="primary"
              />
            }
            label="Actualizar precios en Loyverse automáticamente"
            sx={{ color: '#4b5563' }}
          />
        </Box>
      </Paper>

      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff'
        }}
      >
        <BuscadorProductos
          productos={productos}
          onProductoSelect={handleProductoSelect}
          cantidad={cantidad}
          onCantidadChange={setCantidad}
        />
      </Paper>

      <TablaProductos
        productos={productosSeleccionados}
        onEdit={handleEditProducto}
        onRemove={handleRemoveProducto}
        moneda={moneda}
        tasaCambio={tasaCambio}
      />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={productosSeleccionados.length === 0 || !moneda || !tasaCambio}
          sx={{ 
            py: 1.5,
            px: 4,
            borderRadius: 1,
            textTransform: 'none',
            fontWeight: 600,
            boxShadow: 2,
            backgroundColor: '#3b82f6',
            '&:hover': {
              backgroundColor: '#2563eb'
            },
            '&.Mui-disabled': {
              backgroundColor: '#e2e8f0',
              color: '#94a3b8'
            }
          }}
        >
          {actualizarPrecios ? 'Guardar Factura y Actualizar Precios' : 'Guardar Factura'}
        </Button>
      </Box>
      
      {/* Diálogo para editar producto */}
      <DialogoEditarProducto
        open={dialogOpen}
        onClose={handleDialogClose}
        productoEditando={productoEditando}
        onChange={setProductoEditando}
        onSave={handleSaveProductEdit}
        tasaCambio={tasaCambio}
        moneda={moneda}
      />
      
      {/* Snackbar para feedback */}
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={6000} 
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbarSeverity}
          variant="filled"
          sx={{ 
            width: '100%',
            boxShadow: 3,
            borderRadius: 1
          }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NuevaFactura; 