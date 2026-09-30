# -*- coding: utf-8 -*-
import sqlite3
import os

def inicializar_base_datos(db_path="biblioteca.db"):
    """
    Crea las tablas para el sistema con llaves foráneas y soporte para el flujo
    separado de Recepción -> Catalogación (Dewey, Sala, Estante, Origen).
    Maneja migraciones automáticas seguras si la base de datos ya existía.

    NOTA: Se eliminó la carga de datos semilla para que el sistema arranque vacío
    y el módulo de Recepción cree únicamente a partir de la entrada del usuario.
    """

    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # Habilitar soporte de llaves foráneas en SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- CONTROL DE MIGRACIÓN (Evita errores si biblioteca.db ya existía) ---
    try:
        cursor.execute("SELECT origen FROM libros LIMIT 1")
    except sqlite3.OperationalError:
        print("[!] Base de datos obsoleta detectada. Reconstruyendo tablas...")
        cursor.execute("DROP TABLE IF EXISTS ejemplares;")
        cursor.execute("DROP TABLE IF EXISTS libros;")
        cursor.execute("DROP TABLE IF EXISTS distribucion_detalles;")
        cursor.execute("DROP TABLE IF EXISTS distribuciones;")
        cursor.execute("DROP TABLE IF EXISTS bitacora;")
        cursor.execute("DROP TABLE IF EXISTS usuarios;")
        cursor.execute("DROP TABLE IF EXISTS bibliotecas;")

    # 1. Tabla de Usuarios y Roles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL, -- 'Administrador', 'Bibliotecario Central', 'Bibliotecario Sede'
            permisos TEXT NOT NULL
        )
    """)

    # 2. Tabla de Bibliotecas (Sedes) con datos de encargados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bibliotecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            direccion TEXT,
            tipo TEXT NOT NULL, -- 'Central' o 'Dependiente'
            encargado_nombre TEXT DEFAULT 'No asignado',
            encargado_contacto TEXT DEFAULT 'No asignado'
        )
    """)

    # 3. Tabla de Libros (Datos Bibliográficos únicos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            isbn TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            editorial TEXT,
            anio INTEGER,
            edicion TEXT,
            tema TEXT,
            dewey_codigo TEXT, -- Código Dewey (000 - 900)
            clasificacion TEXT, -- Cota de biblioteca generada
            idioma TEXT,
            origen TEXT -- 'Biblioteca Nacional', 'Donación', 'Compra', etc.
        )
    """)

    # 4. Tabla de Ejemplares (Copias físicas individuales con ubicación tridimensional)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ejemplares (
            id_unico TEXT PRIMARY KEY, -- Código de barra / Stock Number
            isbn TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'recibido', -- 'recibido', 'catalogado', 'en stock', 'en tránsito', 'distribuido', 'dado de baja'
            sala TEXT, -- Sala física donde se encuentra en la Central (ej. 'Sala de Ciencias')
            estante TEXT, -- Estante físico (ej. 'Estante B-12')
            biblioteca_id INTEGER NOT NULL,
            FOREIGN KEY (isbn) REFERENCES libros (isbn) ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (biblioteca_id) REFERENCES bibliotecas (id) ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    # 5. Tabla de Distribuciones (Lotes enviados desde la Central)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distribuciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origen_id INTEGER NOT NULL,
            destino_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            responsable TEXT NOT NULL,
            observaciones TEXT,
            estado TEXT NOT NULL DEFAULT 'en tránsito',
            FOREIGN KEY (origen_id) REFERENCES bibliotecas (id),
            FOREIGN KEY (destino_id) REFERENCES bibliotecas (id)
        )
    """)

    # 6. Detalle de Distribuciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distribucion_detalles (
            distribucion_id INTEGER NOT NULL,
            ejemplar_id TEXT NOT NULL,
            PRIMARY KEY (distribucion_id, ejemplar_id),
            FOREIGN KEY (distribucion_id) REFERENCES distribuciones (id) ON DELETE CASCADE,
            FOREIGN KEY (ejemplar_id) REFERENCES ejemplares (id_unico) ON DELETE CASCADE
        )
    """)

    # 7. Auditoría y Trazabilidad (Bitácora del sistema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            usuario TEXT NOT NULL,
            accion TEXT NOT NULL,
            detalle TEXT NOT NULL
        )
    """)

    # --- MIGRACIÓN DINÁMICA DE CAMPOS DE ENCARGADO EN DB VIEJA ---
    cursor.execute("PRAGMA table_info(bibliotecas);")
    cols = [col[1] for col in cursor.fetchall()]
    if "encargado_nombre" not in cols:
        cursor.execute("ALTER TABLE bibliotecas ADD COLUMN encargado_nombre TEXT DEFAULT 'No asignado';")
    if "encargado_contacto" not in cols:
        cursor.execute("ALTER TABLE bibliotecas ADD COLUMN encargado_contacto TEXT DEFAULT 'No asignado';")

    conexion.commit()
    conexion.close()
    print("[-] Base de datos inicializada correctamente (sin datos semilla).")

