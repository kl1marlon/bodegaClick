import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  InputAdornment,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Button,
  ButtonGroup,
  Menu,
  MenuItem,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
  FormControlLabel,
  Switch,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  Slider
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InventoryIcon from '@mui/icons-material/Inventory';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import InfoIcon from '@mui/icons-material/Info';
import UpdateIcon from '@mui/icons-material/Update';
import LoyaltyIcon from '@mui/icons-material/Loyalty';
import ReceiptIcon from '@mui/icons-material/Receipt';
import CalculateIcon from '@mui/icons-material/Calculate';
import SyncIcon from '@mui/icons-material/Sync';
import FilterListIcon from '@mui/icons-material/FilterList';
import { fetchProductos, syncFromLoyverse, updateProductoTipoTasa } from '../store/productosSlice';
import { fetchTasasCambio, fetchLatestTasa, createTasaCambio } from '../store/tasasCambioSlice';
import { aplicarRedondeoEspecial } from '../utils/calculosPrecios';

const ListadoProductos = () => {
  const dispatch = useDispatch();
  const { items: productos, status } = useSelector((state) => state.productos);
  const { items: tasasCambio } = useSelector((state) => state.tasasCambio);
  
  // Estados para paginación
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  
  // Estado para filtro de categoría
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState('');
  const [categorias, setCategorias] = useState([]);
  
  // INICIO: FILTRO TEMPORAL PARA MIGRACIÓN - PRODUCTOS SIN PRECIO BASE USD
  // Esto es para ayudar durante la migración de datos, eliminar después
  const [mostrarSinPrecioBaseUSD, setMostrarSinPrecioBaseUSD] = useState(false);
  // FIN: FILTRO TEMPORAL PARA MIGRACIÓN
  
  // Estado para tasas de cambio
  const [tasaBCV, setTasaBCV] = useState(null);
  const [tasaParalelo, setTasaParalelo] = useState(null);
  const [tasaSeleccionadaProducto, setTasaSeleccionadaProducto] = useState({});
  
  // Estado para diálogo informativo
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  
  // Estado para diálogo de estadísticas por categoría
  const [statsDialogOpen, setStatsDialogOpen] = useState(false);
  
  // Estado para sincronización
  const [sincronizando, setSincronizando] = useState(false);
  const [actualizarPrecios, setActualizarPrecios] = useState(true);
  
  // Estado para opciones de sincronización
  const [opcionesSincronizacion, setOpcionesSincronizacion] = useState({
    actualizar_precios: true,
    categorias: [],
    tipo_tasa: '',
    productos_ids: [],
    tamaño_lote: 20
  });
  
  // Estado para diálogo de selección de productos específicos
  const [productosSeleccionados, setProductosSeleccionados] = useState([]);
  
  // Estado para diálogo de opciones de sincronización
  const [syncOptionsDialogOpen, setSyncOptionsDialogOpen] = useState(false);
  
  // Estado para feedback
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // INICIO: CONTADOR TEMPORAL DE PRODUCTOS CON PRECIO BASE USD
  // Este contador es temporal y se usa durante la migración de datos
  // para rastrear cuántos productos tienen precio_base_usd configurado.
  // TODO: Eliminar esta sección una vez completada la migración
  const [contadorPrecioBaseUSD, setContadorPrecioBaseUSD] = useState({
    total: 0,
    conPrecioBaseUSD: 0,
    porcentaje: 0
  });
  
  useEffect(() => {
    if (productos.length > 0) {
      const total = productos.length;
      const conPrecioBaseUSD = productos.filter(p => 
        p.precio_base_usd && Number(p.precio_base_usd) > 0
      ).length;
      
      setContadorPrecioBaseUSD({
        total,
        conPrecioBaseUSD,
        porcentaje: Math.round((conPrecioBaseUSD / total) * 100)
      });
    }
  }, [productos]);
  // FIN: CONTADOR TEMPORAL DE PRODUCTOS CON PRECIO BASE USD
  
  // Cargar productos y tasas al montar el componente
  useEffect(() => {
    if (status !== 'succeeded') {
      dispatch(fetchProductos());
    }
    dispatch(fetchTasasCambio());
    dispatch(fetchLatestTasa('BCV')).then(action => {
      if (action.payload) {
        setTasaBCV(action.payload);
      }
    });
    dispatch(fetchLatestTasa('PARALELO')).then(action => {
      if (action.payload) {
        setTasaParalelo(action.payload);
      }
    });
  }, [dispatch, status]);
  
  // Extraer categorías únicas de los productos
  useEffect(() => {
    if (productos.length > 0) {
      const uniqueCategorias = ['', ...new Set(productos.map(producto => producto.categoria).filter(Boolean))];
      setCategorias(uniqueCategorias);
    }
  }, [productos]);
  
  // Inicializar tasas seleccionadas para cada producto
  useEffect(() => {
    if (productos.length > 0 && tasaParalelo) {
      const initialTasas = {};
      productos.forEach(producto => {
        initialTasas[producto.id] = producto.tipo_tasa || 'PARALELO';
      });
      setTasaSeleccionadaProducto(initialTasas);
    }
  }, [productos, tasaParalelo]);
  
  // Filtrar productos cuando cambia el término de búsqueda, la categoría o la lista de productos
  useEffect(() => {
    if (productos.length > 0) {
      let filtered = [...productos];
      
      // Filtrar por término de búsqueda
      if (searchTerm.trim() !== '') {
        filtered = filtered.filter(producto => 
          producto.nombre.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      
      // Filtrar por categoría
      if (categoriaSeleccionada !== '') {
        filtered = filtered.filter(producto => 
          producto.categoria === categoriaSeleccionada
        );
      }
      
      // INICIO: FILTRO TEMPORAL PARA PRODUCTOS SIN PRECIO BASE USD
      if (mostrarSinPrecioBaseUSD) {
        filtered = filtered.filter(producto => 
          !producto.precio_base_usd || Number(producto.precio_base_usd) <= 0
        );
      }
      // FIN: FILTRO TEMPORAL
      
      setProductosFiltrados(filtered);
      setPage(0); // Resetear a la primera página cuando cambia el filtro
    }
  }, [searchTerm, categoriaSeleccionada, productos, mostrarSinPrecioBaseUSD]);
  
  // Manejadores para la paginación
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Función para cambiar la tasa de un producto
  const cambiarTasaProducto = (productoId, tipoTasa) => {
    // Actualizar el estado local inmediatamente para una respuesta UI rápida
    setTasaSeleccionadaProducto({
      ...tasaSeleccionadaProducto,
      [productoId]: tipoTasa
    });
    
    // Enviar la actualización al backend
    dispatch(updateProductoTipoTasa({ productoId, tipoTasa }))
      .unwrap()
      .then(() => {
        setSnackbar({
          open: true,
          message: `Tipo de tasa actualizado a ${tipoTasa} correctamente`,
          severity: 'success'
        });
      })
      .catch((error) => {
        console.error("Error al actualizar el tipo de tasa:", error);
        setSnackbar({
          open: true,
          message: `Error al actualizar tipo de tasa: ${error.message}`,
          severity: 'error'
        });
        // Revertir el cambio en la UI si hay error
        setTasaSeleccionadaProducto({
          ...tasaSeleccionadaProducto,
          [productoId]: tasaSeleccionadaProducto[productoId] === 'BCV' ? 'PARALELO' : 'BCV'
        });
      });
  };
  
  // Manejar cambio de categoría
  const handleCategoriaChange = (event) => {
    setCategoriaSeleccionada(event.target.value);
  };
  
  // Resetear filtros
  const resetearFiltros = () => {
    setSearchTerm('');
    setCategoriaSeleccionada('');
    setMostrarSinPrecioBaseUSD(false);
  };
  
  // Función para calcular el precio en USD desde BS
  const calcularPrecioUSD = (precioBs, productoId) => {
    if (!precioBs) return 0;
    
    // Convertir a número
    precioBs = Number(precioBs);
    
    // Obtener la tasa seleccionada para este producto
    const tipoTasa = tasaSeleccionadaProducto[productoId] || 'PARALELO';
    const tasa = tipoTasa === 'BCV' ? tasaBCV : tasaParalelo;
    
    if (!tasa || tasa.valor <= 0) return 0;
    
    // Calcular y devolver con 2 decimales
    return Number((precioBs / tasa.valor).toFixed(2));
  };
  
  // Función para calcular el precio BS a partir del precio_base_usd y la tasa
  const calcularPrecioBS = (precioBaseUSD, productoId) => {
    if (!precioBaseUSD) return 0;
    
    // Convertir a número
    precioBaseUSD = Number(precioBaseUSD);
    
    // Obtener la tasa seleccionada para este producto
    const tipoTasa = tasaSeleccionadaProducto[productoId] || 'PARALELO';
    const tasa = tipoTasa === 'BCV' ? tasaBCV : tasaParalelo;
    
    if (!tasa || tasa.valor <= 0) return 0;
    
    // Calcular precio en bolívares
    const precioBs = precioBaseUSD * tasa.valor;
    
    // Aplicar el redondeo especial que se usa en las facturas
    return aplicarRedondeoEspecial(precioBs);
  };
  
  // Obtener el valor actual de la tasa según el tipo
  const obtenerValorTasa = (tipo) => {
    if (tipo === 'BCV' && tasaBCV) {
      return tasaBCV.valor;
    } else if (tipo === 'PARALELO' && tasaParalelo) {
      return tasaParalelo.valor;
    }
    return 'N/A';
  };
  
  // Función para abrir diálogo de opciones de sincronización
  const abrirSyncOptionsDialog = () => {
    setSyncOptionsDialogOpen(true);
  };
  
  // Función para cerrar diálogo de opciones de sincronización
  const cerrarSyncOptionsDialog = () => {
    setSyncOptionsDialogOpen(false);
  };
  
  // Función para manejar la sincronización desde Loyverse
  const handleSyncFromLoyverse = () => {
    // Primero abrir el diálogo de opciones en lugar de iniciar directamente
    abrirSyncOptionsDialog();
  };
  
  // Función para iniciar la sincronización con las opciones seleccionadas
  const iniciarSincronizacion = () => {
    setSincronizando(true);
    cerrarSyncOptionsDialog();
    
    console.log("Iniciando sincronización con opciones:", opcionesSincronizacion);
    
    dispatch(syncFromLoyverse(opcionesSincronizacion))
      .then((result) => {
        if (result.error) {
          console.error("Error en la sincronización:", result.error.message);
          setSnackbar({
            open: true,
            message: `Error al sincronizar: ${result.error.message}`,
            severity: 'error'
          });
        } else {
          console.log("Sincronización completada exitosamente:", result.payload);
          
          // Mostrar mensaje de éxito con los detalles recibidos
          setSnackbar({
            open: true,
            message: result.payload.message || 'Sincronización completada exitosamente',
            severity: 'success'
          });
          
          dispatch(fetchProductos()); // Refrescar la lista de productos
        }
      })
      .finally(() => {
        setSincronizando(false);
      });
  };
  
  // Manejar cambio en productos seleccionados
  const handleChangeProductosSeleccionados = (event) => {
    const value = event.target.value;
    setProductosSeleccionados(value);
    setOpcionesSincronizacion(prev => ({
      ...prev,
      productos_ids: value
    }));
  };
  
  // Manejar cambio en categorías seleccionadas (múltiples)
  const handleChangeCategoriasSincronizacion = (event) => {
    const value = event.target.value;
    setOpcionesSincronizacion(prev => ({
      ...prev,
      categorias: typeof value === 'string' ? value.split(',') : value
    }));
  };
  
  // Manejar cambio en opciones de sincronización
  const handleChangeOpcionesSincronizacion = (event) => {
    const { name, value, checked, type } = event.target;
    setOpcionesSincronizacion(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Abrir el diálogo informativo
  const abrirInfoDialog = () => {
    setInfoDialogOpen(true);
  };
  
  // Cerrar el diálogo informativo
  const cerrarInfoDialog = () => {
    setInfoDialogOpen(false);
  };
  
  // Abrir el diálogo de estadísticas por categoría
  const abrirStatsDialog = () => {
    setStatsDialogOpen(true);
  };
  
  // Cerrar el diálogo de estadísticas por categoría
  const cerrarStatsDialog = () => {
    setStatsDialogOpen(false);
  };
  
  // Obtener el ícono para la fuente de actualización
  const getFuenteActualizacionIcon = (fuente) => {
    switch (fuente) {
      case 'loyverse':
        return <LoyaltyIcon fontSize="small" sx={{ color: '#3b82f6' }} />;
      case 'factura':
        return <ReceiptIcon fontSize="small" sx={{ color: '#10b981' }} />;
      case 'calculado':
        return <CalculateIcon fontSize="small" sx={{ color: '#f59e0b' }} />;
      default:
        return <UpdateIcon fontSize="small" sx={{ color: '#6b7280' }} />;
    }
  };
  
  // Obtener el texto para la fuente de actualización
  const getFuenteActualizacionText = (fuente) => {
    switch (fuente) {
      case 'loyverse':
        return 'Loyverse API';
      case 'factura':
        return 'Factura';
      case 'calculado':
        return 'Cálculo automático';
      default:
        return 'Desconocida';
    }
  };
  
  // Formatear fecha
  const formatDate = (dateString) => {
    if (!dateString) return 'No disponible';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Productos para la página actual
  const productosEnPagina = productosFiltrados.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
  // Cerrar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };
  
  return (
    <Box sx={{ 
      maxWidth: 1200, 
      margin: '0 auto', 
      padding: 3, 
      backgroundColor: '#f8f9fa'
    }}>
      <Box sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        mb: 4,
        borderBottom: '2px solid #e2e8f0',
        paddingBottom: 2,
      }}>
        <Typography 
          variant="h4" 
          sx={{ 
            fontSize: '2rem', 
            fontWeight: 600, 
            color: '#1e293b',
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}
        >
          <InventoryIcon fontSize="large" />
          Inventario de Productos
          <Tooltip title="Información sobre tasas de cambio">
            <IconButton 
              onClick={abrirInfoDialog}
              size="small"
              sx={{ ml: 2 }}
            >
              <InfoIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Estadísticas por categoría">
            <IconButton 
              onClick={abrirStatsDialog}
              size="small"
            >
              <FilterListIcon />
            </IconButton>
          </Tooltip>
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SyncIcon />}
            onClick={handleSyncFromLoyverse}
            disabled={sincronizando}
            sx={{
              borderRadius: 2,
              px: 3,
              py: 1,
              textTransform: 'none',
              fontWeight: 600
            }}
          >
            {sincronizando ? 'Sincronizando...' : 'Sincronizar con Loyverse'}
            {sincronizando && <CircularProgress size={20} sx={{ ml: 1, color: 'white' }} />}
          </Button>
        </Box>
      </Box>
      
      {/* INICIO: CONTADOR TEMPORAL - Eliminar después de la migración */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 2, 
          mb: 3, 
          borderRadius: 2,
          border: '2px solid #ff9800',
          backgroundColor: '#fff8e1',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          right: 0, 
          backgroundColor: '#ff9800', 
          color: 'white',
          px: 2,
          py: 0.5,
          borderBottomLeftRadius: 8
        }}>
          <Typography variant="subtitle2">
            TEMPORAL - Para migración
          </Typography>
        </Box>
        
        <Typography variant="h6" sx={{ mb: 1, color: '#e65100', fontWeight: 'bold' }}>
          Progreso de Migración - Precios Base USD
        </Typography>
        
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="body1">
              <strong>Productos con precio base USD:</strong> {contadorPrecioBaseUSD.conPrecioBaseUSD} de {contadorPrecioBaseUSD.total} ({contadorPrecioBaseUSD.porcentaje}%)
            </Typography>
            <Typography variant="body1" color="error.main" sx={{ mt: 1 }}>
              <strong>Productos sin precio base USD:</strong> {contadorPrecioBaseUSD.total - contadorPrecioBaseUSD.conPrecioBaseUSD} ({100 - contadorPrecioBaseUSD.porcentaje}%)
            </Typography>
            <Button
              variant="contained"
              color="warning"
              size="small"
              onClick={() => setMostrarSinPrecioBaseUSD(!mostrarSinPrecioBaseUSD)}
              sx={{ 
                mt: 1, 
                textTransform: 'none',
                backgroundColor: mostrarSinPrecioBaseUSD ? '#f97316' : '#fb923c',
                '&:hover': {
                  backgroundColor: '#ea580c',
                },
                fontWeight: 600
              }}
            >
              {mostrarSinPrecioBaseUSD ? 'Quitar filtro sin precio USD' : 'Mostrar solo sin precio USD'}
            </Button>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <Box sx={{ 
                width: '100%', 
                bgcolor: '#ffcc80', 
                borderRadius: 1,
                height: 10,
                position: 'relative'
              }}>
                <Box sx={{ 
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  bgcolor: '#fb8c00',
                  height: '100%',
                  width: `${contadorPrecioBaseUSD.porcentaje}%`,
                  borderRadius: 1,
                  transition: 'width 0.5s'
                }} />
              </Box>
            </Box>
            {mostrarSinPrecioBaseUSD && (
              <Box sx={{ 
                mt: 2, 
                px: 2, 
                py: 1, 
                bgcolor: '#fee2e2', 
                borderRadius: 1,
                border: '1px solid #fecaca',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <Typography variant="body2" color="error.main" fontWeight={600}>
                  Mostrando solo productos sin precio base USD
                </Typography>
                <Chip 
                  label={productosFiltrados.length} 
                  size="small" 
                  color="error"
                  sx={{ 
                    fontWeight: 700,
                    ml: 1
                  }} 
                />
              </Box>
            )}
          </Grid>
        </Grid>
      </Paper>
      {/* FIN: CONTADOR TEMPORAL */}
      
      {/* Panel de estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Total Productos
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {productos.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Tasa BCV Actual
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {tasaBCV ? tasaBCV.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Tasa Paralelo Actual
              </Typography>
              <Typography variant="h3" component="div" color="secondary">
                {tasaParalelo ? tasaParalelo.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Resultados búsqueda
              </Typography>
              <Typography variant="h3" component="div" color={searchTerm || categoriaSeleccionada ? 'secondary' : 'primary'}>
                {productosFiltrados.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Buscador y Filtros */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff'
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={5}>
            <TextField
              fullWidth
              label="Buscar Productos"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Escribe el nombre del producto..."
              variant="outlined"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
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
          </Grid>
          <Grid item xs={12} md={5}>
            <FormControl fullWidth variant="outlined">
              <InputLabel id="categoria-select-label">Filtrar por Categoría</InputLabel>
              <Select
                labelId="categoria-select-label"
                id="categoria-select"
                value={categoriaSeleccionada}
                onChange={handleCategoriaChange}
                label="Filtrar por Categoría"
                startAdornment={
                  <InputAdornment position="start">
                    <FilterListIcon />
                  </InputAdornment>
                }
                sx={{
                  borderRadius: 1,
                  '& fieldset': {
                    borderColor: '#cbd5e1',
                  },
                  '&:hover fieldset': {
                    borderColor: '#94a3b8',
                  }
                }}
              >
                <MenuItem value="">Todas las categorías</MenuItem>
                {categorias.filter(cat => cat !== '').map((categoria) => (
                  <MenuItem key={categoria} value={categoria}>
                    {categoria}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              color="secondary"
              onClick={resetearFiltros}
              sx={{
                borderRadius: 1,
                height: '56px',
                textTransform: 'none',
                fontWeight: 600
              }}
            >
              Limpiar filtros
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabla de productos */}
      <Paper 
        elevation={3} 
        sx={{ 
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        {status === 'loading' || sincronizando ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <CircularProgress />
            {sincronizando && (
              <Typography variant="h6" sx={{ ml: 2, color: '#475569' }}>
                Sincronizando productos desde Loyverse...
              </Typography>
            )}
          </Box>
        ) : (
          <>
            {(categoriaSeleccionada || mostrarSinPrecioBaseUSD) && (
              <Box sx={{ 
                p: 2, 
                bgcolor: '#e0f2fe', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                borderBottom: '1px solid #bae6fd'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {mostrarSinPrecioBaseUSD && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <FilterListIcon color="error" />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#b91c1c', ml: 1 }}>
                        Filtrando: <span style={{ color: '#ef4444' }}>Solo productos sin precio base USD</span>
                      </Typography>
                      <Divider orientation="vertical" flexItem sx={{ mx: 2, height: 24 }} />
                    </Box>
                  )}
                  {categoriaSeleccionada && (
                    <>
                      <FilterListIcon color="primary" />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#0369a1' }}>
                        Categoría: <span style={{ color: '#0284c7' }}>{categoriaSeleccionada}</span>
                      </Typography>
                    </>
                  )}
                </Box>
                <Button
                  size="small"
                  variant="outlined"
                  color={mostrarSinPrecioBaseUSD ? "error" : "primary"}
                  onClick={resetearFiltros}
                  sx={{ 
                    borderRadius: 1,
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Quitar filtros
                </Button>
              </Box>
            )}
            <TableContainer sx={{ maxHeight: 'calc(100vh - 350px)' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Producto</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Código</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio USD</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio BS</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Tasa</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Categoría</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Stock</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Actualización</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {productosEnPagina.map((producto) => (
                    <TableRow 
                      key={producto.id}
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
                      <TableCell 
                        component="th" 
                        scope="row"
                        sx={{ 
                          color: '#334155', 
                          borderBottom: '1px solid #f1f5f9',
                          fontWeight: 500
                        }}
                      >
                        {producto.nombre}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.codigo || 'N/A'}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        ${producto.precio_base_usd ? Number(producto.precio_base_usd).toFixed(2) : '0.00'}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9', fontWeight: 500 }}
                      >
                        {calcularPrecioBS(producto.precio_base_usd, producto.id)} Bs
                      </TableCell>
                      <TableCell
                        align="center"
                        sx={{ borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip 
                          title="Esta tasa está guardada en el producto. Al cambiarla se actualizará en la base de datos."
                          arrow
                        >
                          <Button 
                            variant="outlined"
                            size="small"
                            color={tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'primary' : 'secondary'}
                            onClick={() => cambiarTasaProducto(
                              producto.id, 
                              tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'PARALELO' : 'BCV'
                            )}
                            startIcon={<CurrencyExchangeIcon />}
                            sx={{ 
                              borderRadius: '4px',
                              fontWeight: 500,
                              textTransform: 'none'
                            }}
                          >
                            {tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'BCV' : 'Paralelo'} {
                              tasaSeleccionadaProducto[producto.id] === 'BCV' 
                                ? (tasaBCV ? tasaBCV.valor : 'N/A') 
                                : (tasaParalelo ? tasaParalelo.valor : 'N/A')
                            } Bs
                          </Button>
                        </Tooltip>
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.categoria ? (
                          <Chip 
                            label={producto.categoria} 
                            size="small" 
                            onClick={() => setCategoriaSeleccionada(producto.categoria)}
                            sx={{ 
                              backgroundColor: '#e0f2fe',
                              color: '#0369a1',
                              fontWeight: 500,
                              cursor: 'pointer',
                              '&:hover': {
                                backgroundColor: '#bae6fd',
                              }
                            }} 
                          />
                        ) : 'Sin categoría'}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Chip 
                          label={producto.stock_actual || '0'} 
                          size="small"
                          color={producto.stock_actual > 10 ? 'success' : producto.stock_actual > 0 ? 'warning' : 'error'}
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip 
                          title={
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                Fuente: {getFuenteActualizacionText(producto.fuente_actualizacion)}
                              </Typography>
                              <Typography variant="body2">
                                Actualización precio: {formatDate(producto.ultima_actualizacion_precio)}
                              </Typography>
                            </Box>
                          } 
                          arrow
                        >
                          <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
                            {getFuenteActualizacionIcon(producto.fuente_actualizacion)}
                          </Box>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {productosEnPagina.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4, color: '#6b7280' }}>
                        {searchTerm 
                          ? 'No se encontraron productos con ese término de búsqueda' 
                          : 'No hay productos disponibles'}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            
            <Divider />
            
            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50, 100]}
              component="div"
              count={productosFiltrados.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage="Filas por página:"
              labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
              sx={{
                backgroundColor: '#f8fafc',
                borderTop: '1px solid #e2e8f0',
                '& .MuiToolbar-root': {
                  minHeight: '56px',
                },
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                  color: '#64748b',
                }
              }}
            />
          </>
        )}
      </Paper>
      
      {/* Diálogo informativo */}
      <Dialog
        open={infoDialogOpen}
        onClose={cerrarInfoDialog}
        maxWidth="md"
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CurrencyExchangeIcon color="primary" />
            <Typography variant="h6">Información sobre Tasas de Cambio</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Tasas de cambio actuales:
            </Typography>
            <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
              <Box>
                <Typography variant="body1" color="primary" sx={{ fontWeight: 500 }}>
                  BCV: {tasaBCV ? tasaBCV.valor : 'No disponible'} Bs/USD
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaBCV ? new Date(tasaBCV.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body1" color="secondary" sx={{ fontWeight: 500 }}>
                  Paralelo: {tasaParalelo ? tasaParalelo.valor : 'No disponible'} Bs/USD
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaParalelo ? new Date(tasaParalelo.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body1" gutterBottom>
              Los precios en USD son calculados a partir de los precios en Bolívares usando la tasa seleccionada para cada producto.
            </Typography>
            <Typography variant="body1" gutterBottom>
              Puede cambiar la tasa utilizada para cada producto haciendo clic en los botones "BCV" o "Paralelo" en la columna "Tasa".
            </Typography>
            <Typography variant="body1" gutterBottom sx={{ fontWeight: 500, color: '#0284c7' }}>
              ¡Importante! La tasa mostrada en cada producto ahora refleja el valor almacenado en la base de datos (tipo_tasa).
              Al cambiarla, se actualizará permanentemente para ese producto.
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Fuentes de actualización:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LoyaltyIcon sx={{ color: '#3b82f6' }} />
                <Typography variant="body1">
                  <strong>Loyverse API:</strong> Productos actualizados directamente desde la API de Loyverse.
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ReceiptIcon sx={{ color: '#10b981' }} />
                <Typography variant="body1">
                  <strong>Factura:</strong> Productos actualizados a través de la creación de facturas.
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CalculateIcon sx={{ color: '#f59e0b' }} />
                <Typography variant="body1">
                  <strong>Cálculo automático:</strong> Precios calculados automáticamente basados en porcentajes de ganancia.
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Sincronización con Loyverse:
            </Typography>
            <Typography variant="body1">
              Puede sincronizar manualmente los productos desde Loyverse haciendo clic en el botón "Sincronizar con Loyverse" en la parte superior de la página.
              Esto traerá la información más actualizada de productos, incluyendo nombres, precios y categorías.
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              La opción "Actualizar precios" permite decidir si desea actualizar los precios con los valores de Loyverse. El sistema verificará si hay facturas creadas en los últimos 2 días y, en caso afirmativo, no actualizará los precios para mantener los ajustes recientes.
            </Typography>
            <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontStyle: 'italic' }}>
              Nota: Al cambiar el tipo de tasa de un producto (BCV o Paralelo), este cambio se guardará en la base de datos y afectará los cálculos de precios en futuras facturas.
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarInfoDialog} color="primary" variant="contained">
            Entendido
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de estadísticas por categoría */}
      <Dialog
        open={statsDialogOpen}
        onClose={cerrarStatsDialog}
        maxWidth="md"
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon color="primary" />
            <Typography variant="h6">Estadísticas por Categoría</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Distribución de productos por categoría:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
              {[
                { categoria: 'Bebidas', cantidad: 23 },
                { categoria: 'Charcuteria', cantidad: 14 },
                { categoria: 'Chucheria', cantidad: 115 },
                { categoria: 'Cigarros', cantidad: 24 },
                { categoria: 'Coche', cantidad: 16 },
                { categoria: 'Comida', cantidad: 134 },
                { categoria: 'Farmacia', cantidad: 12 },
                { categoria: 'Helado', cantidad: 5 },
                { categoria: 'Higiene', cantidad: 62 },
                { categoria: 'Impresiones', cantidad: 4 },
                { categoria: 'Panaderia', cantidad: 10 },
                { categoria: 'Papeleria', cantidad: 23 },
                { categoria: 'Papelería', cantidad: 2 },
                { categoria: 'Varios', cantidad: 49 },
                { categoria: 'Vicio', cantidad: 4 }
              ].map((item) => (
                <Card 
                  key={item.categoria} 
                  sx={{ 
                    minWidth: 180, 
                    flexGrow: 1, 
                    bgcolor: '#f8fafc', 
                    border: '1px solid #e2e8f0',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: '#f1f5f9',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                    }
                  }}
                  onClick={() => {
                    setCategoriaSeleccionada(item.categoria);
                    cerrarStatsDialog();
                  }}
                >
                  <CardContent>
                    <Typography variant="h6" fontWeight={500} color="#0369a1">
                      {item.categoria}
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="#1e293b">
                      {item.cantidad} productos
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
            <Typography variant="body2" sx={{ mt: 3, color: 'text.secondary', fontStyle: 'italic' }}>
              Haz clic en una categoría para filtrar los productos por esa categoría.
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarStatsDialog} color="primary" variant="contained">
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de opciones de sincronización */}
      <Dialog
        open={syncOptionsDialogOpen}
        onClose={cerrarSyncOptionsDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SyncIcon color="primary" />
            <Typography variant="h6">Opciones de Sincronización con Loyverse</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Configurar sincronización:
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Selecciona las opciones para personalizar el proceso de sincronización de productos con Loyverse.
              </Typography>
            </Grid>
            
            {/* Actualizar precios */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={opcionesSincronizacion.actualizar_precios}
                    onChange={handleChangeOpcionesSincronizacion}
                    name="actualizar_precios"
                    color="primary"
                  />
                }
                label="Actualizar precios en Loyverse (usando precio_base_usd * tasa)"
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                Si está activado, se enviarán los precios calculados de BodegaClick hacia Loyverse.
              </Typography>
            </Grid>
            
            {/* Selección de categorías */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="categorias-select-label">Filtrar por Categorías</InputLabel>
                <Select
                  labelId="categorias-select-label"
                  id="categorias-select"
                  multiple
                  value={opcionesSincronizacion.categorias}
                  onChange={handleChangeCategoriasSincronizacion}
                  label="Filtrar por Categorías"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  <MenuItem value="">
                    <em>Todas las categorías</em>
                  </MenuItem>
                  {categorias.filter(cat => cat !== '').map((categoria) => (
                    <MenuItem key={categoria} value={categoria}>
                      {categoria}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>
                  Deja vacío para sincronizar todas las categorías
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Selección de tipo de tasa */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="tipo-tasa-select-label">Filtrar por Tipo de Tasa</InputLabel>
                <Select
                  labelId="tipo-tasa-select-label"
                  id="tipo-tasa-select"
                  value={opcionesSincronizacion.tipo_tasa}
                  onChange={handleChangeOpcionesSincronizacion}
                  name="tipo_tasa"
                  label="Filtrar por Tipo de Tasa"
                >
                  <MenuItem value="">Todas las tasas</MenuItem>
                  <MenuItem value="BCV">Solo productos con tasa BCV</MenuItem>
                  <MenuItem value="PARALELO">Solo productos con tasa Paralelo</MenuItem>
                </Select>
                <FormHelperText>
                  Al exportar precios, solo se procesarán productos con este tipo de tasa
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Selección de productos específicos para pruebas */}
            <Grid item xs={12}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="productos-select-label">Productos para prueba</InputLabel>
                <Select
                  labelId="productos-select-label"
                  id="productos-select"
                  multiple
                  value={productosSeleccionados}
                  onChange={handleChangeProductosSeleccionados}
                  label="Productos para prueba"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const producto = productos.find(p => p.id === value);
                        return (
                          <Chip 
                            key={value} 
                            label={producto ? producto.nombre : `ID: ${value}`} 
                            size="small" 
                          />
                        );
                      })}
                    </Box>
                  )}
                >
                  {productos
                    .filter(producto => producto.loyverse_id) // Solo productos con ID de Loyverse
                    .map((producto) => (
                      <MenuItem key={producto.id} value={producto.id}>
                        {producto.nombre} ({producto.tipo_tasa} - {producto.categoria || 'Sin categoría'})
                      </MenuItem>
                    ))}
                </Select>
                <FormHelperText>
                  Selecciona productos específicos para probar la sincronización (deja vacío para sincronizar según categorías)
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Tamaño de lote para exportación */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Tamaño de lote para exportación
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Slider
                  value={opcionesSincronizacion.tamaño_lote}
                  onChange={(event, newValue) => {
                    setOpcionesSincronizacion(prev => ({
                      ...prev,
                      tamaño_lote: newValue
                    }));
                  }}
                  step={5}
                  marks={[
                    { value: 5, label: '5' },
                    { value: 20, label: '20' },
                    { value: 50, label: '50' },
                    { value: 100, label: '100' }
                  ]}
                  min={5}
                  max={100}
                  valueLabelDisplay="auto"
                  aria-labelledby="tamaño-lote-slider"
                />
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 100 }}>
                  {opcionesSincronizacion.tamaño_lote} productos por lote
                </Typography>
              </Box>
              <FormHelperText>
                Un valor menor es más lento pero más seguro. Útil para conexiones lentas o inestables.
              </FormHelperText>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ 
                bgcolor: '#f1f9ff', 
                p: 2, 
                borderRadius: 1, 
                border: '1px solid #e0f2fe',
                mt: 2 
              }}>
                <Typography variant="body2" color="info.main">
                  <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  <strong>Importante:</strong> La sincronización traerá todos los productos de Loyverse 
                  (sin sus precios) y podrá enviar los precios calculados en BodegaClick 
                  (precio_base_usd * tasa) hacia Loyverse dependiendo de la configuración seleccionada.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarSyncOptionsDialog} color="inherit">
            Cancelar
          </Button>
          <Button 
            onClick={iniciarSincronizacion} 
            color="primary" 
            variant="contained"
            disabled={sincronizando}
            startIcon={sincronizando ? <CircularProgress size={20} /> : <SyncIcon />}
          >
            {sincronizando ? 'Sincronizando...' : 'Iniciar Sincronización'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity} 
          sx={{ 
            width: '100%',
            maxWidth: '600px'
          }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ListadoProductos; 