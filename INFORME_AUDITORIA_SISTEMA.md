# Informe de auditoría del sistema

**Sistema evaluado:** Biblioteca Central Rómulo Gallegos  
**Fecha de revisión:** 6 de octubre de 2026  
**Tipo de trabajo:** revisión técnica de código fuente, arquitectura y pruebas disponibles  
**Resultado global:** **Las remediaciones de A-01 a A-03 cuentan con cambios de código; la puesta en marcha aún requiere pruebas en equipos reales y resolver los riesgos web condicionados.**  
**Base de revisión:** estado del workspace disponible durante esta revisión; no se asocia a un commit de liberación.

## 1. Resumen ejecutivo

El sistema ofrece una base funcional para el flujo local de recepción, catalogación, ubicación y distribución. La arquitectura separa vistas, controladores, modelos y servicios; usa SQLAlchemy con claves foráneas SQLite habilitadas; las contraseñas se almacenan con PBKDF2-HMAC-SHA256, sal individual y comparación constante; y existen pruebas automatizadas para persistencia, flujos, documentos y respaldos.

La revisión inicial encontró riesgos en confidencialidad, autorización y exportación XLSX. Durante las pruebas de disponibilidad se añadieron mitigaciones para A-01 a A-03: la exportación integral queda limitada al rol administrador en la vista y su método de acción, se excluyen los hashes/sales y se neutralizan textos que podrían convertirse en fórmulas; la API bloquea consultas y escrituras durante el cambio inicial obligatorio. Se añadieron pruebas para verificar los secretos omitidos, la neutralización de prefijos de fórmula y el flujo web de cambio de clave. La comprobación dinámica de la interfaz Qt no fue posible en este entorno por falta de `libGL.so.1`.

**Dictamen:** los cambios y las pruebas locales no equivalen a autorización de puesta en producción. No exponer la vista web a redes compartidas: siguen abiertos los hallazgos de transporte/sesión y la discrepancia sobre escrituras en modo no demo. Antes de operar con datos reales siguen siendo necesarios el piloto institucional, restauración en equipo limpio, revisión de permisos de archivos e impresión/aceptación del personal.

## 2. Alcance, método y limitaciones

### Alcance revisado

- Punto de entrada e interfaz: `main.py`, `views/main_window.py`, `views/login_view.py`, `views/interface_choice_view.py`.
- Autenticación y autorización: `controllers/auth_controller.py`, `database/seed_data.py`, `web_preview.py`.
- Persistencia: `database/db_manager.py` y `database/models.py`.
- Reportes, exportaciones y respaldos: `views/reportes_view.py`, `services/excel_service.py`, `services/pdf_service.py`, `services/backup_service.py`.
- Reglas de catalogación/cota: `controllers/catalogacion_controller.py` y su interfaz.
- Pruebas enumeradas bajo `tests/`.

### Método

Lectura estática de código y documentación, análisis de rutas y permisos, revisión de pruebas existentes, recolección de cantidad de pruebas con pytest y comprobación aislada del comportamiento de openpyxl para una cadena `=1+1`. Los hallazgos incluyen ruta de código y efecto observado o derivado directamente de la implementación.

### Limitaciones

No se revisaron una instalación productiva, base de datos real, configuración de sistema operativo, permisos de archivos en equipos destino, red institucional, proceso de despliegue ni políticas de la Biblioteca. No se ejecutaron pruebas de penetración, fuzzing, análisis dinámico de la interfaz Qt, análisis automatizado de dependencias o evaluación formal contra ISO 27001, OWASP ASVS u otro estándar. Este informe es técnico y preliminar; no es certificación ni opinión legal/regulatoria.

## 3. Criterios de severidad

- **Alta:** puede comprometer credenciales o permitir acceso no autorizado con impacto importante, dadas las condiciones indicadas.
- **Moderada:** puede afectar confidencialidad, integridad o disponibilidad, pero requiere condiciones adicionales o tiene alcance limitado.
- **Baja:** deficiencia de control o mantenimiento cuyo impacto directo es más acotado.

La severidad indicada es inherente al código observado; la probabilidad práctica depende de la exposición, los datos cargados y los controles del equipo donde se instale.

## 4. Hallazgos

### A-01. Exportación integral expone hashes y sales de usuarios

**Severidad:** Alta  
**Estado:** Mitigado en código; autorización de interfaz pendiente de prueba dinámica Qt

