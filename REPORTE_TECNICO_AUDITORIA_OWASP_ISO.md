# Reporte técnico de auditoría y verificación

**Sistema:** Biblioteca Central Rómulo Gallegos  
**Fecha:** 6 de octubre de 2026  
**Alcance:** controles de autenticación, autorización, exportación, auditoría operativa y respaldos.  
**Ejecución:** `pytest -v` — **24 aprobadas, 0 fallidas** (6,81 s).

Este reporte acompaña la documentación actualizada de uso en `README.md` y `views/manual_view.py`, la descripción funcional `DESCRIPCION_PROYECTO.md`, y la documentación técnica y de hallazgos en `DOCUMENTACION_TECNICA_AUDITORIA.md` e `INFORME_AUDITORIA_SISTEMA.md`.

## Resumen ejecutivo

Se reforzó el control del cambio obligatorio de contraseña, se protegieron las rutas web y la exportación integral, se excluyeron credenciales de exportaciones Excel/PDF, se añadieron registros de auditoría y se incorporó verificación de integridad a los respaldos. Las nuevas pruebas usan SQLite temporal y datos de ensayo; no acceden ni escriben en la base institucional.

El resultado es una **mejora parcial y verificada por pruebas automatizadas**, no una certificación OWASP ni ISO/IEC 25010, ni una autorización automática para producción. Continúan pendientes el despliegue y aceptación en equipos reales, TLS para el modo web si se expone a una red, rotación del usuario inicial conocido, caducidad de sesiones y una política de protección/retención de la bitácora.

## Cambios implementados

### Autenticación, autorización y sesión web

- `AuthController` registra inicios de sesión correctos/incorrectos y cambios de clave; ofrece una comprobación de autorización operativa que rechaza cuentas inactivas o con cambio de contraseña pendiente.
- La gestión de cuentas exige una cuenta administradora activa que ya haya completado el cambio obligatorio.
- La API verifica el estado operativo antes de servir rutas protegidas. Una sesión que se marque con cambio obligatorio pendiente vuelve a recibir 403 para consultas y escrituras; únicamente cambio de clave y logout permanecen disponibles.
- Las mutaciones web se rechazan fuera del modo `--demo`. La prueba confirma 403 y ausencia de persistencia.
- Las cookies usan `HttpOnly` y `SameSite=Strict`. `Secure` se agrega cuando `BLIBLIOTECA_ENV=production`, `APP_ENV=production` o `BLIBLIOTECA_COOKIE_SECURE=1`.
- La exportación integral está restringida al administrador en la vista y en el servicio.

### Exportaciones y datos sensibles

- Excel descarta columnas `password_hash` y `salt` en todas las hojas, incluidas exportaciones genéricas e integrales.
- La exportación integral exige autorización administrativa explícita.
- Los valores de texto iniciados por `=`, `+`, `-` o `@`, incluso después de espacios, tabuladores o retornos, se escriben como texto neutralizado. Los valores numéricos legítimos siguen siendo numéricos.
- Los generadores de tablas/reporte PDF eliminan las columnas sensibles antes de construir las tablas.

### Bitácora y respaldos

- Se añadió la tabla `auditoria_log`, creada automáticamente al inicializar una base existente.
- Registra fecha/hora, actor opcional con clave foránea, acción, origen de escritorio/IP e información resumida de la operación.
- Acciones cubiertas: `LOGIN_EXITOSO`, `LOGIN_FALLIDO`, `CAMBIO_CLAVE`, `EXPORTACION_DATOS`, `RESPALDO_DB` y `ACCION_ADMIN`.
- No se guardan contraseñas, hashes, sales ni tokens en los detalles de auditoría.
- `BackupService` ejecuta `PRAGMA integrity_check` en la copia recién creada y sólo reporta éxito si obtiene `ok`; el controlador registra el evento de respaldo.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `controllers/auth_controller.py` | Registra login exitoso/fallido, cambio de clave y acciones de gestión de usuarios; añade comprobación de acceso operativo y bloquea administración para cuentas con cambio de clave pendiente. |
| `controllers/backup_controller.py` | Registra cada respaldo exitoso con actor y origen. |
| `controllers/biblioteca_controller.py` | Registra altas y desactivaciones de sucursales. |
| `controllers/etiqueta_controller.py` | Registra exportaciones de fichas, etiquetas y documentos institucionales. |
| `database/models.py` | Añade `AuditoriaLog`, su clave foránea, índices y restricción de tipos de acción. |
| `services/audit_service.py` | Nuevo servicio común para validar y escribir eventos de auditoría. |
| `services/backup_service.py` | Verifica automáticamente la integridad SQLite del archivo antes de declarar exitoso el respaldo. |
| `services/excel_service.py` | Filtra campos secretos globalmente, protege celdas contra fórmulas y exige rol autorizado para exportación integral. |
| `services/pdf_service.py` | Excluye columnas de hash/sal en tablas y reportes PDF. |
| `web_preview.py` | Enforza cambio obligatorio por ruta, fija atributos de cookie y `Secure` según entorno, registra origen web y bloquea escrituras fuera del modo demo. |
| `views/bibliotecas_view.py` | Pasa el usuario activo para auditar operaciones sobre sucursales. |
| `views/distribucion_view.py` | Pasa base y actor al controlador de exportación para registrar los PDFs generados. |
| `views/main_window.py` | Inyecta el actor/base en vistas de reportes, sucursales y exportación; identifica el usuario que dispara backups. |
| `views/reportes_view.py` | Audita exportaciones PDF/Excel y backups; limita y vuelve a comprobar exportación integral. |
| `README.md` | Documenta audit log, restricciones de escritura web y configuración de cookie segura. |
| `DOCUMENTACION_TECNICA_AUDITORIA.md` | Actualiza cantidad y alcance de las pruebas automatizadas. |
| `INFORME_AUDITORIA_SISTEMA.md` | Actualiza los estados de hallazgos mitigados y riesgos residuales. |
| `REPORTE_TECNICO_AUDITORIA_OWASP_ISO.md` | Este informe detallado con inventario de cambios, resultados y evaluación parcial de alineación. |
| `DESCRIPCION_PROYECTO.md` | Actualiza resumen, documentos institucionales, controles de seguridad y estado de pruebas del proyecto. |
| `views/manual_view.py` | Actualiza las instrucciones integradas de primer acceso, modo web, matrices, fichas, exportaciones y respaldos. |
| `TODO.md` | Registra los pendientes reales para instalación, seguridad, impresión, recuperación y aceptación del personal. |
| `tests/test_database_architecture.py` | Comprueba que el esquema incluya `auditoria_log`. |
| `tests/test_international_audit.py` | Nueva suite de seis pruebas de autorización, exportaciones, claves foráneas, auditoría, cookies y respaldos. |
| `tests/test_operational_readiness.py` | Amplía la prueba HTTP para cookies y revocación operativa de sesiones, y comprueba bloqueo de escrituras fuera de modo demo. |
| `tests/test_services_and_branches.py` | Verifica que el servicio requiera rol admin, no exponga hash/sal y neutralice entradas de fórmula. |

