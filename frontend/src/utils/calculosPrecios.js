/**
 * Utilidades para el cálculo de precios
 */

/**
 * Calcula el precio de venta basado en los parámetros dados
 * @param {number} precio_compra_usd - Precio de compra en USD
 * @param {number} unidades_paquete - Unidades por paquete
 * @param {number} tasa_cambio_valor - Valor de la tasa de cambio
 * @param {number} porcentaje - Porcentaje de ganancia
 * @param {boolean} aplicarIva - Si se debe aplicar IVA
 * @returns {number} - Precio de venta calculado
 */
export const calcularPrecioVenta = (precio_compra_usd, unidades_paquete, tasa_cambio_valor, porcentaje, aplicarIva = false) => {
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

/**
 * Calcula el precio base USD dividiendo el precio de compra por las unidades por paquete
 * @param {number} precio_compra_usd - Precio de compra en USD
 * @param {number} unidades_paquete - Unidades por paquete
 * @returns {number} - Precio base en USD por unidad
 */
export const calcularPrecioBaseUSD = (precio_compra_usd, unidades_paquete) => {
  precio_compra_usd = Number(precio_compra_usd) || 0;
  unidades_paquete = Number(unidades_paquete) || 1;
  
  if (precio_compra_usd === 0 || unidades_paquete === 0) {
    return 0;
  }
  
  // Precio base por unidad = precio de compra / unidades por paquete
  const precio_base = precio_compra_usd / unidades_paquete;
  return parseFloat(precio_base.toFixed(2));
};

/**
 * Calcula el precio base USD incluyendo el porcentaje de ganancia y el IVA si aplica
 * @param {number} precio_compra_usd - Precio de compra en USD
 * @param {number} unidades_paquete - Unidades por paquete
 * @param {number} porcentaje - Porcentaje de ganancia
 * @param {boolean} aplicarIva - Si se debe aplicar IVA
 * @returns {number} - Precio base en USD por unidad con ganancia e IVA
 */
export const calcularPrecioBaseUSDConGanancia = (precio_compra_usd, unidades_paquete, porcentaje, aplicarIva = false) => {
  // Convertir a números para evitar errores
  precio_compra_usd = Number(precio_compra_usd) || 0;
  unidades_paquete = Number(unidades_paquete) || 1;
  porcentaje = Number(porcentaje) || 0;
  
  if (precio_compra_usd === 0 || unidades_paquete === 0) {
    return 0;
  }
  
  // Calcular el precio base por unidad
  const precio_base = precio_compra_usd / unidades_paquete;
  
  // Aplicar el porcentaje de ganancia
  const precio_con_ganancia = precio_base * (1 + (porcentaje / 100));
  
  // Aplicar IVA si está activado
  const precio_final = aplicarIva ? precio_con_ganancia * 1.16 : precio_con_ganancia;
  
  // Redondear a 2 decimales para evitar problemas de precisión
  return parseFloat(precio_final.toFixed(2));
};

/**
 * Aplica reglas de redondeo especiales a precios en bolívares
 * @param {number} precioBs - Precio en bolívares
 * @returns {number} - Precio redondeado según reglas especiales
 */
export const aplicarRedondeoEspecial = (precioBs) => {
  // Asegurarse de que sea un número
  precioBs = Number(precioBs) || 0;
  
  // Primero redondeamos a 2 decimales para evitar problemas de precisión
  precioBs = Math.round(precioBs * 100) / 100;
  
  // Convertir a entero para trabajar con la parte entera
  const entero = Math.floor(precioBs);
  const decimal = precioBs - entero;
  
  // Verificar si el número ya termina en 0 o 5
  const residuo = entero % 10;
  const terminaEn5o0 = residuo === 0 || residuo === 5;
  
  // Si ya termina en 0 o 5 y no tiene decimales, mantenerlo igual
  if (terminaEn5o0 && decimal === 0) {
    return entero;
  }
  
  // Para precios menores a 20
  if (entero < 20) {
    if (entero < 5) {
      // Números menores a 5
      if (entero <= 2) {
        // 1 y 2 se mantienen igual
        return entero;
      } else {
        // 3 y 4 se redondean a 5
        return 5;
      }
    } else if (entero < 10) {
      // Números entre 5 y 9
      if (entero == 5) {
        // Si es exactamente 5, se mantiene
        return 5;
      } else if (decimal > 0 && entero == 5) {
        // Si es mayor que 5 (5.algo), se redondea a 10
        return 10;
      } else if (entero > 5) {
        // 6, 7, 8, 9 se redondean a 10
        return 10;
      }
    } else if (entero < 15) {
      // Números entre 10 y 14
      if (entero == 10) {
        return 10;
      } else if (entero == 11) {
        return 10;
      } else {
        // 12, 13, 14 se redondean a 15
        return 15;
      }
    } else {
      // Números entre 15 y 19
      if (entero == 15) {
        return 15;
      } else if (entero == 16) {
        return 15;
      } else {
        // 17, 18, 19 se redondean a 20
        return 20;
      }
    }
  } else {
    // Para precios mayores o iguales a 20
    // Redondear al 5 o 0 más cercano
    if (residuo < 5) {
      // Números terminados en 0, 1, 2, 3, 4 se redondean al siguiente 5
      // Si ya termina en 0, se mantiene igual
      if (residuo === 0) {
        return entero;
      }
      return entero - residuo + 5;
    } else {
      // Números terminados en 5, 6, 7, 8, 9 se redondean al siguiente 0
      // Si ya termina en 5, se mantiene igual
      if (residuo === 5) {
        return entero;
      }
      return entero - residuo + 10;
    }
  }
};

/**
 * Calcula el precio en bolívares cuando el precio está en USD
 * @param {number} precio_usd - Precio en dólares
 * @param {number} tasa_valor - Valor de la tasa de cambio
 * @returns {number} - Precio en bolívares redondeado
 */
export const calcularPrecioBs = (precio_usd, tasa_valor) => {
  precio_usd = Number(precio_usd) || 0;
  tasa_valor = Number(tasa_valor) || 1;
  
  if (precio_usd === 0) return 0;
  
  const precioBs = precio_usd * tasa_valor;
  return aplicarRedondeoEspecial(precioBs);
};

/**
 * Calcula el precio directamente en bolívares
 * @param {number} precio_compra_usd - Precio de compra en USD
 * @param {number} unidades_paquete - Unidades por paquete
 * @param {number} tasa_valor - Valor de la tasa de cambio
 * @param {number} porcentaje - Porcentaje de ganancia
 * @param {boolean} aplicarIva - Si se debe aplicar IVA
 * @returns {number} - Precio en bolívares con reglas de redondeo aplicadas
 */
export const calcularPrecioDirectoEnBs = (precio_compra_usd, unidades_paquete, tasa_valor, porcentaje, aplicarIva) => {
  // Convertir a números para evitar errores
  precio_compra_usd = Number(precio_compra_usd) || 0;
  unidades_paquete = Number(unidades_paquete) || 1;
  tasa_valor = Number(tasa_valor) || 1;
  porcentaje = Number(porcentaje) || 0;
  
  if (precio_compra_usd === 0 || unidades_paquete === 0) return 0;
  
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

/**
 * Calcula el precio de venta cuando se trabaja directamente en bolívares
 * @param {number} precio_compra_bs - Precio de compra en Bolívares
 * @param {number} unidades_paquete - Unidades por paquete
 * @param {number} porcentaje - Porcentaje de ganancia
 * @param {boolean} aplicarIva - Si se debe aplicar IVA
 * @returns {number} - Precio de venta en bolívares antes del redondeo
 */
export const calcularPrecioVentaBs = (precio_compra_bs, unidades_paquete, porcentaje, aplicarIva = false) => {
  console.log('Calculando precio venta en Bs con:', { 
    precio_compra_bs, 
    unidades_paquete, 
    porcentaje, 
    aplicarIva 
  });
  
  // Convertir a números para evitar errores
  precio_compra_bs = Number(precio_compra_bs) || 0;
  unidades_paquete = Number(unidades_paquete) || 1;
  porcentaje = Number(porcentaje) || 0;
  
  if (precio_compra_bs === 0) {
    console.log('Precio de compra BS no válido');
    return 0;
  }
  
  if (unidades_paquete === 0) {
    console.log('Unidades por paquete no válidas');
    return 0;
  }
  
  // Aplicar la fórmula: (precio_compra_bs / unidades) × (1 + porcentaje_ganancia/100)
  const precio_base_bs = precio_compra_bs / unidades_paquete;
  const precio_con_ganancia = precio_base_bs * (1 + (porcentaje / 100));
  
  // Aplicar IVA si está activado
  const precio_final = aplicarIva ? precio_con_ganancia * 1.16 : precio_con_ganancia;
  
  // Redondear a 2 decimales para evitar problemas de precisión
  const precio_redondeado = parseFloat(precio_final.toFixed(2));
  console.log('Precio final calculado en Bs:', precio_redondeado);
  return precio_redondeado;
};

/**
 * Calcula el precio base USD a partir del precio de venta en bolívares y la tasa
 * @param {number} precio_venta_bs - Precio de venta en bolívares (antes del redondeo)
 * @param {number} tasa_valor - Valor de la tasa de cambio
 * @returns {number} - Precio base en USD
 */
export const calcularPrecioBaseUSDDesdeBS = (precio_venta_bs, tasa_valor) => {
  precio_venta_bs = Number(precio_venta_bs) || 0;
  tasa_valor = Number(tasa_valor) || 1;
  
  if (precio_venta_bs === 0 || tasa_valor === 0) {
    return 0;
  }
  
  // Precio base USD = precio venta BS / tasa
  const precio_base_usd = precio_venta_bs / tasa_valor;
  return parseFloat(precio_base_usd.toFixed(2));
}; 