**Evidencia inicial:** `views/main_window.py` agregaba `ReportesView` para ambos roles y la exportación integral no comprobaba permisos; `services/excel_service.py` escribía también `usuarios.password_hash` y `usuarios.salt`. La tabla contiene ambos valores en `database/models.py`.

**Cambio y verificación:** `views/main_window.py` habilita la opción sólo para administradores; `views/reportes_view.py` oculta el botón y vuelve a verificar el rol dentro del método; `services/excel_service.py` excluye hash y sal incluso de la exportación administrativa. La prueba XLSX verifica la ausencia de esas columnas. La verificación interactiva por rol queda pendiente porque no se pudo iniciar Qt en este entorno.

**Riesgo residual:** la exportación administrativa todavía contiene datos operativos completos; se recomienda limitar el acceso al archivo y mantener un procedimiento de custodia. Si se distribuyeron XLSX integrales antes de la corrección, tratarlos como posible exposición de credenciales.

### A-02. El cambio inicial obligatorio no está impuesto por la API

**Severidad:** Alta en modo web; Moderada en escritorio  
**Estado:** Remediado en rutas HTTP probadas; credencial inicial estática aún requiere gestión de despliegue

**Evidencia inicial:** el usuario `admin` se crea con `debe_cambiar_clave=True` y la documentación publica la clave inicial. La API web originalmente no imponía la marca.

**Cambio y verificación:** `web_preview.py` permite que la sesión inicial consulte su estado y cambie su contraseña, pero bloquea con 403 las consultas y mutaciones protegidas mientras la marca está activa. Una prueba HTTP con servidor loopback y base temporal valida que la consulta y escritura se deniegan, que cambiar la clave habilita la API y que logout invalida el token.

**Riesgo residual:** el inicio de sesión crea una sesión restringida (no una sesión operativa) y la clave bootstrap sigue siendo fija/documentada. Antes del despliegue, debe establecerse una clave inicial única y cambiarla durante la instalación.

### A-03. Inyección de fórmulas en exportaciones XLSX

**Severidad:** Moderada  
**Estado:** Remediado y cubierto por prueba automatizada

**Evidencia inicial:** `services/excel_service.py` escribía directamente valores procedentes de registros; `=1+1` quedaba con `data_type` de fórmula.

**Cambio y verificación:** la serialización de textos antepone un apóstrofo a valores cuyos primeros caracteres significativos sean `=`, `+`, `-` o `@`; se fuerza el tipo de celda a texto. Una prueba verifica esos prefijos, incluidos tabuladores/retornos iniciales, y confirma que los números siguen siendo numéricos.

**Riesgo residual:** verificar archivos con los programas de hoja de cálculo adoptados por la institución y conservar los campos numéricos como datos numéricos.

### A-04. Servidor web sin TLS ni atributos completos de sesión si se expone a red

**Severidad:** Moderada; Alta si se enlaza fuera de loopback  
**Estado:** Abierto / condicionado

**Evidencia:** `web_preview.py` usa `ThreadingHTTPServer` y admite `--host`; opera sobre HTTP. La cookie declara `HttpOnly` y `SameSite=Strict`, pero no `Secure`, expiración ni renovación. La ejecución documentada mantiene el servicio en `127.0.0.1`, lo cual es la configuración recomendada actual.

**Impacto:** si se configura un host accesible desde la LAN, credenciales y cookies viajan sin cifrado de transporte; la sesión permanece en memoria hasta logout/proceso detenido y no tiene expiración propia. También aumenta la superficie de ataque de la API de pruebas.

**Recomendación:** mantener el modo web exclusivamente en loopback y etiquetarlo como vista local de prueba, o retirar ese modo de instalaciones productivas. Si se requiere acceso por red, ponerlo detrás de una arquitectura web soportada con TLS, expiración/rotación/revocación de sesión, controles anti-CSRF y límites de intentos. No exponer el servidor de desarrollo directamente.

**Criterio de cierre:** comprobación de configuración que impide escucha no-loopback en modo local; o controles TLS y sesión verificados en una configuración aprobada para red.

### A-09. La vista web anunciada como lectura puede modificar la base activa

**Severidad:** Moderada  
**Estado:** Abierto

