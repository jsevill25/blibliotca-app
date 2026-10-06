# Sistema Bibliotecario Rómulo Gallegos

Aplicación **exclusivamente de escritorio** para registrar, catalogar, ubicar y distribuir libros entre la Biblioteca Central y sus sucursales. La interfaz usa PySide6, SQLAlchemy y SQLite. `main.py` abre directamente el inicio de sesión de escritorio; no se incluye un servidor ni un cliente web.

La primera pestaña tras iniciar sesión es el manual gráfico de usuario; también está disponible desde el menú **Ayuda**. La descripción técnica y la base para la presentación académica del proyecto están en [DESCRIPCION_PROYECTO.md](DESCRIPCION_PROYECTO.md).

## Requisitos

- Python 3.11 o superior
- Qt/PySide6 y dependencias listadas en `requirements.txt`
- En Linux de escritorio se requiere el runtime OpenGL del sistema (paquete `libgl1` en Ubuntu/Debian)

## Instalación y ejecución

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

En Windows, activa el entorno con `.venv\Scripts\activate`.

## Primer acceso

La primera ejecución crea `data/biblioteca_central.db`, las tablas necesarias (incluida la bitácora) y la Biblioteca Central. La cuenta inicial es `admin` con la clave de instalación `admin123`; el primer ingreso obliga a cambiarla por una contraseña de al menos 10 caracteres. Esta clave inicial es conocida y sólo sirve para bootstrap: cámbiala antes de registrar información real y no la compartas.

## Módulos

- Recepción: alta, búsqueda por texto/procedencia/fecha y corrección auditada de ingresos con número `REG-AAAA-NNNNN`; precio unitario y número de volúmenes son opcionales.
- Catalogación: pendientes, sugerencia Cutter, clasificación Dewey/LC persistida y asignación de cota con advertencia de duplicados.
- Fichero: búsqueda e inventario catalogado; genera la Matriz de Control por Sucursales para un libro. Las marcas I (ingreso), D (disponibilidad) y P (préstamo) se calculan según el estado y la ubicación más recientes.
- Distribución: envíos `ENV-AAAAMMDD-NNN` sólo con libros catalogados; registra ubicación y movimientos, genera/consulta el Control de Envío institucional, la Nota de Entrega y la mini-ficha PDF. La nota prellena sucursal, municipio, volumen y fecha y solicita verificar el nombre y la cédula de quien recibe.
- Ubicación: búsqueda global, filtros por estado/biblioteca/sala, última ubicación, último movimiento e historial.
- Reportes: resumen de recepción, catalogación, distribución e inventario por ubicación en PDF/Excel; reporte matricial anual de sucursales por áreas Dewey en PDF Letter horizontal. Biografías y publicaciones periódicas se aproximan mediante rangos Dewey; las publicaciones oficiales y materiales no bibliográficos no se infieren porque el modelo no los clasifica.
- Etiquetas: cotas PDF de dimensiones ajustables y Ficha Catalográfica Individual, cuatro por hoja Letter con guías de corte.
- Usuarios: alta, edición, cambio de contraseña y activación/desactivación; las operaciones se autorizan en el controlador sólo para administradores.

Los respaldos se guardan en `data/backups` (o junto a la base configurada), se verifica `PRAGMA integrity_check` y se rotan para conservar los siete más recientes. La aplicación también intenta crear uno al cerrarse; si falla, muestra el error y pide confirmación antes de cerrar. El respaldo es una copia de SQLite, no está cifrado ni sustituye una copia externa. La restauración se verificó en pruebas sobre una base temporal; para recuperar una instalación, restaura manualmente una copia después de cerrar la aplicación y conserva intacto el original.

Los eventos de inicio de sesión (correctos e incorrectos), cambio de contraseña, administración de usuarios/sucursales, exportaciones y respaldos se registran en `auditoria_log`. La bitácora no guarda contraseñas, hashes ni tokens y todavía no cubre todos los cambios bibliotecarios. Las exportaciones Excel/PDF excluyen `password_hash` y `salt`; la exportación integral de tablas está disponible sólo para administradores. Los textos XLSX con prefijos de fórmula se neutralizan.

## Pruebas

```bash
pytest -q
```

Para ver el resultado detallado:

```bash
pytest -v
```

Las pruebas usan SQLite temporal y datos sintéticos. Consulta [DOCUMENTACION_TECNICA_AUDITORIA.md](DOCUMENTACION_TECNICA_AUDITORIA.md), [INFORME_AUDITORIA_SISTEMA.md](INFORME_AUDITORIA_SISTEMA.md) y [REPORTE_TECNICO_AUDITORIA_OWASP_ISO.md](REPORTE_TECNICO_AUDITORIA_OWASP_ISO.md) para el resultado actualizado y las pruebas de instalación, impresión y aceptación que aún deben realizarse por separado.

## Empaquetado

PyInstaller debe ejecutarse en el sistema operativo de destino; cada sistema necesita su propio build. En Linux de escritorio instala primero `libgl1`. Desde un entorno con las dependencias instaladas:

```bash
pyinstaller --noconfirm --onedir --name SistemaBibliotecarioRG \
	--hidden-import=PySide6.QtSvg \
	--hidden-import=reportlab.graphics.barcode \
	--collect-all=sqlalchemy \
	main.py
```

La base y los respaldos se crean en la carpeta `data` junto al ejecutable. Copia el directorio generado completo a la memoria USB.

Antes de distribuir, valida el ejecutable en Windows 10/11 y Linux, y prueba inicio de sesión, escritura de datos, generación de PDF y backup desde una carpeta USB con permisos de escritura.
