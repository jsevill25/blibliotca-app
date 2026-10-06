# Informe de auditoría del sistema

**Sistema evaluado:** Biblioteca Central Rómulo Gallegos  
**Fecha de revisión:** 6 de octubre de 2026  
**Tipo de trabajo:** revisión técnica de código fuente, arquitectura y pruebas disponibles  
**Resultado global:** **la aplicación y la auditoría se limitan al escritorio PySide6. A-01 a A-03 cuentan con controles implementados y probados; A-04 documenta y cierra la retirada de la vista web y el defecto de navegación reportado; A-07 está parcialmente mitigado. La puesta en marcha sigue condicionada a pruebas de despliegue y riesgos residuales.**
**Base de revisión:** estado del workspace disponible durante esta revisión; no se asocia a un commit de liberación.

## 1. Resumen ejecutivo

El sistema ofrece una base funcional para el flujo local de recepción, catalogación, ubicación y distribución. La arquitectura separa vistas, controladores, modelos y servicios; usa SQLAlchemy con claves foráneas SQLite habilitadas; las contraseñas se almacenan con PBKDF2-HMAC-SHA256, sal individual y comparación constante; y existen pruebas automatizadas para persistencia, flujos, documentos y respaldos.

La revisión encontró riesgos en confidencialidad, autorización y exportación XLSX, y el usuario reportó que los botones del panel no abrían los módulos. La exportación integral está restringida a administradores; hash/sal se excluyen de Excel y PDF; se neutralizan valores que podrían convertirse en fórmulas; y `auditoria_log` registra inicios de sesión, cambios de clave, acciones administrativas, exportaciones y respaldos. Se retiraron el selector web, el servidor HTTP y sus recursos. También se corrigió la navegación para seleccionar páginas reales del `QStackedWidget`. La suite Qt no pudo abrirse visualmente en este entorno por falta de `libGL.so.1`; el reporte técnico detalla las verificaciones automatizadas y sus límites.

**Dictamen:** los cambios y las pruebas locales no equivalen a certificación ni autorización de puesta en producción. La aplicación candidata ya no contiene una superficie web activa. Antes de operar con datos reales siguen siendo necesarios el piloto institucional, restauración en equipo limpio, revisión de permisos de archivos, apertura visual de Qt e impresión/aceptación del personal.

## 2. Alcance, método y limitaciones

### Alcance revisado

- Punto de entrada e interfaz: `main.py`, `views/main_window.py`, `views/login_view.py`, `views/navigation.py`.
- Autenticación y autorización de escritorio: `controllers/auth_controller.py`, `database/seed_data.py`.
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

**Cambio y verificación:** `views/main_window.py` habilita la opción sólo para administradores; `views/reportes_view.py` oculta el botón y vuelve a verificar el rol dentro del método; `services/excel_service.py` requiere autorización administrativa y excluye hash/sal incluso en la exportación permitida; las tablas de reporte PDF también filtran esos campos. Pruebas automatizadas verifican denegación por defecto, omisión de columnas y ausencia de valores secretos. La verificación interactiva por rol queda pendiente porque no se pudo iniciar Qt en este entorno.

**Riesgo residual:** la exportación administrativa todavía contiene datos operativos completos; se recomienda limitar el acceso al archivo y mantener un procedimiento de custodia. Si se distribuyeron XLSX integrales antes de la corrección, tratarlos como posible exposición de credenciales.

### A-02. Cambio inicial obligatorio de contraseña

**Severidad:** Moderada
**Estado:** El flujo de escritorio impone el cambio antes de aceptar la sesión; verificación visual Qt pendiente

**Evidencia inicial:** el usuario `admin` se crea con `debe_cambiar_clave=True` y la documentación publica la credencial bootstrap.

**Cambio y verificación:** `views/login_view.py` no acepta ni abre la ventana principal mientras la marca está activa; solicita y confirma la nueva clave, la cambia mediante `AuthController` y autentica de nuevo antes de continuar. Las pruebas de controlador verifican que las operaciones administrativas se rechazan mientras el cambio está pendiente y se habilitan después del cambio.

