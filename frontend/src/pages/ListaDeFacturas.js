import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { fetchFacturasOptimizado, fetchFacturaDetalleOptimizado, setPage, setPageSize } from '../store/facturasSlice';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Box,
  TablePagination,
  Chip,
  Grid,
  IconButton,
  TextField,
  InputAdornment,
  Alert,
  AlertTitle,
  Pagination,
  MenuItem,
  Collapse,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { startOfDay, endOfDay, startOfWeek, endOfWeek, startOfMonth, endOfMonth, format } from 'date-fns';
import { es } from 'date-fns/locale';
import moment from 'moment';
import 'moment/locale/es';

moment.locale('es');

const ListaDeFacturas = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const facturas = useSelector((state) => state.facturas.items || []);
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  const paginacion = useSelector((state) => state.facturas.paginacion);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [facturasFiltradas, setFacturasFiltradas] = useState([]);
  
  // Estado para filtros de fecha
  const [filtros, setFiltros] = useState({
    fechaDesde: null,
    fechaHasta: null
  });
  const [filtroRapido, setFiltroRapido] = useState(null);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  
  // Cargar facturas al montar el componente
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        console.log('Iniciando carga de facturas optimizada...');
        console.log('Parámetros de paginación:', { page: paginacion.page, pageSize: paginacion.pageSize });
        console.log('Filtros de fecha:', { fechaDesde: filtros.fechaDesde, fechaHasta: filtros.fechaHasta });
        
        // Preparamos los parámetros incluyendo los filtros de fecha
        const params = {
          page: paginacion.page,
          pageSize: paginacion.pageSize,
          fechaDesde: filtros.fechaDesde ? format(filtros.fechaDesde, 'yyyy-MM-dd') : null,
          fechaHasta: filtros.fechaHasta ? format(filtros.fechaHasta, 'yyyy-MM-dd') : null
        };
        
        console.log('Parámetros de la petición:', params);
        
        const resultado = await dispatch(fetchFacturasOptimizado(params)).unwrap();
        
        console.log('Facturas cargadas exitosamente (optimizado):', resultado);
        console.log('Datos en facturas:', resultado.results);
      } catch (error) {
        console.error("Error al cargar facturas (optimizado):", error);
      }
    };
    
    obtenerDatos();
  }, [dispatch, paginacion.page, paginacion.pageSize, filtros.fechaDesde, filtros.fechaHasta]);
  
  // Filtrar facturas cuando cambia el término de búsqueda o la lista de facturas
  useEffect(() => {
    console.log('Actualizando facturas filtradas. Facturas disponibles:', facturas);
    if (facturas && facturas.length > 0) {
      let filtered = [...facturas];
      
      // Filtrar por término de búsqueda
      if (searchTerm.trim() !== '') {
        filtered = filtered.filter(factura => 
          (factura.numero && factura.numero.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (factura.id && factura.id.toString().includes(searchTerm))
        );
      }
      
      setFacturasFiltradas(filtered);
      console.log('Facturas filtradas actualizadas:', filtered);
    } else {
      setFacturasFiltradas([]);
      console.log('No hay facturas disponibles para filtrar');
    }
  }, [searchTerm, facturas]);
  
  // Función para cambiar de página
  const handlePageChange = (event, newPage) => {
    dispatch(setPage(newPage));
  };
  
  // Función para cambiar el tamaño de página
  const handlePageSizeChange = (event) => {
    dispatch(setPageSize(parseInt(event.target.value, 10)));
    dispatch(setPage(1)); // Resetear a la primera página
  };
  
  // Manejadores de cambio de fechas
  const handleFechaDesdeChange = (newValue) => {
    setFiltros(prev => ({
      ...prev,
      fechaDesde: newValue
    }));
    // Al cambiar fecha manualmente, quitamos el filtro rápido seleccionado
    setFiltroRapido(null);
  };

  const handleFechaHastaChange = (newValue) => {
    setFiltros(prev => ({
      ...prev,
      fechaHasta: newValue
    }));
    // Al cambiar fecha manualmente, quitamos el filtro rápido seleccionado
    setFiltroRapido(null);
  };
  
  // Manejador de filtros rápidos
  const handleFiltroRapido = (event, newValue) => {
    if (!newValue) {
      return; // Si se deselecciona, no hacemos nada
    }
    
    const fechaActual = new Date();
    let desde, hasta;
    
    if (newValue === 'hoy') {
      desde = startOfDay(fechaActual);
      hasta = endOfDay(fechaActual);
    } else if (newValue === 'semana') {
      desde = startOfWeek(fechaActual, { locale: es });
      hasta = endOfWeek(fechaActual, { locale: es });
    } else if (newValue === 'mes') {
      desde = startOfMonth(fechaActual);
      hasta = endOfMonth(fechaActual);
    }
    
    setFiltroRapido(newValue);
    setFiltros({
      fechaDesde: desde,
      fechaHasta: hasta
    });
  };
  
  // Función para aplicar filtros
  const aplicarFiltros = () => {
    // La recarga se hará automáticamente gracias a las dependencias del useEffect
    // que detectará cambios en fechaDesde y fechaHasta
  };
  
  // Función para resetear filtros
  const resetearFiltros = () => {
    setFiltros({
      fechaDesde: null,
      fechaHasta: null
    });
    setFiltroRapido(null);
  };
  
  // Función para recargar facturas
  const recargarFacturas = () => {
    // Preparamos los parámetros incluyendo los filtros de fecha
    const params = {
      page: paginacion.page,
      pageSize: paginacion.pageSize,
      fechaDesde: filtros.fechaDesde ? format(filtros.fechaDesde, 'yyyy-MM-dd') : null,
      fechaHasta: filtros.fechaHasta ? format(filtros.fechaHasta, 'yyyy-MM-dd') : null
    };
    
    dispatch(fetchFacturasOptimizado(params))
      .unwrap()
      .then(() => {
        console.log('Facturas recargadas exitosamente (optimizado)');
      })
      .catch(error => {
        console.error('Error al recargar facturas (optimizado):', error);
      });
  };
  
  // Función para ver el detalle de una factura
  const verDetalleFactura = (facturaId) => {
    navigate(`/facturas/${facturaId}`);
  };
  
  // Renderizado condicional según el estado
  if (status === 'loading' && !facturas.length) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Cargando facturas...
          </Typography>
        </Box>
      </Container>
    );
  }
  
  if (status === 'failed') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert 
          severity="error" 
          variant="filled"
          sx={{ mb: 3 }}
        >
          <AlertTitle>Error al cargar las facturas</AlertTitle>
          {error || 'Ocurrió un error desconocido'}
        </Alert>
        
        <Button
          startIcon={<RefreshIcon />}
          variant="contained"
          color="primary"
          onClick={recargarFacturas}
          sx={{ mt: 2 }}
        >
          Reintentar
        </Button>
      </Container>
    );
  }
  
  // Calcular estadísticas básicas
  const stats = {
    totalFacturas: paginacion.totalItems || 0,
    gastoTotalUSD: facturas ? facturas.reduce((sum, factura) => sum + parseFloat(factura.total_usd || 0), 0) : 0,
    gastoTotalBS: facturas ? facturas.reduce((sum, factura) => sum + parseFloat(factura.total_bs || 0), 0) : 0
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Encabezado */}
      <Typography variant="h4" gutterBottom>
        Lista Optimizada de Facturas
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Implementación optimizada para visualización de facturas
      </Typography>
      
      {/* Estadísticas básicas */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Estadísticas</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="textSecondary">Total Facturas</Typography>
            <Typography variant="h6">{stats.totalFacturas}</Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="textSecondary">Total USD (página actual)</Typography>
            <Typography variant="h6">${stats.gastoTotalUSD.toFixed(2)}</Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="textSecondary">Total Bs (página actual)</Typography>
            <Typography variant="h6">Bs.{stats.gastoTotalBS.toFixed(2)}</Typography>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Panel de filtros avanzados */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Filtros
          </Typography>
          <Button
            size="small"
            startIcon={<FilterListIcon />}
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
          >
            {mostrarFiltros ? 'Ocultar filtros' : 'Mostrar filtros'}
          </Button>
        </Box>
        
        {/* Filtros rápidos siempre visibles */}
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom>Filtros rápidos:</Typography>
          <ToggleButtonGroup
            value={filtroRapido}
            exclusive
            onChange={handleFiltroRapido}
            aria-label="filtros rápidos"
            size="small"
          >
            <ToggleButton value="hoy" aria-label="hoy">
              Hoy
            </ToggleButton>
            <ToggleButton value="semana" aria-label="semana actual">
              Semana Actual
            </ToggleButton>
            <ToggleButton value="mes" aria-label="mes actual">
              Mes Actual
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        
        {/* Filtros avanzados colapsables */}
        <Collapse in={mostrarFiltros}>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Fecha desde"
                value={filtros.fechaDesde}
                onChange={handleFechaDesdeChange}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Fecha hasta"
                value={filtros.fechaHasta}
                onChange={handleFechaHastaChange}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={6} sx={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end' }}>
              <Button 
                variant="outlined" 
                onClick={resetearFiltros} 
                sx={{ mr: 1 }}
              >
                Limpiar filtros
              </Button>
              <Button 
                variant="contained" 
                color="primary"
                onClick={aplicarFiltros}
              >
                Aplicar filtros
              </Button>
            </Grid>
          </Grid>
        </Collapse>
      </Paper>
      
      {/* Barra de búsqueda y acciones */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Buscar por número o ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              size="small"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={6} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              startIcon={<RefreshIcon />}
              variant="outlined"
              onClick={recargarFacturas}
              sx={{ mr: 1 }}
            >
              Actualizar
            </Button>
            <Button
              variant="outlined"
              color="info"
              onClick={() => navigate('/buscar-producto-historial')}
              sx={{ mr: 1 }}
            >
              Buscar Producto
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/facturas/nueva')}
            >
              Nueva Factura
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabla de facturas */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 'calc(100vh - 350px)' }}>
          <Table stickyHeader aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Número</TableCell>
                <TableCell>Fecha</TableCell>
                <TableCell align="right">Total USD</TableCell>
                <TableCell align="right">Total Bs</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell align="center">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {facturasFiltradas.length > 0 ? (
                facturasFiltradas.map((factura) => (
                  <TableRow key={factura.id} hover>
                    <TableCell>{factura.id}</TableCell>
                    <TableCell>{factura.numero}</TableCell>
                    <TableCell>{moment(factura.fecha).format('DD/MM/YYYY')}</TableCell>
                    <TableCell align="right">${parseFloat(factura.total_usd).toFixed(2)}</TableCell>
                    <TableCell align="right">Bs.{parseFloat(factura.total_bs).toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip 
                        label={factura.sincronizado_loyverse ? 'Sincronizado' : 'Pendiente'} 
                        color={factura.sincronizado_loyverse ? 'success' : 'warning'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell align="center">
                      <IconButton 
                        size="small" 
                        color="primary" 
                        onClick={() => verDetalleFactura(factura.id)}
                        title="Ver detalle"
                      >
                        <DescriptionIcon fontSize="small" />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="secondary" 
                        title="Sincronizar con Loyverse"
                        disabled={factura.sincronizado_loyverse}
                      >
                        <SyncIcon fontSize="small" />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="default" 
                        title="Exportar"
                      >
                        <GetAppIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    {searchTerm ? 'No se encontraron facturas que coincidan con la búsqueda' : 'No hay facturas disponibles'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Paginación */}
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <Pagination 
            count={paginacion.totalPages} 
            page={paginacion.page} 
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 2 }}>
          <Typography variant="body2" color="textSecondary" sx={{ mr: 2, alignSelf: 'center' }}>
            Filas por página:
          </Typography>
          <TextField
            select
            value={paginacion.pageSize}
            onChange={handlePageSizeChange}
            size="small"
            sx={{ width: 80 }}
          >
            {[10, 20, 50, 100].map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
        </Box>
      </Paper>
      
      {/* Información de depuración */}
      {process.env.NODE_ENV === 'development' && (
        <Paper sx={{ mt: 3, p: 2 }}>
          <Typography variant="h6" gutterBottom>Información de depuración</Typography>
          <Typography variant="body2">Estado: {status}</Typography>
          <Typography variant="body2">Facturas cargadas: {facturas.length}</Typography>
          <Typography variant="body2">Facturas filtradas: {facturasFiltradas.length}</Typography>
          <Typography variant="body2">Página actual: {paginacion.page}</Typography>
          <Typography variant="body2">Tamaño de página: {paginacion.pageSize}</Typography>
          <Typography variant="body2">Total de páginas: {paginacion.totalPages}</Typography>
          <Typography variant="body2">Total de facturas: {paginacion.totalItems}</Typography>
        </Paper>
      )}
    </Container>
  );
};

export default ListaDeFacturas;
