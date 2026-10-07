from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, exists, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_PATH
from database.models import Base, Book, BookStock, Library, Location
from database.seed_data import seed_initial_data


class DatabaseManager:
    def __init__(self, database_path: str | Path = DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite+pysqlite:///{self.database_path.as_posix()}", future=True)
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    @staticmethod
    def _enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)
        columnas_libros = {columna["name"] for columna in inspect(self.engine).get_columns("libros")}
        columnas_bibliotecas = {columna["name"] for columna in inspect(self.engine).get_columns("bibliotecas")}
        with self.engine.begin() as connection:
            if "numero_volumenes" not in columnas_libros:
                connection.execute(text("ALTER TABLE libros ADD COLUMN numero_volumenes INTEGER"))
            if "cantidad" not in columnas_libros:
                connection.execute(text("ALTER TABLE libros ADD COLUMN cantidad INTEGER NOT NULL DEFAULT 1"))
            if "precio_unitario" not in columnas_libros:
                connection.execute(text("ALTER TABLE libros ADD COLUMN precio_unitario NUMERIC(12, 2)"))
            if "municipio" not in columnas_bibliotecas:
                connection.execute(text("ALTER TABLE bibliotecas ADD COLUMN municipio VARCHAR(120) NOT NULL DEFAULT ''"))
        columnas = {columna["name"] for columna in inspect(self.engine).get_columns("catalogacion")}
        if "codigo_clasificacion" not in columnas:
            with self.engine.begin() as connection:
                connection.execute(text("ALTER TABLE catalogacion ADD COLUMN codigo_clasificacion VARCHAR(40) NOT NULL DEFAULT ''"))
        with self.session() as session:
            seed_initial_data(session, self.database_path)
            columnas_libros = {columna["name"] for columna in inspect(self.engine).get_columns("libros")}
            tablas = set(inspect(self.engine).get_table_names())
            if {"id", "cantidad", "activo"} <= columnas_libros and {"ubicaciones", "stock_libros"} <= tablas:
                self._migrar_existencias_legacy(session)

    @staticmethod
    def _migrar_existencias_legacy(session: Session) -> None:
        central_id = session.scalar(
            select(Library.id).where(Library.nombre == "Biblioteca Central Rómulo Gallegos")
        )
        ultima_ubicacion_id = (
            select(Location.id)
            .where(Location.libro_id == Book.id)
            .order_by(Location.fecha_ubicacion.desc(), Location.id.desc())
            .limit(1)
            .correlate(Book)
            .scalar_subquery()
        )
        faltantes = session.execute(
            select(Book.id, Book.cantidad, ultima_ubicacion_id)
            .where(
                Book.activo.is_(True),
                ~exists(select(BookStock.id).where(BookStock.libro_id == Book.id)),
            )
        ).all()
        for libro_id, cantidad, ubicacion_id in faltantes:
            ubicacion = session.get(Location, ubicacion_id) if ubicacion_id else None
            biblioteca_id = ubicacion.biblioteca_id if ubicacion and ubicacion.biblioteca_id else central_id
            if biblioteca_id is not None:
                session.add(BookStock(
                    libro_id=libro_id,
                    biblioteca_id=biblioteca_id,
                    cantidad=max(0, cantidad or 0),
                ))

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()


_default_database: DatabaseManager | None = None


def get_default_database() -> DatabaseManager:
    global _default_database
    if _default_database is None:
        _default_database = DatabaseManager()
        _default_database.initialize()
    return _default_database