**Riesgo residual:** la credencial bootstrap sigue siendo fija/documentada y la interacción de los diálogos no pudo probarse gráficamente en este contenedor. Establecer una clave inicial única y cambiarla durante la instalación.

### A-03. Inyección de fórmulas en exportaciones XLSX

**Severidad:** Moderada  
**Estado:** Remediado y cubierto por prueba automatizada

**Evidencia inicial:** `services/excel_service.py` escribía directamente valores procedentes de registros; `=1+1` quedaba con `data_type` de fórmula.

**Cambio y verificación:** la serialización de textos antepone un apóstrofo a valores cuyos primeros caracteres significativos sean `=`, `+`, `-` o `@`; se fuerza el tipo de celda a texto. Una prueba verifica esos prefijos, incluidos tabuladores/retornos iniciales, y confirma que los números siguen siendo numéricos.

**Riesgo residual:** verificar archivos con los programas de hoja de cálculo adoptados por la institución y conservar los campos numéricos como datos numéricos.

### A-04. Superficie web retirada y navegación de escritorio corregida

**Severidad:** Baja (mantenibilidad/operación)
**Estado:** Cerrado en el código candidato; apertura visual Qt pendiente

**Evidencia inicial:** el punto de entrada ofrecía un selector Desktop/Web aunque la operación solicitada se limita a escritorio. Además, el panel añadía `QScrollArea` al `QStackedWidget` pero registraba una vista interna distinta, por lo que los botones no podían activar la página esperada.

**Cambio y verificación:** `main.py` entra directamente al flujo de login; se eliminaron el selector, el servidor HTTP y los archivos `web/`. La navegación registra y selecciona el mismo widget de página añadido al stack. Pruebas unitarias verifican el widget seleccionado, el estado del botón y que el entrypoint no importe la implementación web ni el selector.

**Riesgo residual:** no se pudo abrir la aplicación gráfica en este contenedor por falta de `libGL.so.1`; la aceptación visual debe realizarse en un equipo con runtime Qt/OpenGL instalado.

### A-05. Cutter automático no equivale a consulta Cutter-Sanborn ni garantiza norma BNV

**Severidad:** Moderada (integridad de catalogación)  
**Estado:** Abierto / limitación funcional

**Evidencia:** `CatalogacionController.sugerir_cutter()` normaliza letras y obtiene el número con suma de códigos de caracteres módulo 900. No carga una tabla Cutter-Sanborn ni contiene rangos de autoridad. La generación de cota reutiliza ese método. La cota final es editable, pero el flujo permite guardar la sugerencia como resultado catalográfico.

**Impacto:** las signaturas pueden diferir de los valores de autoridad bibliotecológica y producir ordenamiento físico inconsistente, duplicados o trabajo de recatalogación. La interfaz no muestra una garantía o nivel de confianza.

**Recomendación:** integrar una tabla Cutter-Sanborn/Cutter autorizada por la institución, versionarla y atribuir su fuente; si no se dispone de tabla, nombrar el valor como sugerencia heurística y exigir revisión de catalogador antes de guardar. Añadir casos de referencia aprobados por un profesional BNV.

**Criterio de cierre:** pruebas verificadas por catalogador para autores y títulos de muestra, incluidos diacríticos y homónimos; documentación de fuente/versión de tabla y revisión manual explícita cuando no exista coincidencia.

### A-06. Base y respaldos sin cifrado ni procedimiento institucional de recuperación

**Severidad:** Moderada  
**Estado:** Mitigado parcialmente; verificación y restauración aislada probadas

**Evidencia:** `config.py` ubica SQLite y respaldos junto a la aplicación. `services/backup_service.py` genera copias SQLite sin cifrado, conserva siete archivos en el mismo destino y elimina los más antiguos. El servicio ejecuta `PRAGMA integrity_check` antes de reportar éxito; las pruebas restauran una copia en una base temporal nueva y verifican integridad, datos y relaciones. No hay un asistente de restauración en la aplicación ni política institucional de cifrado o separación de medios.

**Impacto:** pérdida, robo o copia de la carpeta (incluida memoria portable) expone datos bibliográficos y personales; la misma avería física puede afectar base y respaldos. Una prueba automatizada en base temporal no acredita que el personal pueda recuperar una instalación en un equipo limpio.

