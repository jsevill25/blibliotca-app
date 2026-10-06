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

## Vista web de prueba

Para recorrer en el navegador los módulos principales de la aplicación de escritorio con registros de muestra, ejecuta:

```bash
python web_preview.py --demo --port 8766
```

Abre `http://127.0.0.1:8766`. La vista incluye Manual, Recepción, Catalogación, Fichero e inventario, Distribución, Ubicación, Etiquetas, Reportes, Sucursales y Usuarios. Permite probar los flujos principales y generar documentos PDF/Excel; sus operaciones de escritura sólo están habilitadas en modo `--demo`, que usa una base SQLite temporal separada y no modifica los datos de la aplicación. La interfaz web comparte la lógica y el tema negro/amarillo del escritorio, con composición adaptable al navegador; no es una captura píxel por píxel de Qt. Para consultar una base existente en modo lectura, inicia el servidor sin `--demo` o indica su ruta con `--database /ruta/a/biblioteca_central.db`.

## Primer acceso

La primera ejecución crea `data/biblioteca_central.db`, las tablas necesarias y la Biblioteca Central. El usuario inicial es `admin` con contraseña `admin123`; el sistema obliga a cambiarla en el primer ingreso y exige una contraseña de al menos 10 caracteres.

## Módulos

- Recepción: alta, búsqueda por texto/procedencia/fecha y corrección auditada de ingresos con número `REG-AAAA-NNNNN`; precio unitario y número de volúmenes son opcionales.
- Catalogación: pendientes, sugerencia Cutter, clasificación Dewey/LC persistida y asignación de cota con advertencia de duplicados.
- Fichero: genera para un libro catalogado la matriz institucional anual por sucursal; las marcas de ingreso, disponibilidad y préstamo se basan en el estado y la ubicación más recientes registrados en SQLite.
- Distribución: envíos `ENV-AAAAMMDD-NNN` sólo con libros catalogados; registra ubicación y movimientos, genera/consulta el Control de Envío institucional y la Nota de Entrega en PDF. La nota completa sucursal, municipio, volumen y fecha; solicita confirmar nombre y cédula de quien recibe.
- Ubicación: búsqueda global, filtros por estado/biblioteca/sala, última ubicación, último movimiento e historial.
- Reportes: recepción, catalogación, distribución e inventario por ubicación en PDF/Excel; exportación completa de tablas y respaldo SQLite.
- Reportes: resumen matricial anual de sucursales por áreas Dewey, títulos y volúmenes, exportable en PDF Letter horizontal. Biografías y publicaciones periódicas se identifican por Dewey; publicaciones oficiales y material no bibliográfico quedan en cero porque aún no hay campos que los clasifiquen de forma fiable.
- Etiquetas: cotas PDF con dimensiones ajustables y fichas catalográficas individuales, cuatro por hoja Letter con guías de corte.
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
