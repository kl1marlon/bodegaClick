import React from 'react';
import { Box, Container } from '@mui/material';
import NuevaFactura from './pages/NuevaFactura';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Container component="main" sx={{ mt: 4, mb: 4, flex: 1 }}>
        <NuevaFactura />
      </Container>
    </Box>
  );
}

export default App; 