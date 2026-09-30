# SPGB Rómulo Gallegos — Sistema de Gestión Bibliotecaria

Aplicación de escritorio para control de inventario central, catalogación Dewey y distribución de ejemplares a sedes dependientes de la red bibliotecaria.

## Requisitos

- Python 3.11+
- Tkinter (incluido en la mayoría de instalaciones de Python en Linux)

## Instalación

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

La base de datos SQLite `biblioteca.db` se crea automáticamente al iniciar.

## Usuarios de prueba

| Usuario   | Contraseña   | Rol                    |
|-----------|--------------|------------------------|
| admin     | admin123     | Administrador          |
| central   | central123   | Bibliotecario Central  |
| sede      | sede123      | Bibliotecario Sede     |

## Módulos principales

- **Recepción** — ingreso de libros nuevos (estado `recibido`)
- **Catalogación** — clasificación Dewey, cota Cutter-Sanborn y ubicación física
- **Inventario** — matriz de stock por sede y gestión de ejemplares
- **Distribución** — envío de lotes a bibliotecas dependientes
- **Reportes** — fichas bibliográficas, actas de distribución y cotas en PDF
- **Administración** — usuarios, respaldos y auditoría

## Arquitectura

```
main.py
├── models/
│   ├── database.py      # Esquema SQLite y datos semilla
│   └── libro_model.py   # Acceso a datos
├── controllers/
│   └── libro_controller.py
└── views/
    └── main_view.py     # Interfaz CustomTkinter
```

## Licencia

Uso interno — SPGB Rómulo Gallegos.
# blibliotca-app
