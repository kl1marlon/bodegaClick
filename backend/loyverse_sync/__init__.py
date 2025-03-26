"""
Módulo de sincronización con Loyverse.

Este módulo proporciona funcionalidades para sincronizar productos entre 
BodegaClick y Loyverse, con un enfoque especial en:
- Importar categorías y datos básicos de productos desde Loyverse
- Preservar los precios definidos en BodegaClick (precio_base_usd)
- Exportar precios calculados desde BodegaClick hacia Loyverse
- Sincronización selectiva por categorías y tipos de tasa
""" 