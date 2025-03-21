import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  Tooltip
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import EditAttributesIcon from '@mui/icons-material/EditAttributes';
import { fetchProductos } from '../store/productosSlice';
import { fetchLatestTasa, createTasaCambio } from '../store/tasasCambioSlice';
import { createFactura } from '../store/facturasSlice';

// Usar la misma URL base que en el resto de la aplicación
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const NuevaFactura = () => {
  const dispatch = useDispatch();
  const productos = useSelector((state) => state.productos.items);
  const tasaCambio = useSelector((state) => state.tasasCambio.latestTasa);
  
  const [moneda, setMoneda] = useState('');
  const [tipoTasa, setTipoTasa] = useState('');
  const [productoSearch, setProductoSearch] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  const [productosSeleccionados, setProductosSeleccionados] = useState([]);
  const [cantidad, setCantidad] = useState(1);
  const [showResults, setShowResults] = useState(false);
  
  // Nuevos estados para manejo de porcentaje de ganancia
  const [porcentajeGanancia, setPorcentajeGanancia] = useState(30);
  const [actualizarPrecios, setActualizarPrecios] = useState(true);
  const [editingProductIndex, setEditingProductIndex] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [productoEditando, setProductoEditando] = useState({
    porcentajeGanancia: null,
    cantidad: 0,
    aplicarIva: false
  });
  
  // Estado para feedback al usuario
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  // Nuevos estados para editar tasas de cambio
  const [tasaDialogOpen, setTasaDialogOpen] = useState(false);
  const [nuevaTasaValor, setNuevaTasaValor] = useState('');

  useEffect(() => {
    console.log('Iniciando carga de productos...');
    dispatch(fetchProductos());
  }, [dispatch]);

  useEffect(() => {
    if (tipoTasa) {
      dispatch(fetchLatestTasa(tipoTasa));
    }
  }, [dispatch, tipoTasa]);

  // Filtrar productos basado en la búsqueda
  useEffect(() => {
    if (productoSearch.length > 0) {
      const searchTerm = productoSearch.toLowerCase();
      console.log('Término de búsqueda:', searchTerm);
      console.log('Productos disponibles:', productos);
      const filtrados = productos.filter(p =>
        p.nombre.toLowerCase().includes(searchTerm)
      ).slice(0, 10);
      console.log('Productos filtrados:', filtrados);
      setProductosFiltrados(filtrados);
      setShowResults(true);
    } else {
      setProductosFiltrados([]);
      setShowResults(false);
    }
  }, [productoSearch, productos]);

  const handleMonedaChange = (event) => {
    setMoneda(event.target.value);
    if (event.target.value === 'BS' || event.target.value === 'USD') {
      setTipoTasa('BCV');
    } else {
      setTipoTasa('');
    }
  };

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
  };

  const handleRemoveProducto = (index) => {
    setProductosSeleccionados(productosSeleccionados.filter((_, i) => i !== index));
  };

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

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingProductIndex(null);
  };

  // Nueva función para abrir el diálogo de edición de tasa
  const handleOpenTasaDialog = () => {
    setNuevaTasaValor(tasaCambio ? tasaCambio.valor : '');
    setTasaDialogOpen(true);
  };

  // Nueva función para cerrar el diálogo de edición de tasa
  const handleCloseTasaDialog = () => {
    setTasaDialogOpen(false);
  };

  // Nueva función para guardar la nueva tasa de cambio
  const handleSaveTasa = () => {
    if (!nuevaTasaValor || nuevaTasaValor <= 0) {
      setSnackbarMessage('Por favor ingrese un valor válido para la tasa de cambio');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }

    const tasaData = {
      tipo: tipoTasa,
      valor: parseFloat(nuevaTasaValor),
      fecha: new Date().toISOString().split('T')[0]
    };

    dispatch(createTasaCambio(tasaData))
      .then(response => {
        setSnackbarMessage(`Tasa de cambio ${tipoTasa} actualizada correctamente`);
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
        dispatch(fetchLatestTasa(tipoTasa));
        setTasaDialogOpen(false);
      })
      .catch(error => {
        setSnackbarMessage('Error al actualizar la tasa de cambio: ' + (error.response?.data?.error || error.message));
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      });
  };

  const calcularPrecioVenta = (precio_compra_usd, unidades_paquete, tasa_cambio_valor, porcentaje, aplicarIva = false) => {
    console.log('Calculando precio venta con:', { 
      precio_compra_usd, 
      unidades_paquete, 
      tasa_cambio_valor, 
      porcentaje, 
      aplicarIva 
    });
    
    // Convertir a números para evitar errores
    precio_compra_usd = Number(precio_compra_usd) || 0;
    unidades_paquete = Number(unidades_paquete) || 1;
    tasa_cambio_valor = Number(tasa_cambio_valor) || 1;
    porcentaje = Number(porcentaje) || 0;
    
    if (precio_compra_usd === 0) {
      console.log('Precio de compra USD no válido');
      return 0;
    }
    
    if (unidades_paquete === 0) {
      console.log('Unidades por paquete no válidas');
      return 0;
    }
    
    if (tasa_cambio_valor === 0) {
      console.log('Tasa de cambio no válida');
      return 0;
    }
    
    // Aplicar la fórmula: (precio_compra × tasa_dolar_paralelo / unidades) × (1 + porcentaje_ganancia/100)
    const precio_base = precio_compra_usd / unidades_paquete;
    const precio_con_ganancia = precio_base * (1 + (porcentaje / 100));
    
    // Aplicar IVA si está activado
    const precio_final = aplicarIva ? precio_con_ganancia * 1.16 : precio_con_ganancia;
    
    // Redondear a 2 decimales para evitar problemas de precisión
    const precio_redondeado = parseFloat(precio_final.toFixed(2));
    console.log('Precio final calculado:', precio_redondeado);
    return precio_redondeado;
  };

  // Función para aplicar reglas de redondeo especiales a precios en bolívares
  const aplicarRedondeoEspecial = (precioBs) => {
    // Asegurarse de que sea un número
    precioBs = Number(precioBs) || 0;
    
    // Primero redondeamos a 2 decimales para evitar problemas de precisión
    precioBs = Math.round(precioBs * 100) / 100;
    
    if (precioBs < 10) {
      // Para precios menores a 10, revisar la última cifra
      const ultimaCifra = Math.floor(precioBs) % 10;
      if (ultimaCifra === 4 || ultimaCifra === 6 || ultimaCifra === 9) {
        // Redondear hacia arriba al siguiente entero
        return Math.ceil(precioBs);
      }
      // Si no es terminación prohibida, solo dejamos el valor como está
      return precioBs;
    } else {
      // Para precios mayores o iguales a 10
      const entero = Math.floor(precioBs);
      const ultimaCifra = entero % 10;
      const decimal = precioBs - entero;
      
      // Si tiene algún decimal, necesitamos aplicar reglas de redondeo
      if (decimal > 0) {
        // Si termina en 0-4, redondear al 5 más cercano
        if (ultimaCifra < 5) {
          return entero - ultimaCifra + 5;
        } 
        // Si termina en 5-9, redondear al próximo múltiplo de 10
        else {
          return entero - ultimaCifra + 10;
        }
      }
      
      // Si no tiene decimales:
      // Para terminaciones 1, 2, 3, 4, redondear al 5
      if (ultimaCifra >= 1 && ultimaCifra <= 4) {
        return entero - ultimaCifra + 5;
      }
      
      // Para terminaciones 6, 7, 8, 9, redondear al próximo 0
      if (ultimaCifra >= 6 && ultimaCifra <= 9) {
        return entero - ultimaCifra + 10;
      }
      
      // Si llegamos aquí, el valor ya termina en 0 o 5 sin decimales
      return entero;
    }
  };

  // Función auxiliar para calcular el precio en bolívares cuando el precio está en USD
  const calcularPrecioBs = (precio_usd) => {
    precio_usd = Number(precio_usd) || 0;
    if (!tasaCambio || precio_usd === 0) return 0;
    
    const tasa_valor = Number(tasaCambio.valor) || 1;
    const precioBs = precio_usd * tasa_valor;
    return aplicarRedondeoEspecial(precioBs);
  };

  // Función para calcular el precio directamente en bolívares según corresponda
  const calcularPrecioDirectoEnBs = (precio_compra_usd, unidades_paquete, porcentaje, aplicarIva) => {
    // Convertir a números para evitar errores
    precio_compra_usd = Number(precio_compra_usd) || 0;
    unidades_paquete = Number(unidades_paquete) || 1;
    porcentaje = Number(porcentaje) || 0;
    
    if (precio_compra_usd === 0 || unidades_paquete === 0 || !tasaCambio) return 0;
    
    const tasa_valor = Number(tasaCambio.valor) || 1;
    
    // Aplicar la fórmula: (precio_compra / unidades) × (1 + porcentaje_ganancia/100)
    const precio_base = precio_compra_usd / unidades_paquete;
    const precio_con_ganancia = precio_base * (1 + (porcentaje / 100));
    
    // Aplicar IVA si está activado
    const precio_final = aplicarIva ? precio_con_ganancia * 1.16 : precio_con_ganancia;
    
    // Multiplicar por la tasa para obtener el precio en bolívares
    const precio_en_bs = precio_final * tasa_valor;
    
    // Aplicar reglas de redondeo especiales
    return aplicarRedondeoEspecial(precio_en_bs);
  };

  // Función para mostrar el precio en bolívares según corresponda
  const mostrarPrecioEnBs = (precio_usd, precio_compra_usd, unidades_paquete, porcentaje, aplicarIva) => {
    // Si estamos en modo bolívares, no hacemos la conversión
    if (moneda === 'BS') return null;
    
    // Si es un precio ya calculado (en la tabla), solo multiplicamos por la tasa
    if (precio_usd && !precio_compra_usd) {
      return calcularPrecioBs(precio_usd);
    }
    
    // Si es en el diálogo de edición, calculamos el precio directo en bolívares
    return calcularPrecioDirectoEnBs(precio_compra_usd, unidades_paquete, porcentaje, aplicarIva);
  };

  const handleSaveProductEdit = () => {
    // Asegurarnos de que los valores sean numéricos
    const precio_compra = Number(productoEditando.precio_compra_usd) || 0;
    const unidades = Number(productoEditando.unidades_paquete) || 1;
    const porcentaje = Number(productoEditando.porcentajeGanancia) || Number(porcentajeGanancia) || 0;
    const cantidad = Number(productoEditando.cantidad) || 1;
    
    if (precio_compra === 0 || unidades === 0) {
      setSnackbarMessage('Por favor ingrese el precio de compra y las unidades por paquete');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }

    let precio_venta = calcularPrecioVenta(
      precio_compra,
      unidades,
      tasaCambio?.valor || 1,
      porcentaje,
      productoEditando.aplicarIva
    );

    // Aplicar redondeo especial si la moneda es BS
    if (moneda === 'BS' && tasaCambio) {
      precio_venta = aplicarRedondeoEspecial(precio_venta);
    }

    const nuevoProducto = {
      producto: productoEditando.producto,
      cantidad: cantidad,
      precio_compra_usd: precio_compra,
      unidades_paquete: unidades,
      precio_unitario: precio_venta,
      total: precio_venta * cantidad,
      porcentajeGanancia: porcentaje,
      aplicarIva: productoEditando.aplicarIva
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
    setProductoSearch('');
    setCantidad(1);
  };

  const calcularTotal = () => {
    return productosSeleccionados.reduce((sum, item) => sum + item.total, 0);
  };

  const handleSubmit = () => {
    // Si la moneda es USD, convertimos los precios a BS para Loyverse
    const facturaData = {
      moneda: moneda,
      tasa_cambio: tasaCambio?.id,
      porcentaje_ganancia: porcentajeGanancia,
      detalles: productosSeleccionados.map(item => {
        // Calcular precio unitario y total en BS si es en USD
        const precio_unitario = moneda === 'USD' && tasaCambio 
          ? calcularPrecioBs(item.precio_unitario) 
          : aplicarRedondeoEspecial(item.precio_unitario);
        
        const total = precio_unitario * item.cantidad;
        
        return {
          producto: item.producto.id,
          cantidad: item.cantidad,
          precio_unitario: precio_unitario,
          porcentaje_ganancia: item.porcentajeGanancia || porcentajeGanancia,
          precio_compra_usd: item.precio_compra_usd ? parseFloat(Number(item.precio_compra_usd).toFixed(2)) : 0,
          unidades_paquete: item.unidades_paquete,
          total: total,
          aplicarIva: item.aplicarIva || false
        };
      })
    };

    console.log('Enviando datos de factura:', facturaData); // Para depuración
    
    dispatch(createFactura(facturaData))
      .then(response => {
        // Mostrar mensaje de factura creada
        setSnackbarMessage('Factura creada correctamente');
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
        
        // Si está habilitada la opción de actualizar precios, procesamos la factura
        if (actualizarPrecios && response.payload && response.payload.id) {
          // Realizar la llamada al endpoint para procesar la factura usando axios
          axios.post(`${API_URL}/facturas/${response.payload.id}/procesar_factura/`)
            .then(res => {
              console.log('Precios actualizados:', res.data);
              // Mostrar mensaje de éxito
              setSnackbarMessage('Precios actualizados en Loyverse correctamente');
              setSnackbarSeverity('success');
              setSnackbarOpen(true);
              
              // Limpiar el formulario
              setProductosSeleccionados([]);
            })
            .catch(error => {
              console.error('Error al actualizar precios:', error);
              // Mostrar mensaje de error
              setSnackbarMessage('Error al actualizar precios: ' + (error.response?.data?.error || error.message));
              setSnackbarSeverity('error');
              setSnackbarOpen(true);
            });
        } else {
          // Limpiar el formulario si no se van a actualizar precios
          setProductosSeleccionados([]);
        }
      })
      .catch(error => {
        console.error('Error al crear factura:', error);
        setSnackbarMessage('Error al crear factura: ' + (error.response?.data?.error || error.message));
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
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
          </Grid>
          
          {(moneda === 'BS' || moneda === 'USD') && (
            <Grid item xs={12} md={4}>
              <Box display="flex" alignItems="center">
                <FormControl fullWidth variant="outlined">
                  <InputLabel>Tipo de Tasa</InputLabel>
                  <Select 
                    value={tipoTasa} 
                    onChange={(e) => setTipoTasa(e.target.value)}
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
                  Tasa actual: {tipoTasa} = {tasaCambio.valor} Bs/USD (última actualización: {new Date(tasaCambio.fecha).toLocaleDateString()})
                </Typography>
              )}
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
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Buscar Producto"
              value={productoSearch}
              onChange={(e) => setProductoSearch(e.target.value)}
              placeholder="Escribe para buscar productos..."
              variant="outlined"
              InputProps={{
                sx: {
                  borderRadius: 1
                }
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: '#cbd5e1',
                  },
                  '&:hover fieldset': {
                    borderColor: '#94a3b8',
                  }
                }
              }}
            />
            {showResults && productosFiltrados.length > 0 && (
              <Paper 
                elevation={5}
                sx={{ 
                  mt: 1, 
                  maxHeight: 300, 
                  overflow: 'auto',
                  position: 'absolute',
                  zIndex: 1000,
                  width: '63%',
                  borderRadius: 1
                }}
              >
                <List sx={{ padding: 0 }}>
                  {productosFiltrados.map(producto => (
                    <ListItem 
                      key={producto.id} 
                      button 
                      onClick={() => handleProductoSelect(producto)}
                      sx={{
                        borderBottom: '1px solid #f1f5f9',
                        '&:hover': {
                          backgroundColor: '#f8fafc',
                        },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      <ListItemText
                        primary={
                          <Typography sx={{ fontWeight: 500, color: '#1e293b' }}>
                            {producto.nombre}
                          </Typography>
                        }
                        secondary={
                          <Typography sx={{ color: '#64748b' }}>
                            Precio: ${Number(producto.precio_base).toFixed(2)}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Cantidad"
              value={cantidad}
              onChange={(e) => setCantidad(Number(e.target.value))}
              inputProps={{ min: 1 }}
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
      </Paper>

      <TableContainer 
        component={Paper} 
        elevation={3}
        sx={{ 
          borderRadius: 2,
          overflow: 'hidden',
          mb: 3
        }}
      >
        <Table>
          <TableHead sx={{ backgroundColor: '#f1f5f9' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Producto</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Cantidad</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Precio Unitario</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Total</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>% Ganancia</TableCell>
              <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>IVA</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {productosSeleccionados.map((item, index) => (
              <TableRow 
                key={index} 
                sx={{
                  '&:hover': {
                    backgroundColor: '#f8fafc',
                  },
                  '&:nth-of-type(even)': {
                    backgroundColor: '#f9fafb',
                  },
                  transition: 'background-color 0.2s'
                }}
              >
                <TableCell sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>{item.producto.nombre}</TableCell>
                <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>{item.cantidad}</TableCell>
                <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                  {moneda === 'BS' ? 
                    `${aplicarRedondeoEspecial(item.precio_unitario).toFixed(2)} ${moneda}` : 
                    `${calcularPrecioBs(item.precio_unitario).toFixed(2)} BS`
                  }
                </TableCell>
                <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                  {moneda === 'BS' ? 
                    `${aplicarRedondeoEspecial(item.total).toFixed(2)} ${moneda}` : 
                    `${calcularPrecioBs(item.total).toFixed(2)} BS`
                  }
                </TableCell>
                <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                  {item.porcentajeGanancia !== null ? `${item.porcentajeGanancia}%` : `${porcentajeGanancia}% (global)`}
                </TableCell>
                <TableCell align="center" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                  {item.aplicarIva ? 
                    <Typography sx={{ color: '#059669' }}>Sí (16%)</Typography> : 
                    <Typography sx={{ color: '#6b7280' }}>No</Typography>
                  }
                </TableCell>
                <TableCell align="right" sx={{ borderBottom: '1px solid #f1f5f9' }}>
                  <IconButton 
                    onClick={() => handleEditProducto(index)} 
                    size="small"
                    sx={{ 
                      color: '#3b82f6',
                      backgroundColor: '#eff6ff',
                      mr: 1,
                      '&:hover': {
                        backgroundColor: '#dbeafe'
                      }
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton 
                    onClick={() => handleRemoveProducto(index)} 
                    size="small"
                    sx={{ 
                      color: '#ef4444',
                      backgroundColor: '#fef2f2',
                      '&:hover': {
                        backgroundColor: '#fee2e2'
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {productosSeleccionados.length > 0 && (
              <TableRow sx={{ backgroundColor: '#f1f5f9' }}>
                <TableCell colSpan={3} align="right" sx={{ fontWeight: 700, color: '#1e293b', py: 2 }}>
                  Total:
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, color: '#1e293b', py: 2 }}>
                  {moneda === 'BS' ? 
                    `${aplicarRedondeoEspecial(calcularTotal()).toFixed(2)} ${moneda}` : 
                    `${calcularPrecioBs(calcularTotal()).toFixed(2)} BS`
                  }
                </TableCell>
                <TableCell colSpan={3} />
              </TableRow>
            )}
            {productosSeleccionados.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4, color: '#6b7280' }}>
                  No hay productos en la factura. Busque y agregue productos usando el formulario superior.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

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
      <Dialog 
        open={dialogOpen} 
        onClose={handleDialogClose}
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
            {productoEditando.producto ? productoEditando.producto.nombre : 'Editar Producto'}
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          <Grid container spacing={3} sx={{ mt: 0 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Precio de Compra (USD)"
                type="number"
                value={productoEditando.precio_compra_usd}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  precio_compra_usd: Number(e.target.value)
                })}
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
                value={productoEditando.unidades_paquete}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  unidades_paquete: Number(e.target.value)
                })}
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
                value={productoEditando.cantidad}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  cantidad: Number(e.target.value)
                })}
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
                value={productoEditando.porcentajeGanancia}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  porcentajeGanancia: Number(e.target.value)
                })}
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
                    checked={productoEditando.aplicarIva || false}
                    onChange={(e) => setProductoEditando({
                      ...productoEditando,
                      aplicarIva: e.target.checked
                    })}
                    color="primary"
                  />
                }
                label="Aplicar IVA (16%)"
                sx={{ color: '#4b5563' }}
              />
            </Grid>
            {tasaCambio && (
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
                  <Typography sx={{ fontSize: '0.875rem', color: '#334155', fontWeight: 500 }}>
                    Precio de venta calculado: 
                    <Box component="span" sx={{ fontWeight: 600, color: '#0f766e', ml: 1 }}>
                      {moneda === 'BS' ? 
                        `BS ${aplicarRedondeoEspecial(calcularPrecioVenta(
                          productoEditando.precio_compra_usd,
                          productoEditando.unidades_paquete,
                          tasaCambio.valor,
                          productoEditando.porcentajeGanancia,
                          productoEditando.aplicarIva
                        )).toFixed(2)}` : 
                        `BS ${calcularPrecioDirectoEnBs(
                          productoEditando.precio_compra_usd,
                          productoEditando.unidades_paquete,
                          productoEditando.porcentajeGanancia,
                          productoEditando.aplicarIva
                        ).toFixed(2)}`
                      }
                      {productoEditando.aplicarIva && ' (incluye IVA 16%)'}
                    </Box>
                  </Typography>
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
            onClick={handleDialogClose} 
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
            onClick={handleSaveProductEdit} 
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