# Sistema Bibliotecario Rómulo Gallegos

Aplicación de escritorio MVC para registrar, catalogar, ubicar y distribuir libros entre la Biblioteca Central y sus sucursales. La nueva interfaz usa PySide6, SQLAlchemy y SQLite; conserva los módulos anteriores en el repositorio, pero `main.py` inicia el sistema Qt.

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

La primera ejecución crea `data/biblioteca_central.db`, las tablas necesarias y la Biblioteca Central. El usuario inicial es `admin` con contraseña `admin123`; el sistema obliga a cambiarla en el primer ingreso y exige una contraseña de al menos 10 caracteres.

## Módulos

- Recepción: alta, búsqueda por texto/procedencia/fecha y corrección auditada de ingresos con número `REG-AAAA-NNNNN`.
- Catalogación: pendientes, sugerencia Cutter, clasificación Dewey/LC persistida y asignación de cota con advertencia de duplicados.
- Distribución: envíos `ENV-AAAAMMDD-NNN` sólo con libros catalogados; registra ubicación y movimientos.
- Ubicación: búsqueda global, filtros por estado/biblioteca/sala, última ubicación, último movimiento e historial.
- Reportes: recepción, catalogación, distribución e inventario por ubicación en PDF/Excel; exportación completa de tablas y respaldo SQLite.
- Etiquetas: cotas PDF con dimensiones ajustables y fichas catalográficas de 7,5 × 12,5 cm, cuatro por hoja.
- Usuarios: alta, edición, cambio de contraseña y activación/desactivación; las operaciones se autorizan en el controlador sólo para administradores.

Los respaldos se guardan en `data/backups` (o junto a la base configurada) y se rotan para conservar los siete más recientes. La aplicación también crea uno al cerrarse.

## Pruebas

```bash
pytest -q
```

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
