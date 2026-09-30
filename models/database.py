# -*- coding: utf-8 -*-
import sqlite3
import os

def inicializar_base_datos(db_path="biblioteca.db"):
    """
    Crea las tablas para el sistema con llaves foráneas y soporte para el flujo
    separado de Recepción -> Catalogación (Dewey, Sala, Estante, Origen).
    Maneja migraciones automáticas seguras si la base de datos ya existía.
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

    # --- DATOS SEMILLA ---
    cursor.execute("SELECT COUNT(*) FROM bibliotecas")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO bibliotecas (nombre, direccion, tipo, encargado_nombre, encargado_contacto) VALUES (?, ?, ?, ?, ?)
        """, [
            ("Biblioteca Central Canaima", "Av. Bolívar, Caracas", "Central", "Livia Quevedo", "+58-412-1111111"),
            ("Sede Norte - Caricuao", "Estación Caricuao, Caracas", "Dependiente", "Marcos Pérez", "+58-416-2222222"),
            ("Sede Sur - El Valle", "Av. Intercomunal, Caracas", "Dependiente", "Elena Blanco", "+58-424-3333333")
        ])

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO usuarios (username, password, rol, permisos) VALUES (?, ?, ?, ?)
        """, [
            ("admin", "admin123", "Administrador", "todos"),
            ("central", "central123", "Bibliotecario Central", "catalogacion,inventario,distribucion"),
            ("sede", "sede123", "Bibliotecario Sede", "inventario")
        ])

    cursor.execute("SELECT COUNT(*) FROM libros")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO libros (isbn, titulo, autor, editorial, anio, edicion, tema, dewey_codigo, clasificacion, idioma, origen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("978-607-02-1234-5", "Don Quijote de la Mancha", "Miguel de Cervantes", "Canaima Editores", 2021, "1ra", "Ficción", "800", "800\nC325d\n2021", "Español", "Biblioteca Nacional"),
            ("978-013-235088-4", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, "1ra", "Tecnología", "000", "000\nM210c\n2008", "Inglés", "Donación")
        ])

    cursor.execute("SELECT COUNT(*) FROM ejemplares")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO ejemplares (id_unico, isbn, estado, sala, estante, biblioteca_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("EJ-QUIJOTE-001", "978-607-02-1234-5", "en stock", "Sala General", "Estante A-1", 1),
            ("EJ-QUIJOTE-002", "978-607-02-1234-5", "en stock", "Sala General", "Estante A-1", 1),
            ("EJ-CLEAN-001", "978-013-235088-4", "en stock", "Sala de Tecnología", "Estante T-4", 1)
        ])

    conexion.commit()
    conexion.close()
    print("[-] Base de datos inicializada correctamente.")
