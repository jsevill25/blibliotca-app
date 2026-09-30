# TODO - BlackboxAI

## Implementar edición de Recepción (tab "Modificar Recepción")
- [ ] Implementar en `views/main_view.py` las funciones faltantes:
  - [ ] `llenar_lista_recepcion`
  - [ ] `buscar_recepcion`
  - [ ] `cargar_recepcion_para_editar`
  - [ ] `eliminar_recepcion`
- [ ] Ajustar `models/libro_model.py` (si hace falta) para proveer el listado de recepciones “recibidas (sin procesar)”
- [ ] Ajustar `controllers/libro_controller.py` para exponer métodos para el listado y borrado de recepciones
- [ ] Probar flujo:
  - [ ] Ir a Recepción -> Modificar Recepción
  - [ ] Confirmar que el Treeview muestra registros
  - [ ] Seleccionar registro -> formulario se llena
  - [ ] Guardar Cambios -> actualiza recepción
  - [ ] Eliminar -> borra recepción por ISBN

