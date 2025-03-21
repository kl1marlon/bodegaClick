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
  CircularProgress
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InventoryIcon from '@mui/icons-material/Inventory';
import { fetchProductos } from '../store/productosSlice';

const ListadoProductos = () => {
  const dispatch = useDispatch();
  const { items: productos, status } = useSelector((state) => state.productos);
  
  // Estados para paginación
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  
  // Cargar productos al montar el componente
  useEffect(() => {
    if (status !== 'succeeded') {
      dispatch(fetchProductos());
    }
  }, [dispatch, status]);
  
  // Filtrar productos cuando cambia el término de búsqueda o la lista de productos
  useEffect(() => {
    if (productos.length > 0) {
      if (searchTerm.trim() === '') {
        setProductosFiltrados(productos);
      } else {
        const filtered = productos.filter(producto => 
          producto.nombre.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setProductosFiltrados(filtered);
      }
      setPage(0); // Resetear a la primera página cuando cambia el filtro
    }
  }, [searchTerm, productos]);
  
  // Manejadores para la paginación
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Productos para la página actual
  const productosEnPagina = productosFiltrados.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
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
          paddingBottom: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        <InventoryIcon fontSize="large" />
        Inventario de Productos
      </Typography>
      
      {/* Panel de estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
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
        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Resultados de búsqueda
              </Typography>
              <Typography variant="h3" component="div" color={searchTerm ? 'secondary' : 'primary'}>
                {productosFiltrados.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Página actual
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {page + 1} / {Math.max(1, Math.ceil(productosFiltrados.length / rowsPerPage))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Buscador */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff'
        }}
      >
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
      </Paper>
      
      {/* Tabla de productos */}
      <Paper 
        elevation={3} 
        sx={{ 
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        {status === 'loading' ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer sx={{ maxHeight: 'calc(100vh - 350px)' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Producto</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Código</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio USD</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio BS</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Categoría</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Stock</TableCell>
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
                        ${Number(producto.precio_base).toFixed(2)}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.precio_bs ? producto.precio_bs.toFixed(2) : 'N/A'}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.categoria ? (
                          <Chip 
                            label={producto.categoria} 
                            size="small" 
                            sx={{ 
                              backgroundColor: '#e0f2fe',
                              color: '#0369a1',
                              fontWeight: 500
                            }} 
                          />
                        ) : 'Sin categoría'}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Chip 
                          label={producto.stock || '0'} 
                          size="small"
                          color={producto.stock > 10 ? 'success' : producto.stock > 0 ? 'warning' : 'error'}
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                  {productosEnPagina.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center" sx={{ py: 4, color: '#6b7280' }}>
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
    </Box>
  );
};

export default ListadoProductos; 