from sqlalchemy import inspect, text
import sqlite3

from database.db_manager import DatabaseManager
from database.models import Library, User


def test_database_initializes_schema_seed_and_foreign_keys(tmp_path):
    database = DatabaseManager(tmp_path / "library.db")
    database.initialize()

    tables = set(inspect(database.engine).get_table_names())
    assert {
        "libros", "recepcion", "catalogacion", "bibliotecas", "ubicaciones",
        "bultos", "bulto_libros", "movimientos", "usuarios",
    } <= tables

    with database.session() as session:
        admin = session.query(User).filter_by(username="admin").one()
        central = session.query(Library).filter_by(nombre="Biblioteca Central Rómulo Gallegos").one()
        assert admin.rol == "admin"
        assert admin.debe_cambiar_clave is True
        assert admin.password_hash != "admin123"
        assert central.activa is True

    with database.engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    database.close()


def test_database_migrates_cataloging_code_column(tmp_path):
    path = tmp_path / "older.db"
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE catalogacion (
                id INTEGER PRIMARY KEY,
                libro_id INTEGER NOT NULL UNIQUE,
                fecha_catalogacion DATETIME NOT NULL,
                clasificacion VARCHAR(16) NOT NULL,
                cota_completa VARCHAR(120) NOT NULL,
                cutter VARCHAR(40) NOT NULL,
                catalogado_por INTEGER
            )
        """)

    database = DatabaseManager(path)
    database.initialize()
    columns = {column["name"] for column in inspect(database.engine).get_columns("catalogacion")}
    assert "codigo_clasificacion" in columns
    database.close()


def test_database_migrates_optional_package_form_fields(tmp_path):
    path = tmp_path / "older-books.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE libros (id INTEGER PRIMARY KEY, titulo TEXT NOT NULL)")

    database = DatabaseManager(path)
    database.initialize()
    columns = {column["name"] for column in inspect(database.engine).get_columns("libros")}
    assert {"precio_unitario", "numero_volumenes"} <= columns
    database.close()


def test_database_migrates_library_municipality(tmp_path):
    path = tmp_path / "older-libraries.db"
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE bibliotecas (
                id INTEGER PRIMARY KEY,
                nombre VARCHAR(180) NOT NULL UNIQUE,
                direccion VARCHAR(240) NOT NULL DEFAULT '',
                encargado VARCHAR(160) NOT NULL DEFAULT '',
                telefono VARCHAR(40) NOT NULL DEFAULT '',
                email VARCHAR(160) NOT NULL DEFAULT '',
                activa BOOLEAN NOT NULL DEFAULT 1
            )
        """)

    database = DatabaseManager(path)
    database.initialize()
    columns = {column["name"] for column in inspect(database.engine).get_columns("bibliotecas")}
    assert "municipio" in columns
    database.close()