## Resultado de pruebas

| Suite | Casos | Resultado |
|---|---:|---|
| `tests/test_database_architecture.py` | 4 | Aprobadas |
| `tests/test_international_audit.py` | 6 | Aprobadas |
| `tests/test_operational_readiness.py` | 3 | Aprobadas |
| `tests/test_recepcion_mvc.py` | 5 | Aprobadas |
| `tests/test_services_and_branches.py` | 2 | Aprobadas |
| `tests/test_system_workflow.py` | 4 | Aprobadas |
| **Total** | **24** | **24 aprobadas, 0 fallidas** |

La suite incluyó: contraseña obligatoria y sesión web previamente activa; bloqueo de escrituras fuera de demo; neutralización XLSX; exclusión de secretos en Excel/PDF; integridad de claves foráneas SQLite; bitácora para login, cambio de clave, acción administrativa y respaldo; atributos de cookie; y prueba de recuperación en una base temporal. También conserva la prueba con 300 registros sintéticos, búsqueda menor a dos segundos en este entorno y PDF de múltiples páginas. Este tiempo no es garantía de rendimiento en otros equipos.

## Estado de alineación

| Referencia | Estado observado | Límites |
|---|---|---|
| **OWASP — control de acceso** | Mitigación verificada: clave pendiente bloquea rutas protegidas; exportación integral y administración restringidas; web de consulta no escribe fuera de demo. | La revisión cubre rutas conocidas; los endpoints nuevos deben seguir el mismo control. No se realizó prueba de penetración. |
| **OWASP — inyección en exportaciones** | Mitigación implementada y probada para los prefijos de fórmula indicados; secretos filtrados en formatos tabulares. | Validar también con las aplicaciones de hoja de cálculo oficialmente usadas por la Biblioteca. |
| **OWASP — autenticación/sesión** | Cambio obligatorio impuesto en API; cookies con `HttpOnly` y `SameSite=Strict`, y `Secure` activable por configuración. | Servidor de prueba sin TLS, sesiones sin expiración/rotación, y credencial inicial publicada que debe cambiarse antes de usar. `Secure` presupone que el tráfico llega mediante HTTPS. |
| **OWASP — logging/monitoring** | Bitácora SQLAlchemy persistente para los seis grupos de acciones indicados, sin registrar secretos. | No es append-only ni a prueba de manipulación; faltan política de retención, acceso restringido, alertas y cobertura de todas las operaciones bibliotecarias. |
| **ISO/IEC 25010 — seguridad** | Avances verificables en confidencialidad (filtrado), integridad (guardas/FK/backup) y responsabilidad (eventos auditados). | Evidencia parcial; no se evaluaron exhaustivamente confidencialidad operacional, autenticidad, trazabilidad ni resiliencia ante incidentes. |
| **ISO/IEC 25010 — fiabilidad/mantenibilidad** | Pruebas automatizadas de regresión, integridad y restauración aislada; cambios en capas existentes. | No hubo validación de hardware/instalación productiva, prueba de carga formal, análisis de cobertura ni revisión de migraciones versionadas. |

Los resultados anteriores describen controles concretos; **no certifican cumplimiento** de OWASP, ISO/IEC 25010 ni de otra norma.

## Pendientes antes de habilitar el sistema a usuarios

1. Cambiar `admin123` durante la instalación y dejar de distribuir credenciales iniciales conocidas.
2. No exponer `web_preview.py` fuera de loopback; si se necesita acceso por red, usar una arquitectura HTTPS soportada y añadir expiración/renovación/revocación de sesiones, protección CSRF y límites de intentos.
3. Definir custodia, retención, permisos y respaldo de la bitácora; evaluar un destino de auditoría de sólo anexado.
4. Realizar instalación y restauración en un equipo limpio, comprobar permisos/rutas de base de datos e impresión física de los formatos.
5. Completar aceptación con bibliotecarios y aprobación institucional de formularios y documentos.

La verificación de interfaz Qt e impresión física no se pudo ejecutar en este entorno. El resultado automatizado no sustituye esas pruebas ni la revisión institucional.
