import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Grid,
  FormControlLabel,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Snackbar,
  Alert,
  Checkbox,
  InputAdornment,
  IconButton,
  Tooltip,
  FormHelperText
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import CategoryIcon from '@mui/icons-material/Category';
import InventoryIcon from '@mui/icons-material/Inventory';
import MoneyIcon from '@mui/icons-material/Money';
import { fetchLatestTasa } from '../store/tasasCambioSlice';
import { aplicarRedondeoEspecial } from '../utils/calculosPrecios';
import axios from 'axios';

// Usar la configuración dinámica de API URL
const getApiUrl = () => {
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const API_URL = getApiUrl();

/**
 * Componente para crear un nuevo producto
 */
const CrearProducto = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { tasaBCV, tasaParalelo } = useSelector((state) => ({
    tasaBCV: state.tasasCambio.items.find(tasa => tasa.tipo === 'BCV'),
    tasaParalelo: state.tasasCambio.items.find(tasa => tasa.tipo === 'PARALELO')
  }));

  // Estado para el formulario de producto
  const [producto, setProducto] = useState({
    nombre: '',
    descripcion: '',
    categoria: '',
    precio_base_usd: '',
    precio_compra_usd: '',
    porcentaje_ganancia: 30.00,
    aplicar_iva: false,
    track_stock: true,
    tipo_tasa: 'PARALELO',
    es_precio_variable: false,
    unidades_paquete: 1
  });

  // Estado para las categorías disponibles
  const [categorias, setCategorias] = useState([]);
  const [nuevaCategoria, setNuevaCategoria] = useState('');
  const [mostrarCampoNuevaCategoria, setMostrarCampoNuevaCategoria] = useState(false);

  // Estado para el proceso de carga
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

  // Cargar tasas de cambio al iniciar
  useEffect(() => {
    if (!tasaBCV) {
      dispatch(fetchLatestTasa('BCV'));
    }
    if (!tasaParalelo) {
      dispatch(fetchLatestTasa('PARALELO'));
    }

    // Cargar categorías existentes
    const cargarCategorias = async () => {
      try {
        const response = await axios.get(`${API_URL}/productos/categorias/`);
        if (response.data) {
          setCategorias(response.data.filter(cat => cat !== null && cat !== ''));
        }
      } catch (error) {
        console.error('Error al cargar categorías:', error);
        setError('No se pudieron cargar las categorías existentes');
      }
    };

    cargarCategorias();
  }, [dispatch, tasaBCV, tasaParalelo]);

  // Función para manejar cambios en los campos del formulario
  const handleChange = (field, value) => {
    // Validaciones especiales para campos numéricos
    if (['precio_base_usd', 'precio_compra_usd', 'porcentaje_ganancia', 'unidades_paquete'].includes(field)) {
      // Convertir a string para trabajar con decimales
      const valueStr = value.toString();
      
      // Verificar que no tenga más de 2 decimales
      if (valueStr.includes('.')) {
        const [parteEntera, parteDecimal] = valueStr.split('.');
        
        // Si tiene más de 2 decimales, truncar
        if (parteDecimal && parteDecimal.length > 2) {
          const decimalTruncado = parteDecimal.substring(0, 2);
          value = parseFloat(`${parteEntera}.${decimalTruncado}`);
        }
      }
      
      // Validar que sea un número válido
      if (isNaN(value)) {
        value = '';
      }
      
      // Valores mínimos para ciertos campos
      if (field === 'unidades_paquete' && value <= 0) {
        value = 1;
      }
    }
    
    setProducto(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Calcular el precio en Bs
  const calcularPrecioBs = () => {
    if (!producto.precio_base_usd) return 0;
    
    const precioBaseUSD = parseFloat(producto.precio_base_usd);
    const tasa = producto.tipo_tasa === 'BCV' ? tasaBCV : tasaParalelo;
    
    if (!tasa || !tasa.valor) return 0;
    
    const precioBs = precioBaseUSD * tasa.valor;
    return aplicarRedondeoEspecial(precioBs);
  };

  // Calcular precio base USD a partir del porcentaje de ganancia
  const calcularPrecioBaseUSD = () => {
    if (!producto.precio_compra_usd) return 0;
    
    const precioCompraUSD = parseFloat(producto.precio_compra_usd);
    const porcentajeGanancia = parseFloat(producto.porcentaje_ganancia) || 0;
    const unidadesPaquete = parseFloat(producto.unidades_paquete) || 1;
    
    if (precioCompraUSD <= 0 || unidadesPaquete <= 0) return 0;
    
    // Cálculo: precio por unidad considerando el paquete
    const precioCompraUnidad = precioCompraUSD / unidadesPaquete;
    
    // Aplicar la ganancia
    let precioConGanancia = precioCompraUnidad * (1 + porcentajeGanancia / 100);
    
    // Si se aplica IVA (16%), añadirlo al precio después de la ganancia
    if (producto.aplicar_iva) {
      precioConGanancia = precioConGanancia * 1.16;
    }
    
    // Redondear a 2 decimales para evitar problemas con números flotantes
    return Math.round(precioConGanancia * 100) / 100;
  };

  // Actualizar precio_base_usd cuando cambian los valores relacionados
  useEffect(() => {
    if (producto.precio_compra_usd) {
      const nuevoPrecioBaseUSD = calcularPrecioBaseUSD();
      
      setProducto(prev => ({
        ...prev,
        precio_base_usd: nuevoPrecioBaseUSD.toString()
      }));
    }
  }, [producto.precio_compra_usd, producto.porcentaje_ganancia, producto.aplicar_iva, producto.unidades_paquete]);

  // Función para manejar el cambio en la categoría seleccionada
  const handleCategoriaChange = (event) => {
    const value = event.target.value;
    
    if (value === 'nueva') {
      setMostrarCampoNuevaCategoria(true);
      setProducto(prev => ({ ...prev, categoria: '' }));
    } else {
      setMostrarCampoNuevaCategoria(false);
      setProducto(prev => ({ ...prev, categoria: value }));
    }
  };

  // Función para agregar una nueva categoría
  const agregarNuevaCategoria = () => {
    if (nuevaCategoria.trim() === '') return;
    
    // Verificar si la categoría ya existe (ignorando mayúsculas/minúsculas)
    const categoriaExiste = categorias.some(
      cat => cat.toLowerCase() === nuevaCategoria.toLowerCase()
    );
    
    if (!categoriaExiste) {
      setCategorias([...categorias, nuevaCategoria]);
    }
    
    // Establecer la nueva categoría en el producto
    setProducto(prev => ({ ...prev, categoria: nuevaCategoria }));
    setMostrarCampoNuevaCategoria(false);
    setNuevaCategoria('');
  };

  // Función para guardar el producto
  const guardarProducto = async () => {
    // Validar campos obligatorios
    if (!producto.nombre) {
      setSnackbar({
        open: true,
        message: 'El nombre del producto es obligatorio',
        severity: 'error'
      });
      return;
    }

    if (!producto.precio_compra_usd) {
      setSnackbar({
        open: true,
        message: 'El precio de compra es obligatorio',
        severity: 'error'
      });
      return;
    }

    setCargando(true);
    setError(null);

    try {
      // Ajuste final de valores antes de enviar
      const productoFinal = {
        ...producto,
        precio_base_usd: parseFloat(producto.precio_base_usd) || 0,
        precio_compra_usd: parseFloat(producto.precio_compra_usd) || 0,
        porcentaje_ganancia: parseFloat(producto.porcentaje_ganancia) || 30,
        unidades_paquete: parseInt(producto.unidades_paquete) || 1,
        fuente_actualizacion: 'manual'
      };

      // Llamada al API para crear el producto
      const response = await axios.post(`${API_URL}/productos/crear/`, productoFinal);

      setSnackbar({
        open: true,
        message: 'Producto creado exitosamente',
        severity: 'success'
      });

      // Esperar 2 segundos y luego redirigir al listado de productos
      setTimeout(() => {
        navigate('/productos');
      }, 2000);
    } catch (error) {
      console.error('Error al crear el producto:', error);
      
      let mensajeError = 'Error al crear el producto';
      
      if (error.response) {
        if (error.response.data.detail) {
          mensajeError = error.response.data.detail;
        } else if (error.response.data.error) {
          mensajeError = error.response.data.error;
        }
      }
      
      setError(mensajeError);
      setSnackbar({
        open: true,
        message: mensajeError,
        severity: 'error'
      });
    } finally {
      setCargando(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton 
            color="primary" 
            onClick={() => navigate('/productos')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5" component="h1" sx={{ flexGrow: 1, fontWeight: 600 }}>
            <InventoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Crear Nuevo Producto
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={guardarProducto}
            disabled={cargando}
            sx={{ 
              minWidth: 150,
              borderRadius: 1.5
            }}
          >
            {cargando ? <CircularProgress size={24} /> : 'Guardar Producto'}
          </Button>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          {/* Sección de información básica */}
          <Grid item xs={12} md={7}>
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <LocalOfferIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Información Básica
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Nombre del Producto *"
                      value={producto.nombre}
                      onChange={(e) => handleChange('nombre', e.target.value)}
                      variant="outlined"
                      required
                      sx={{ mb: 2 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Descripción"
                      value={producto.descripcion}
                      onChange={(e) => handleChange('descripcion', e.target.value)}
                      variant="outlined"
                      multiline
                      rows={3}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Sección de categoría */}
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CategoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Categoría
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControl fullWidth variant="outlined" sx={{ mb: mostrarCampoNuevaCategoria ? 2 : 0 }}>
                      <InputLabel id="categoria-select-label">Categoría</InputLabel>
                      <Select
                        labelId="categoria-select-label"
                        id="categoria-select"
                        value={mostrarCampoNuevaCategoria ? 'nueva' : producto.categoria}
                        onChange={handleCategoriaChange}
                        label="Categoría"
                      >
                        <MenuItem value="">
                          <em>Sin categoría</em>
                        </MenuItem>
                        {categorias.map((cat) => (
                          <MenuItem key={cat} value={cat}>
                            {cat}
                          </MenuItem>
                        ))}
                        <MenuItem value="nueva">
                          <AddIcon fontSize="small" sx={{ mr: 1 }} />
                          Crear nueva categoría
                        </MenuItem>
                      </Select>
                    </FormControl>

                    {mostrarCampoNuevaCategoria && (
                      <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                        <TextField
                          fullWidth
                          label="Nueva Categoría"
                          value={nuevaCategoria}
                          onChange={(e) => setNuevaCategoria(e.target.value)}
                          variant="outlined"
                          size="small"
                        />
                        <Button
                          variant="outlined"
                          color="primary"
                          onClick={agregarNuevaCategoria}
                          disabled={!nuevaCategoria.trim()}
                        >
                          Agregar
                        </Button>
                      </Box>
                    )}
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Sección de inventario */}
            <Card variant="outlined" sx={{ mb: 3, borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <InventoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Inventario
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={producto.track_stock}
                          onChange={(e) => handleChange('track_stock', e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Seguimiento de inventario"
                    />
                    <FormHelperText>
                      Si está habilitado, el sistema llevará registro del stock disponible
                    </FormHelperText>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Unidades por Paquete"
                      type="number"
                      value={producto.unidades_paquete}
                      onChange={(e) => handleChange('unidades_paquete', e.target.value)}
                      variant="outlined"
                      InputProps={{
                        inputProps: { min: 1 }
                      }}
                      helperText="Unidades contenidas en un paquete"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Sección de precios */}
          <Grid item xs={12} md={5}>
            <Card variant="outlined" sx={{ borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <MoneyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Información de Precios
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Precio de Compra (USD) *"
                      type="number"
                      value={producto.precio_compra_usd}
                      onChange={(e) => handleChange('precio_compra_usd', e.target.value)}
                      variant="outlined"
                      required
                      InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        inputProps: { min: 0, step: 0.01 }
                      }}
                      sx={{ mb: 2 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Porcentaje de Ganancia (%)"
                      type="number"
                      value={producto.porcentaje_ganancia}
                      onChange={(e) => handleChange('porcentaje_ganancia', e.target.value)}
                      variant="outlined"
                      InputProps={{
                        endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        inputProps: { min: 0, step: 0.01 }
                      }}
                      sx={{ mb: 2 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={producto.aplicar_iva}
                          onChange={(e) => handleChange('aplicar_iva', e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Aplicar IVA (16%)"
                      sx={{ mb: 2 }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
                      <InputLabel id="tipo-tasa-label">Tipo de Tasa</InputLabel>
                      <Select
                        labelId="tipo-tasa-label"
                        id="tipo-tasa-select"
                        value={producto.tipo_tasa}
                        onChange={(e) => handleChange('tipo_tasa', e.target.value)}
                        label="Tipo de Tasa"
                      >
                        <MenuItem value="BCV">
                          BCV ({tasaBCV ? tasaBCV.valor : 'N/A'} Bs)
                        </MenuItem>
                        <MenuItem value="PARALELO">
                          Paralelo ({tasaParalelo ? tasaParalelo.valor : 'N/A'} Bs)
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Precio Base (USD)"
                      type="number"
                      value={producto.precio_base_usd}
                      onChange={(e) => handleChange('precio_base_usd', e.target.value)}
                      variant="outlined"
                      InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                        inputProps: { min: 0, step: 0.01 }
                      }}
                      sx={{ mb: 2 }}
                    />
                    <FormHelperText>
                      Calculado automáticamente a partir del precio de compra y el porcentaje de ganancia
                    </FormHelperText>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Precio en Bolívares"
                      value={calcularPrecioBs()}
                      variant="outlined"
                      InputProps={{
                        startAdornment: <InputAdornment position="start">Bs</InputAdornment>,
                        readOnly: true
                      }}
                      sx={{ mb: 2 }}
                    />
                    <FormHelperText>
                      Calculado usando la tasa {producto.tipo_tasa} actual
                    </FormHelperText>
                  </Grid>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={producto.es_precio_variable}
                          onChange={(e) => handleChange('es_precio_variable', e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Precio Variable"
                    />
                    <FormHelperText>
                      Si está habilitado, el precio se puede modificar al momento de la venta
                    </FormHelperText>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CrearProducto; 