**Evidencia:** `README.md` indica que sin `--demo` se puede consultar una base existente en modo lectura y que las escrituras sólo están habilitadas en `--demo`. Sin embargo, `main.py` inicia `run_web_preview()` con la base activa al elegir Web. En `web_preview.py`, las rutas autenticadas POST para `/api/recepcion`, `/api/catalogacion`, `/api/distribucion` y `/api/ubicacion` ejecutan los controladores sin verificar `self.demo_mode`; el flag sólo identifica la modalidad y la base temporal.

**Impacto:** una persona puede iniciar la modalidad creyendo que es de consulta y alterar registros reales; incluso con controles de autenticación válidos, una operación accidental o inesperada afecta la integridad de los datos y el historial.

**Recomendación:** decidir explícitamente el contrato: implementar un guardado de sólo lectura real para todas las rutas mutadoras cuando `demo_mode` sea falso, o actualizar claramente la interfaz y documentación para advertir que la vista web opera sobre la base activa y es de lectura/escritura. Mantener `--demo` aislado. Recomiendo requerir una opción explícita de habilitación de escritura para una base real.

**Criterio de cierre:** prueba de integración inicia servidor contra base no demo, intenta cada endpoint mutador y confirma rechazo sin alteración de tablas; la modalidad demo continúa escribiendo sólo en su base temporal.

### A-05. Cutter automático no equivale a consulta Cutter-Sanborn ni garantiza norma BNV

**Severidad:** Moderada (integridad de catalogación)  
**Estado:** Abierto / limitación funcional

**Evidencia:** `CatalogacionController.sugerir_cutter()` normaliza letras y obtiene el número con suma de códigos de caracteres módulo 900. No carga una tabla Cutter-Sanborn ni contiene rangos de autoridad. La generación de cota reutiliza ese método. La cota final es editable, pero el flujo permite guardar la sugerencia como resultado catalográfico.

**Impacto:** las signaturas pueden diferir de los valores de autoridad bibliotecológica y producir ordenamiento físico inconsistente, duplicados o trabajo de recatalogación. La interfaz no muestra una garantía o nivel de confianza.

**Recomendación:** integrar una tabla Cutter-Sanborn/Cutter autorizada por la institución, versionarla y atribuir su fuente; si no se dispone de tabla, nombrar el valor como sugerencia heurística y exigir revisión de catalogador antes de guardar. Añadir casos de referencia aprobados por un profesional BNV.

**Criterio de cierre:** pruebas verificadas por catalogador para autores y títulos de muestra, incluidos diacríticos y homónimos; documentación de fuente/versión de tabla y revisión manual explícita cuando no exista coincidencia.

### A-06. Base y respaldos sin cifrado de aplicación y sin restauración operacional evidenciada

**Severidad:** Moderada  
**Estado:** Abierto

**Evidencia:** `config.py` ubica SQLite y respaldos junto a la aplicación. `services/backup_service.py` genera copias SQLite sin cifrado, conserva siete archivos en el mismo destino y elimina los más antiguos. Las pruebas verifican creación, rotación e integridad SQLite, no recuperación integral en una instalación nueva. No se encontró política de cifrado, separación de medios ni procedimiento de restauración en la documentación revisada.

**Impacto:** pérdida, robo o copia de la carpeta (incluida memoria portable) expone datos bibliográficos y personales; la misma avería física puede afectar base y respaldos. Una copia creada no demuestra que pueda recuperarse y reanudarse la operación.

**Recomendación:** usar cifrado de volumen/dispositivo o copias cifradas con gestión institucional de claves; conservar una copia separada del equipo; establecer responsables, retención, verificación de integridad y simulacros periódicos de restauración. Limitar permisos del directorio de datos al usuario del sistema operativo.

**Criterio de cierre:** procedimiento aprobado, evidencia de restauración en dispositivo limpio y controles de acceso/cifrado comprobados.

### A-07. Trazabilidad de movimientos no cubre acciones administrativas ni valores anteriores

**Severidad:** Moderada  
**Estado:** Abierto

**Evidencia:** `movimientos` registra eventos bibliotecarios principales. `recepcion` conserva banderas, usuario y fecha de la última modificación, pero no historial de valores anterior/nuevo. Las operaciones de creación, modificación y desactivación de usuarios no registran un evento de auditoría persistente. No se encontró bitácora general de inicios de sesión, exportaciones, consultas sensibles o fallos de autorización.

**Impacto:** ante un cambio incorrecto o una exportación indebida no siempre se puede establecer quién hizo qué, cuándo y qué dato cambió. Una edición posterior puede sustituir la única evidencia de la corrección anterior.

