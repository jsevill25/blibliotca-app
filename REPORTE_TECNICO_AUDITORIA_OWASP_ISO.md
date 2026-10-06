# Reporte técnico de auditoría: versión de escritorio

**Sistema:** Biblioteca Central Rómulo Gallegos  
**Alcance:** aplicación de escritorio Python/PySide6, SQLite/SQLAlchemy, PDF y XLSX.
**Ejecución automatizada:** `pytest -v` — **24 aprobadas, 0 fallidas** (5,93 s).
**Dictamen:** mejoras verificadas a nivel de código y pruebas automatizadas; no es certificación ni aprobación institucional para producción.

## Resumen

Se retiró del producto la alternativa web y se corrigió el defecto de navegación que impedía seleccionar las páginas del panel: el `QStackedWidget` recibe y muestra ahora la misma página registrada en el mapa de navegación. `main.py` inicia directamente el flujo de acceso PySide6. Las pruebas específicas de navegación no necesitan iniciar Qt, lo cual permitió probar esta lógica en el contenedor.

Los datos sintéticos de la suite se crean en bases SQLite temporales. No se agregaron registros ficticios a la base activa de la biblioteca. La prueba funcional visual completa no pudo ejecutarse en este entorno porque falta la dependencia de sistema `libGL.so.1`; por tanto, los 24 tests verdes no prueban el renderizado real, los diálogos ni la impresión física.

## Cambios de esta revisión

| Archivo | Cambio |
|---|---|
| `main.py` | Elimina la elección entre escritorio y web; abre directamente el login de PySide6 y conserva el cierre de SQLite si el acceso se cancela. |
| `views/main_window.py` | Registra la página scroll real del `QStackedWidget` y delega el registro/selección al helper testeable. |
| `views/navigation.py` | Nuevo helper para añadir páginas y actualizar página activa/estado de botones. |
| `views/interface_choice_view.py` | Eliminado el selector Escritorio/Web. |
| `web_preview.py` | Eliminado el servidor HTTP y su API de demostración/consulta. |
| `web/app.js`, `web/index.html`, `web/styles.css` | Eliminados los recursos del cliente web. |
| `tests/test_desktop_navigation.py` | Añade pruebas de selección de página, estado de navegación y entrypoint exclusivamente de escritorio. |
| `tests/test_operational_readiness.py` | Retira el test HTTP; conserva rendimiento sintético, generación PDF y restauración de backup aislada. |
| `tests/test_international_audit.py` | Retira pruebas exclusivas de cookies web; mantiene autenticación del controlador, exportaciones, auditoría, FK e integridad de backup. |
| `README.md` | Declara el alcance de escritorio y elimina instrucciones web obsoletas. |
| `views/manual_view.py` | Retira la instrucción de uso de la vista web. |
| `DOCUMENTACION_TECNICA_AUDITORIA.md` | Actualiza arquitectura, autorización, operación, suite y límites al alcance PySide6. |
| `INFORME_AUDITORIA_SISTEMA.md` | Enfoca hallazgos en escritorio, registra el cierre de la superficie web y el defecto de navegación, y mantiene riesgos abiertos. |
| `REPORTE_TECNICO_AUDITORIA_OWASP_ISO.md` | Sustituye el informe obsoleto sobre la API por este reporte de auditoría de escritorio. |
| `DESCRIPCION_PROYECTO.md` | Aclara que la distribución actual es escritorio-only y actualiza las limitaciones de verificación. |
| `TODO.md` | Registra el retiro de web y el resultado de pruebas actualizado. |

## Pruebas y validaciones ejecutadas

| Verificación | Resultado |
|---|---|
| `pytest -v` | 24 passed, 0 failed (5,93 s). |
| `tests/test_desktop_navigation.py` | 2 passed; página activa y botón seleccionado correctos, entrypoint sin importaciones web. |
| `tests/test_operational_readiness.py` | 2 passed; búsqueda sobre 300 libros sintéticos, matriz, PDF multipágina y restauración desde backup. |
| `tests/test_international_audit.py` | 5 passed; cambio obligatorio de clave a nivel controlador, saneamiento XLSX, ausencia de secretos en exportaciones, FK y `PRAGMA integrity_check`. |
| `python -m compileall -q main.py controllers database services views tests` | Correcto. |
| Importación/ejecución visual de PySide6 | No verificable en este contenedor: falta `libGL.so.1`. |
| Instalación en Windows/Linux objetivo, impresión física y aceptación bibliotecaria | Pendientes; requieren equipos, impresoras y personal institucionales. |

