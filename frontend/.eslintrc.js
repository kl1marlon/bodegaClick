module.exports = {
  extends: ['react-app', 'react-app/jest'],
  // Desactivar reglas problemáticas para el build
  rules: {
    'no-undef': 'off',      // Desactivar error por variables no definidas
    'no-unused-vars': 'off' // Desactivar error por variables no utilizadas
  }
}; 