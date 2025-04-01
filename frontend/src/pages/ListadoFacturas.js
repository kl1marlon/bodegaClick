import React, { useEffect, useState } from 'react';
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
  Collapse,
  TextField,
  MenuItem,
  InputAdornment
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import FilterListIcon from '@mui/icons-material/FilterList';
import CloseIcon from '@mui/icons-material/Close';
import moment from 'moment';
import 'moment/locale/es';

moment.locale('es');

const ListadoFacturas = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const facturas = useSelector((state) => state.facturas.items);
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);
  const [filtros, setFiltros] = useState({
    fechaInicio: '',
    fechaFin: '',
    montoMinUSD: '',
    montoMaxUSD: '',
    sincronizado: 'todos',
    tipoTasa: 'todos'
  });

  // Estadísticas básicas
  const stats = {
    totalFacturas: facturas.length,
    gastoTotalUSD: facturas.reduce((sum, factura) => sum + factura.total_usd, 0),
    gastoTotalBS: facturas.reduce((sum, factura) => sum + factura.total_bs, 0)
  };

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchFacturas());
    }
  }, [status, dispatch]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const viewFacturaDetail = (facturaId) => {
    navigate(`/facturas/${facturaId}`);
  };

  const handleFiltroChange = (event) => {
    setFiltros({
      ...filtros,
      [event.target.name]: event.target.value
    });
  };

  const aplicarFiltros = () => {
    // Lógica para aplicar filtros
    // Por ahora solo volvemos a cargar todos
    dispatch(fetchFacturas(filtros));
  };

  const resetearFiltros = () => {
    setFiltros({
      fechaInicio: '',
      fechaFin: '',
      montoMinUSD: '',
      montoMaxUSD: '',
      sincronizado: 'todos',
      tipoTasa: 'todos'
    });
    dispatch(fetchFacturas());
  };

  const handleSincronizar = (facturaId) => {
    // Lógica para sincronizar con Loyverse
    console.log(`Sincronizando factura ${facturaId}`);
  };

  const handleExportar = (facturaId) => {
    // Lógica para exportar
    console.log(`Exportando factura ${facturaId}`);
  };

  const getSincronizadoChip = (sincronizado) => {
    return (
      <Chip 
        label={sincronizado ? 'Sincronizado' : 'Pendiente'} 
        color={sincronizado ? 'success' : 'warning'} 
        size="small" 
      />
    );
  };

  if (status === 'loading') {
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
        <Typography color="error" variant="h6">
          Error al cargar las facturas: {error}
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Encabezado con título y estadísticas */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Typography variant="h4" gutterBottom>
            Facturas de Compra
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Registro de facturas de compra para BodegaClick
          </Typography>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total Facturas</Typography>
                <Typography variant="h6">{stats.totalFacturas}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total USD</Typography>
                <Typography variant="h6">${stats.gastoTotalUSD.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total Bs</Typography>
                <Typography variant="h6">Bs.{stats.gastoTotalBS.toFixed(2)}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Panel de filtros */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Filtros
          </Typography>
          <IconButton onClick={() => setFiltrosAbiertos(!filtrosAbiertos)}>
            {filtrosAbiertos ? <CloseIcon /> : <FilterListIcon />}
          </IconButton>
        </Box>
        
        <Collapse in={filtrosAbiertos}>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Fecha desde"
                type="date"
                name="fechaInicio"
                value={filtros.fechaInicio}
                onChange={handleFiltroChange}
                InputLabelProps={{ shrink: true }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Fecha hasta"
                type="date"
                name="fechaFin"
                value={filtros.fechaFin}
                onChange={handleFiltroChange}
                InputLabelProps={{ shrink: true }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Monto mínimo (USD)"
                type="number"
                name="montoMinUSD"
                value={filtros.montoMinUSD}
                onChange={handleFiltroChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Monto máximo (USD)"
                type="number"
                name="montoMaxUSD"
                value={filtros.montoMaxUSD}
                onChange={handleFiltroChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Sincronizado"
                name="sincronizado"
                value={filtros.sincronizado}
                onChange={handleFiltroChange}
                variant="outlined"
                size="small"
              >
                <MenuItem value="todos">Todos</MenuItem>
                <MenuItem value="si">Sincronizados</MenuItem>
                <MenuItem value="no">No sincronizados</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Tipo de Tasa"
                name="tipoTasa"
                value={filtros.tipoTasa}
                onChange={handleFiltroChange}
                variant="outlined"
                size="small"
              >
                <MenuItem value="todos">Todos</MenuItem>
                <MenuItem value="BCV">BCV</MenuItem>
                <MenuItem value="PARALELO">Paralelo</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box display="flex" justifyContent="flex-end" gap={1}>
                <Button 
                  variant="outlined" 
                  onClick={resetearFiltros}
                >
                  Resetear
                </Button>
                <Button 
                  variant="contained" 
                  onClick={aplicarFiltros}
                >
                  Aplicar filtros
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Collapse>
      </Paper>
      
      {/* Tabla principal de facturas */}
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        <TableContainer>
          <Table aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell><strong>Número</strong></TableCell>
                <TableCell><strong>Fecha de Compra</strong></TableCell>
                <TableCell><strong>Total USD</strong></TableCell>
                <TableCell><strong>Total Bs</strong></TableCell>
                <TableCell><strong>Tasa</strong></TableCell>
                <TableCell><strong>% Ganancia</strong></TableCell>
                <TableCell><strong>Sincronizado</strong></TableCell>
                <TableCell><strong>Acciones</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(rowsPerPage > 0
                ? facturas.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                : facturas
              ).map((factura) => (
                <TableRow key={factura.id} hover>
                  <TableCell>{factura.numero || 'N/A'}</TableCell>
                  <TableCell>{moment(factura.fecha).format('DD/MM/YYYY HH:mm')}</TableCell>
                  <TableCell>${factura.total_usd.toFixed(2)}</TableCell>
                  <TableCell>Bs.{factura.total_bs.toFixed(2)}</TableCell>
                  <TableCell>{factura.tasa_cambio ? `${factura.tasa_cambio.valor} (${factura.tasa_cambio.tipo})` : 'N/A'}</TableCell>
                  <TableCell>{factura.porcentaje_ganancia}%</TableCell>
                  <TableCell>{getSincronizadoChip(factura.sincronizado_loyverse)}</TableCell>
                  <TableCell>
                    <Box sx={{ '& > button': { mr: 1 } }}>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<DescriptionIcon />}
                        onClick={() => viewFacturaDetail(factura.id)}
                      >
                        Ver
                      </Button>
                      {!factura.sincronizado_loyverse && (
                        <IconButton
                          color="primary"
                          size="small"
                          onClick={() => handleSincronizar(factura.id)}
                          title="Sincronizar con Loyverse"
                        >
                          <SyncIcon />
                        </IconButton>
                      )}
                      <IconButton
                        color="secondary"
                        size="small"
                        onClick={() => handleExportar(factura.id)}
                        title="Exportar factura"
                      >
                        <GetAppIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
              {facturas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No hay facturas disponibles
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, { label: 'Todas', value: -1 }]}
          component="div"
          count={facturas.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Filas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    </Container>
  );
};

export default ListadoFacturas; 