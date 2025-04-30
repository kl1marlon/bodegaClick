# Guía de Facturas en BodegaClick

## 1. ¿Cómo mostrar nuevos campos de factura en el frontend?

### Pasos generales:

1. **Verifica que el backend envía el campo**
   - Haz un `console.log(factura)` en el componente de React.
   - Si el campo aparece en el JSON, puedes usarlo directamente en el frontend.
   - Si NO aparece, debes agregarlo en el serializer y asegurarte de que la vista lo incluya en la respuesta.

2. **Agrega el campo en el serializer (backend)**
   - Abre `backend/facturacion/serializers.py`.
   - Asegúrate de que el campo esté en la clase `FacturaSerializer` (en la lista `fields`).
   - Si es calculado, usa un `SerializerMethodField`.

3. **Asegúrate de que la vista lo devuelva**
   - Abre `backend/facturacion/views.py`.
   - La vista debe usar el serializer correcto (por ejemplo, `FacturaSerializer`).
   - Si tienes una vista personalizada, agrega el campo manualmente en el diccionario de respuesta.

4. **Muestra el campo en el frontend**
   - Usa el campo en el JSX, por ejemplo:
     ```jsx
     {factura.tu_campo ? factura.tu_campo : 'N/A'}
     ```
   - Si es numérico, puedes formatearlo:
     ```jsx
     {factura.tu_campo ? parseFloat(factura.tu_campo).toFixed(2) : 'N/A'}
     ```

---

## 2. ¿Cómo se guarda el valor de la tasa de cambio al crear una nueva factura?

### Proceso general:

1. **El frontend envía la factura nueva**
   - Al crear una factura, se envía un POST a `/api/facturas/` con los datos:
     ```json
     {
       "numero": "F20250430-5291",
       "fecha": "2025-04-30T15:19:32",
       "moneda": "USD",
       "tasa_cambio": 109,  // <-- este es el ID de la tasa de cambio
       "porcentaje_ganancia": 30,
       "detalles": [ ... ]
     }
     ```

2. **El backend recibe y guarda**
   - El serializer `CrearFacturaSerializer` procesa los datos.
   - El campo `tasa_cambio` es una ForeignKey: se guarda como el ID relacionado.
   - El modelo `Factura` almacena la relación con la tabla de tasas de cambio.

3. **¿Cómo se obtiene el valor al consultar?**
   - Cuando consultas una factura, el serializer puede incluir el valor numérico de la tasa usando un método como:
     ```python
     def get_tasa_cambio_valor(self, obj):
         return obj.tasa_cambio.valor if obj.tasa_cambio else None
     ```
   - Así, el frontend recibe tanto el ID (`tasa_cambio`) como el valor (`tasa_cambio_valor`).

---

## 3. Tips para depuración y exploración

- Siempre revisa el JSON en la consola del navegador.
- Si el campo no aparece, revisa el serializer y la vista.
- Si el campo aparece pero el valor es incorrecto, revisa cómo se calcula o guarda en el backend.
- Puedes agregar nuevos campos calculados en el serializer usando `SerializerMethodField`.

---

## 4. Ejemplo de agregar un campo nuevo

Supón que quieres mostrar el tipo de tasa ("PARALELO", "BCV"):

1. En el serializer:
   ```python
   tipo_tasa = serializers.SerializerMethodField()
   def get_tipo_tasa(self, obj):
       return obj.tasa_cambio.tipo if obj.tasa_cambio else None
   ```
   Agrega `tipo_tasa` a la lista de campos.
2. En el frontend:
   ```jsx
   {factura.tipo_tasa ? factura.tipo_tasa : 'N/A'}
   ```

---

## 5. Recursos útiles
- Documentación oficial Django REST Framework: https://www.django-rest-framework.org/api-guide/serializers/
- Documentación React: https://react.dev/

---

¿Dudas o mejoras? ¡Agrega tus notas aquí!
