from datetime import date, datetime, time, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Location, Package, package_books


class ReportesController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def resumen(self, inicio: date | None = None, fin: date | None = None) -> dict:
        with self.database.session() as session:
            filtros_libros = [Book.activo.is_(True)]
            if inicio:
                filtros_libros.append(Book.fecha_ingreso >= inicio)
            if fin:
                filtros_libros.append(Book.fecha_ingreso < fin + timedelta(days=1))
            estados = dict(session.execute(
                select(Book.estado, func.count(Book.id)).where(*filtros_libros).group_by(Book.estado)
            ).all())
            recepcion = dict(session.execute(
                select(Book.procedencia, func.count(Book.id)).where(*filtros_libros).group_by(Book.procedencia)
            ).all())
            filtros_catalogacion = []
            if inicio:
                filtros_catalogacion.append(Cataloging.fecha_catalogacion >= datetime.combine(inicio, time.min))
            if fin:
                filtros_catalogacion.append(Cataloging.fecha_catalogacion < datetime.combine(fin + timedelta(days=1), time.min))
            catalogados = session.scalar(
                select(func.count(Cataloging.id)).where(*filtros_catalogacion)
            ) or 0
            pendientes = session.scalar(
                select(func.count(Book.id)).where(Book.activo.is_(True), Book.estado == "recibido")
            ) or 0
            filtros_envio = []
            if inicio:
                filtros_envio.append(Package.fecha_envio >= datetime.combine(inicio, time.min))
            if fin:
                filtros_envio.append(Package.fecha_envio < datetime.combine(fin + timedelta(days=1), time.min))
            distribucion = list(session.execute(
                select(Library.nombre, func.count(package_books.c.libro_id))
                .join(Package, Package.biblioteca_destino_id == Library.id)
                .join(package_books, package_books.c.bulto_id == Package.id)
                .where(*filtros_envio)
                .group_by(Library.nombre).order_by(Library.nombre)
            ).all())
            ultima_ubicacion_id = (
                select(Location.id).where(Location.libro_id == Book.id)
                .order_by(desc(Location.fecha_ubicacion), desc(Location.id)).limit(1)
                .correlate(Book).scalar_subquery()
            )
            ubicacion_actual = aliased(Location)
            ubicaciones = list(session.execute(
                select(
                    func.coalesce(Library.nombre, "Central"),
                    func.coalesce(ubicacion_actual.tipo_ubicacion, "Sin ubicación"),
                    func.coalesce(ubicacion_actual.sala, ""),
                    func.coalesce(ubicacion_actual.estante, ""),
                    func.count(Book.id),
                )
                .select_from(Book)
                .outerjoin(ubicacion_actual, ubicacion_actual.id == ultima_ubicacion_id)
                .outerjoin(Library, Library.id == ubicacion_actual.biblioteca_id)
                .where(Book.activo.is_(True))
                .group_by(Library.nombre, ubicacion_actual.tipo_ubicacion, ubicacion_actual.sala, ubicacion_actual.estante)
                .order_by(Library.nombre, ubicacion_actual.sala, ubicacion_actual.estante)
            ).all())
            return {
                "total": sum(estados.values()), "estados": estados,
                "recepcion": recepcion,
                "catalogacion": {"catalogados": catalogados, "pendientes": pendientes},
                "distribucion": distribucion, "ubicaciones": ubicaciones,
            }

    def inventario(self, inicio: date | None = None, fin: date | None = None) -> list[dict]:
        with self.database.session() as session:
            filtros = [Book.activo.is_(True)]
            if inicio:
                filtros.append(Book.fecha_ingreso >= inicio)
            if fin:
                filtros.append(Book.fecha_ingreso <= fin)
            ultima_ubicacion_id = (
                select(Location.id).where(Location.libro_id == Book.id)
                .order_by(desc(Location.fecha_ubicacion), desc(Location.id)).limit(1)
                .correlate(Book).scalar_subquery()
            )
            ubicacion_actual = aliased(Location)
            filas = session.execute(
                select(Book, ubicacion_actual, Library.nombre)
                .select_from(Book)
                .outerjoin(ubicacion_actual, ubicacion_actual.id == ultima_ubicacion_id)
                .outerjoin(Library, Library.id == ubicacion_actual.biblioteca_id)
                .where(*filtros).order_by(Book.numero_registro)
            ).all()
            return [{
                "registro": libro.numero_registro, "titulo": libro.titulo, "autor": libro.autor,
                "isbn": libro.isbn, "estado": libro.estado, "cota": libro.cota,
                "procedencia": libro.procedencia, "fecha_ingreso": libro.fecha_ingreso.isoformat(),
                "biblioteca": nombre or "Central",
                "tipo_ubicacion": ubicacion.tipo_ubicacion if ubicacion else "Sin ubicación",
                "sala": ubicacion.sala if ubicacion else "",
                "estante": ubicacion.estante if ubicacion else "",
            } for libro, ubicacion, nombre in filas]