**Recomendación:** definir eventos auditables y crear una bitácora de sólo anexado con actor, hora UTC/local documentada, operación, entidad/ID y antes/después minimizados. Registrar altas/bajas de usuarios, cambios de rol/clave sin guardar secretos, exportaciones, cambios de catalogación y ubicación. Restringir borrado y exportación de la bitácora.

**Criterio de cierre:** pruebas verifican eventos para acciones privilegiadas y correcciones; una actualización no elimina la evidencia previa y la bitácora no guarda contraseñas ni hashes.

### A-08. Migraciones de esquema no versionadas

**Severidad:** Baja  
**Estado:** Abierto

**Evidencia:** `database/db_manager.py` llama a `Base.metadata.create_all()` y contiene una comprobación manual de columna que aplica `ALTER TABLE` si falta `codigo_clasificacion`. No hay una tabla de versión de esquema ni un historial de migraciones en el repositorio revisado.

**Impacto:** conforme se acumulen cambios, el resultado de actualización puede depender de la versión inicial de la base, resultar difícil de auditar y complicar reversión o recuperación de instalaciones antiguas.

**Recomendación:** adoptar migraciones versionadas, explícitas y transaccionales, con copia previa, validación de versión y pruebas contra snapshots de bases antiguas.

**Criterio de cierre:** cada cambio de esquema cuenta con versión, upgrade probado desde las bases soportadas, validación posterior y procedimiento de recuperación.

## 5. Controles satisfactorios observados

- Hash de clave PBKDF2-HMAC-SHA256 con 310.000 iteraciones y sal aleatoria por usuario; comparación con `hmac.compare_digest`.
- Longitud mínima de diez caracteres para nuevas contraseñas.
- Protección de operaciones de gestión de usuarios mediante rol administrador en el controlador y rutas web.
- Claves foráneas activadas en SQLite y restricciones para roles, procedencias y estados.
- Contexto de sesión SQLAlchemy con commit/rollback explícito.
- Validaciones de estado para catalogación y distribución; verificación de libros catalogados antes del envío.
- Cookie web `HttpOnly` y `SameSite=Strict`; servidor documentado en loopback.
- Copia SQLite mediante API de backup y rotación limitada; prueba de integridad de copia.
- Suite automatizada con 13 casos recolectados: arquitectura (2), recepción MVC (5), servicios/sucursales (2) y flujo integral (4).

Estos controles no compensan los hallazgos abiertos ni validan la configuración final de despliegue.

## 6. Plan de remediación priorizado

### Prioridad inmediata (antes de datos reales o acceso remoto)

1. **A-01:** quitar hash/sal de toda exportación; limitar exportación de tablas a administradores y registrar uso.
2. **A-02:** hacer cumplir cambio obligatorio en servidor/API y evitar credenciales bootstrap conocidas en instalaciones de producción.
3. **A-04:** mantener web sólo en loopback hasta disponer de HTTPS y control de sesión adecuados.
4. **A-03:** neutralizar fórmulas en todo XLSX generado.

### Prioridad de operación segura

5. **A-06:** cifrado, permisos, copia externa y prueba documentada de restauración.
6. **A-07:** ampliar el registro de auditoría para cambios privilegiados y correcciones.

### Prioridad de calidad y mantenimiento

7. **A-05:** validar Cutter con fuente normativa y personal bibliotecario.
8. **A-08:** introducir migraciones versionadas y verificables.

## 7. Criterios de aceptación global

La recomendación de uso con datos reales podrá reconsiderarse cuando:

- las pruebas demuestren que una cuenta no administrativa no puede obtener exportaciones con material de autenticación;
- la API bloquee el acceso funcional mientras una cuenta tenga cambio de clave obligatorio pendiente;
- las entradas XLSX no se interpreten como fórmulas;
- el servicio web no se exponga sin TLS y controles de sesión;
- se realice una restauración documentada desde un respaldo separado;
- la institución acepte el proceso de revisión de cotas y la fuente de Cutter.

Se debe volver a ejecutar `pytest -q`, añadir pruebas específicas para los controles anteriores y guardar la salida asociada a la versión candidata. El resultado de la auditoría debe actualizarse después de remediar y volver a revisar cada hallazgo; no marcar los puntos como cerrados sólo por haber implementado un cambio.
