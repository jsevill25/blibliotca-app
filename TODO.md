# Pendientes para publicación

- [ ] Generar y probar el paquete `onedir` en Windows 10/11 y Linux; este contenedor no tiene una instalación de Python con biblioteca compartida para PyInstaller.
- [ ] Verificar impresión física de cotas y fichas en papel A4 y ajustar márgenes según la impresora disponible.
- [ ] Probar ejecución y escritura de base/backups desde una memoria USB en ambos sistemas operativos.

## Código heredado

`main.py` inicia la aplicación Qt. `views/main_view.py`, `models/libro_model.py` y parte de `controllers/libro_controller.py` pertenecen a la implementación anterior Tkinter/SQLite y no forman parte del flujo activo. Las tareas antiguas de edición de recepción aplicaban a esa vista heredada.

