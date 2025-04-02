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
  Pagination
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';
import moment from 'moment';
import 'moment/locale/es';

moment.locale('es');

const ListaDeFacturas = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const facturas = useSelector((state) => state.facturas.items);
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  const paginacion = useSelector((state) => state.facturas.paginacion);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [facturasFiltradas, setFacturasFiltradas] = useState([]);
  
  // Cargar facturas al montar el componente
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        console.log('Iniciando carga de facturas optimizada...');
        await dispatch(fetchFacturasOptimizado({
          page: paginacion.page,
          pageSize: paginacion.pageSize
        })).unwrap();
        console.log('Facturas cargadas exitosamente (optimizado)');
      } catch (error) {
        console.error("Error al cargar facturas (optimizado):", error);
      }
    };
    
    obtenerDatos();
  }, [dispatch, paginacion.page, paginacion.pageSize]);
  
  // Filtrar facturas cuando cambia el término de búsqueda o la lista de facturas
  useEffect(() => {
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
    } else {
      setFacturasFiltradas([]);
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
  
  // Función para recargar facturas
  const recargarFacturas = () => {
    dispatch(fetchFacturasOptimizado({
      page: paginacion.page,
      pageSize: paginacion.pageSize
    }))
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
      
      {/* Barra de búsqueda y acciones */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Buscar por número de factura o ID..."
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
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" justifyContent="flex-end">
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={recargarFacturas}
              >
                Recargar facturas
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabla de facturas */}
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        <TableContainer>
          <Table aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell><strong>ID</strong></TableCell>
                <TableCell><strong>Número</strong></TableCell>
                <TableCell><strong>Fecha</strong></TableCell>
                <TableCell><strong>Total USD</strong></TableCell>
                <TableCell><strong>Total Bs</strong></TableCell>
                <TableCell><strong>Sincronizado</strong></TableCell>
                <TableCell><strong>Acciones</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {facturasFiltradas.length > 0 ? (
                facturasFiltradas.map((factura) => (
                  <TableRow key={factura.id} hover>
                    <TableCell>{factura.id}</TableCell>
                    <TableCell>{factura.numero || 'N/A'}</TableCell>
                    <TableCell>{moment(factura.fecha).format('DD/MM/YYYY HH:mm')}</TableCell>
                    <TableCell>${parseFloat(factura.total_usd || 0).toFixed(2)}</TableCell>
                    <TableCell>Bs.{parseFloat(factura.total_bs || 0).toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip 
                        label={factura.sincronizado_loyverse ? 'Sincronizado' : 'Pendiente'} 
                        color={factura.sincronizado_loyverse ? 'success' : 'warning'} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<DescriptionIcon />}
                        onClick={() => verDetalleFactura(factura.id)}
                        sx={{ mr: 1 }}
                      >
                        Ver
                      </Button>
                      {!factura.sincronizado_loyverse && (
                        <IconButton
                          color="primary"
                          size="small"
                          title="Sincronizar con Loyverse"
                        >
                          <SyncIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    {status === 'loading' ? 'Cargando facturas...' : 'No hay facturas disponibles'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Paginación */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body2" sx={{ mr: 2 }}>
              Filas por página:
            </Typography>
            <TextField
              select
              value={paginacion.pageSize}
              onChange={handlePageSizeChange}
              variant="outlined"
              size="small"
              sx={{ width: 80 }}
              SelectProps={{
                native: true,
              }}
            >
              {[10, 20, 50, 100].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </TextField>
          </Box>
          
          <Pagination
            count={paginacion.totalPages}
            page={paginacion.page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        </Box>
      </Paper>
      
      {/* Información de depuración */}
      <Paper elevation={1} sx={{ p: 2, mb: 4, bgcolor: '#f5f5f5' }}>
        <Typography variant="subtitle2" gutterBottom>Información de depuración</Typography>
        <Typography variant="body2">Estado Redux: {status}</Typography>
        <Typography variant="body2">Facturas en página actual: {facturas ? facturas.length : 0}</Typography>
        <Typography variant="body2">Facturas filtradas: {facturasFiltradas.length}</Typography>
        <Typography variant="body2">Página actual: {paginacion.page} de {paginacion.totalPages}</Typography>
        <Typography variant="body2">Total de facturas: {paginacion.totalItems}</Typography>
        {error && (
          <Typography variant="body2" color="error">Error: {error}</Typography>
        )}
      </Paper>
    </Container>
  );
};

export default ListaDeFacturas;
