import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { fetchFacturas } from '../store/facturasSlice';
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
  AlertTitle
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
  
  // Estados para paginación
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [facturasFiltradas, setFacturasFiltradas] = useState([]);
  
  // Cargar facturas al montar el componente
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        console.log('Iniciando carga de facturas...');
        await dispatch(fetchFacturas()).unwrap();
        console.log('Facturas cargadas exitosamente');
      } catch (error) {
        console.error("Error al cargar facturas:", error);
      }
    };
    
    obtenerDatos();
  }, [dispatch]);
  
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
      setPage(0); // Resetear a la primera página cuando cambia el filtro
    } else {
      setFacturasFiltradas([]);
    }
  }, [searchTerm, facturas]);
  
  // Manejadores para la paginación
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Función para recargar facturas
  const recargarFacturas = () => {
    dispatch(fetchFacturas())
      .unwrap()
      .then(() => {
        console.log('Facturas recargadas exitosamente');
      })
      .catch(error => {
        console.error('Error al recargar facturas:', error);
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
    totalFacturas: facturas ? facturas.length : 0,
    gastoTotalUSD: facturas ? facturas.reduce((sum, factura) => sum + parseFloat(factura.total_usd || 0), 0) : 0,
    gastoTotalBS: facturas ? facturas.reduce((sum, factura) => sum + parseFloat(factura.total_bs || 0), 0) : 0
  };
  
  // Obtener facturas paginadas
  const facturasPaginadas = rowsPerPage > 0
    ? facturasFiltradas.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
    : facturasFiltradas;
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Encabezado */}
      <Typography variant="h4" gutterBottom>
        Lista Simplificada de Facturas
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Implementación alternativa para visualización de facturas
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
            <Typography variant="body2" color="textSecondary">Total USD</Typography>
            <Typography variant="h6">${stats.gastoTotalUSD.toFixed(2)}</Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="textSecondary">Total Bs</Typography>
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
              {facturasPaginadas.length > 0 ? (
                facturasPaginadas.map((factura) => (
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
        {facturasFiltradas.length > 0 && (
          <TablePagination
            rowsPerPageOptions={[5, 10, 25, { label: 'Todas', value: -1 }]}
            component="div"
            count={facturasFiltradas.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="Filas por página:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
          />
        )}
      </Paper>
      
      {/* Información de depuración */}
      <Paper elevation={1} sx={{ p: 2, mb: 4, bgcolor: '#f5f5f5' }}>
        <Typography variant="subtitle2" gutterBottom>Información de depuración</Typography>
        <Typography variant="body2">Estado Redux: {status}</Typography>
        <Typography variant="body2">Facturas en Redux: {facturas ? facturas.length : 0}</Typography>
        <Typography variant="body2">Facturas filtradas: {facturasFiltradas.length}</Typography>
        {error && (
          <Typography variant="body2" color="error">Error: {error}</Typography>
        )}
      </Paper>
    </Container>
  );
};

export default ListaDeFacturas;