**Recomendación:** usar cifrado de volumen/dispositivo o copias cifradas con gestión institucional de claves; conservar una copia separada del equipo; establecer responsables, retención, verificación de integridad y simulacros periódicos de restauración. Limitar permisos del directorio de datos al usuario del sistema operativo.

**Criterio de cierre:** procedimiento aprobado, evidencia de restauración por personal en dispositivo limpio y controles de acceso/cifrado comprobados.

### A-07. Trazabilidad de movimientos no cubre acciones administrativas ni valores anteriores

**Severidad:** Moderada  
**Estado:** Mitigado parcialmente; registro operativo disponible, cobertura institucional pendiente

**Evidencia inicial:** no existía bitácora general. Ahora `auditoria_log` registra login exitoso/fallido, cambio de clave, creación/edición/activación de cuentas y sucursales, exportaciones y respaldos. `recepcion` aún no conserva un historial completo de valores antes/después; tampoco se registran todas las operaciones bibliotecarias ni los fallos de autorización.

**Impacto residual:** ante un cambio bibliográfico incorrecto no siempre se puede establecer quién cambió qué valor anterior/nuevo. Un usuario con acceso directo a la base puede modificar o eliminar filas del log; la bitácora no es append-only, no tiene controles de retención ni alertas.

**Recomendación:** completar bitácora de sólo anexado con usuario de sistema limitado, almacenar hora UTC o documentar zona horaria, agregar historial antes/después minimizado y auditar modificaciones de catalogación/ubicación. Definir retención y restringir borrado/exportación de la bitácora.

**Criterio de cierre:** pruebas verifican eventos para acciones privilegiadas y correcciones; una actualización no elimina evidencia previa, la bitácora no guarda secretos y la institución aprueba sus permisos, retención y destino.

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
- Protección de operaciones de gestión de usuarios mediante rol administrador en el controlador.
- Claves foráneas activadas en SQLite y restricciones para roles, procedencias y estados.
- Contexto de sesión SQLAlchemy con commit/rollback explícito.
- Validaciones de estado para catalogación y distribución; verificación de libros catalogados antes del envío.
- Copia SQLite mediante API de backup, verificación automática de `PRAGMA integrity_check` y rotación limitada; existe prueba de restauración en una DB temporal.
- Suite automatizada con pruebas de arquitectura, auditoría, disponibilidad operativa, recepción MVC, servicios, flujo integral y navegación de escritorio; el número final se consigna en el reporte de esta revisión.

Estos controles no compensan los hallazgos abiertos ni validan la configuración final de despliegue.

## 6. Plan de remediación priorizado

### Prioridad inmediata (antes de datos reales)

1. Rotar la credencial bootstrap conocida y establecer el proceso seguro de instalación.
2. Completar la apertura visual y aceptación de los módulos PySide6 en los equipos objetivo.
3. Mantener las pruebas de exportación segura y verificar compatibilidad con las hojas de cálculo aprobadas.

### Prioridad de operación segura

4. **A-06:** cifrado, permisos, copia externa y prueba documentada de restauración.
5. **A-07:** ampliar el registro de auditoría para cambios bibliotecarios, antes/después y política de retención.

### Prioridad de calidad y mantenimiento

6. **A-05:** validar Cutter con fuente normativa y personal bibliotecario.
7. **A-08:** introducir migraciones versionadas y verificables.

## 7. Criterios de aceptación global

La recomendación de uso con datos reales podrá reconsiderarse cuando:

- se rote la credencial bootstrap y se documente el proceso seguro de instalación;
- se valide visualmente el flujo de escritorio y se confirme que todos los módulos accesibles por rol abren correctamente;
- se valide la bitácora contra la política de retención y se amplíe a los cambios bibliotecarios que requiera la institución;
- se realice una restauración documentada desde un respaldo separado;
- la institución acepte el proceso de revisión de cotas y la fuente de Cutter.

La ejecución actual de `pytest -v` registró **24 aprobadas y 0 fallidas**. La verificación automatizada debe repetirse en el entorno candidato y complementarse con pruebas de instalación, seguridad y aceptación; no equivale a certificación.
