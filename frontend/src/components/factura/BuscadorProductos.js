import React, { useState, useEffect } from 'react';
import {
  TextField,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  Typography
} from '@mui/material';

/**
 * Componente para buscar productos y mostrar resultados
 * 
 * @param {Object} props - Propiedades del componente
 * @param {Array} props.productos - Lista de productos disponibles
 * @param {function} props.onProductoSelect - Función a llamar cuando se selecciona un producto
 * @param {number} props.cantidad - Cantidad del producto a añadir
 * @param {function} props.onCantidadChange - Función a llamar cuando cambia la cantidad
 * @returns {JSX.Element} - Componente de búsqueda de productos
 */
const BuscadorProductos = ({ productos, onProductoSelect, cantidad, onCantidadChange }) => {
  // Estados locales
  const [productoSearch, setProductoSearch] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  const [showResults, setShowResults] = useState(false);

  // Filtrar productos cuando cambia el término de búsqueda
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

  // Manejar la selección de un producto
  const handleProductoSelect = (producto) => {
    onProductoSelect(producto);
    setProductoSearch('');
    setShowResults(false);
  };

  return (
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
          onChange={(e) => onCantidadChange(Number(e.target.value))}
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
  );
};

export default BuscadorProductos; 