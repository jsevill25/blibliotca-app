# Pendientes para publicación

- [ ] Generar y probar el paquete `onedir` en Windows 10/11 y Linux; la validación en los equipos de destino sigue pendiente.
- [ ] Instalar y abrir la interfaz Qt en equipos de destino; este entorno no dispone de `libGL.so.1` para verificar el arranque gráfico.
- [ ] Cambiar la clave inicial conocida `admin123` antes de cargar información institucional.
- [x] Retirar el selector, el servidor y los recursos web; mantener `main.py` como punto de entrada exclusivo de escritorio.
- [ ] Verificar físicamente las cotas con sus dimensiones configuradas y las fichas catalográficas en cuatro espacios por página Letter; cotejar los formatos institucionales con la persona responsable.
- [ ] Probar ejecución, escritura de base y backups desde una memoria USB en los sistemas operativos de destino.
- [ ] Simular recuperación desde un backup en un equipo limpio y documentar custodios, ubicación externa y frecuencia de copias.
- [ ] Definir permisos, retención y protección de `auditoria_log`; la bitácora actual no es inmutable y no registra cada operación bibliográfica.
- [ ] Completar aceptación con bibliotecarios usando datos de ensayo y registrar observaciones antes de autorizar el uso.
- [x] Ejecutar y registrar la suite automatizada tras los cambios de escritorio: `pytest -v` (24 aprobadas, 0 fallidas).

## Código heredado

`main.py` inicia la aplicación Qt. `views/main_view.py`, `models/libro_model.py` y parte de `controllers/libro_controller.py` pertenecen a la implementación anterior Tkinter/SQLite y no forman parte del flujo activo. Las tareas antiguas de edición de recepción aplicaban a esa vista heredada.