El resto de la suite conserva pruebas de esquema y migraciones existentes, recepción, servicios/sucursales y flujo integral. Las pruebas sintéticas no abren ni escriben en la base institucional.

## Estado de controles abordados

### OWASP (controles pertinentes)

| Área | Estado de esta revisión | Evidencia y límite |
|---|---|---|
| Control de acceso | Parcialmente cubierto | Login de escritorio, cambio obligatorio de clave y autorización administrativa en controladores/servicios tienen pruebas de componentes. No se validó dinámicamente cada pantalla Qt por rol. |
| Inyección en exportaciones | Mitigado y probado | XLSX neutraliza prefijos `=`, `+`, `-`, `@`, preservando los tipos numéricos. |
| Exposición de datos sensibles | Mitigada y probada | `password_hash` y `salt` se omiten en Excel/PDF; exportación integral requiere autorización administrativa. |
| Registro y monitoreo | Parcial | `auditoria_log` registra login, cambio de clave, acciones administrativas, exportaciones y backups; no es inmutable ni registra todos los cambios bibliográficos. |
| Superficie de ataque web | Retirada del producto | Se eliminaron entrypoint, servidor, API y frontend web; pruebas verifican el entrypoint de escritorio. No implica que la aplicación de escritorio esté certificada. |
| Credencial de instalación | Pendiente de operación | `admin123` es conocida y está documentada para bootstrap; debe cambiarse antes de cargar datos reales y se recomienda generar credenciales iniciales únicas por instalación. |

### ISO/IEC 25010 (calidad del producto)

| Característica | Evaluación limitada a evidencia disponible |
|---|---|
| Adecuación funcional | La suite cubre flujos bibliotecarios principales, documentos, exportaciones y respaldo con datos sintéticos. La aceptación del flujo real sigue pendiente. |
| Fiabilidad | Se prueban claves foráneas, operaciones de flujo, integridad y restauración SQLite en temporales; no hay ensayo en el hardware de destino. |
| Seguridad | Mejoras verificables en autorización de componentes, confidencialidad de exportaciones, neutralización XLSX y auditoría. Persisten riesgos de credencial bootstrap, cifrado de datos y cobertura de bitácora. |
| Mantenibilidad | Separación MVC y helper de navegación testeable; aún faltan migraciones versionadas y más cobertura automatizada. |
| Usabilidad/compatibilidad | No evaluables por completo aquí: no se pudo abrir la interfaz visual ni probar pantallas, escalado, impresoras, empaquetado o sistemas operativos finales. |

Estas observaciones son una autoevaluación técnica acotada; **no declaran conformidad ni certificación** con OWASP, ISO/IEC 25010 u otra norma.

## Riesgos y trabajo pendiente antes de uso institucional

1. Cambiar la clave bootstrap conocida y definir un proceso seguro de alta inicial.
2. Abrir la aplicación en un equipo con PySide6 y OpenGL instalados; comprobar login, cambio obligatorio de clave, navegación a cada módulo y acciones según rol.
3. Hacer un piloto con bibliotecarios y datos de ensayo; cotejar los formularios y PDFs con los formatos institucionales aprobados.
4. Probar el paquete de instalación en cada sistema objetivo y verificar rutas/permisos de SQLite y backups.
5. Imprimir muestras reales: fichas 2×2, tablas horizontales, saltos, acentos, escala y márgenes.
6. Ensayar recuperación en un equipo limpio, mantener una copia externa cifrada y definir responsables/retención.
7. Considerar cifrado de base/respaldo, historial de cambios bibliográficos, migraciones versionadas y revisión profesional de Cutter.

El resultado automatizado es un paso de verificación, no una certificación, una garantía de funcionamiento en equipos no probados ni una autorización para cargar datos institucionales.
