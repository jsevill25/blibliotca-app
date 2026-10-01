from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from database.db_manager import DatabaseManager
from database.models import Book, Library, Location, Movement


class UbicacionController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def buscar(self, texto: str = "", estado: str = "", biblioteca_id: int | None = None, tipo_ubicacion: str = "", sala: str = "", estante: str = "") -> list[dict]:
        with self.database.session() as session:
            ultima = aliased(Location)
            ultima_ubicacion_id = (
                select(Location.id).where(Location.libro_id == Book.id)
                .order_by(desc(Location.fecha_ubicacion), desc(Location.id)).limit(1)
                .correlate(Book).scalar_subquery()
            )
            ultimo_movimiento_id = (
                select(Movement.id).where(Movement.libro_id == Book.id)
                .order_by(desc(Movement.fecha), desc(Movement.id)).limit(1)
                .correlate(Book).scalar_subquery()
            )
            movimiento_actual = aliased(Movement)
            query = (
                select(Book, ultima, Library.nombre, movimiento_actual).select_from(Book)
                .outerjoin(ultima, ultima.id == ultima_ubicacion_id)
                .outerjoin(Library, ultima.biblioteca_id == Library.id)
                .outerjoin(movimiento_actual, movimiento_actual.id == ultimo_movimiento_id)
                .where(Book.activo.is_(True))
            )
            if texto.strip():
                patron = f"%{texto.strip()}%"
                query = query.where((Book.titulo.ilike(patron)) | (Book.autor.ilike(patron)) | (Book.isbn.ilike(patron)) | (Book.cota.ilike(patron)) | (Book.numero_registro.ilike(patron)))
            if estado:
                query = query.where(Book.estado == estado)
            if biblioteca_id:
                query = query.where(ultima.biblioteca_id == biblioteca_id)
            if tipo_ubicacion:
                query = query.where(ultima.tipo_ubicacion == tipo_ubicacion)
            if sala.strip():
                query = query.where(ultima.sala.ilike(f"%{sala.strip()}%"))
            if estante.strip():
                query = query.where(ultima.estante.ilike(f"%{estante.strip()}%"))
            filas = session.execute(query.order_by(Book.titulo)).all()
            return [{
                "libro": libro,
                "tipo_ubicacion": ubicacion.tipo_ubicacion if ubicacion else "Sin ubicación",
                "biblioteca": nombre or "Central",
                "sala": ubicacion.sala if ubicacion else "",
                "estante": ubicacion.estante if ubicacion else "",
                "ultimo_movimiento": movimiento,
            } for libro, ubicacion, nombre, movimiento in filas]

    def listar_bibliotecas(self) -> list[Library]:
        with self.database.session() as session:
            return list(session.scalars(select(Library).where(Library.activa.is_(True)).order_by(Library.nombre)))

    def actualizar_ubicacion(self, libro_id: int, biblioteca_id: int, tipo_ubicacion: str, sala: str, estante: str, usuario_id: int | None) -> tuple[bool, str]:
        if tipo_ubicacion not in {"sala", "deposito"}:
            return False, "Seleccione una ubicación física válida."
        with self.database.session() as session:
            libro = session.get(Book, libro_id)
            biblioteca = session.get(Library, biblioteca_id)
            if libro is None or not libro.activo or biblioteca is None or not biblioteca.activa:
                return False, "El libro o la biblioteca seleccionada no están disponibles."
            anterior = session.scalar(select(Location).where(Location.libro_id == libro_id).order_by(desc(Location.fecha_ubicacion), desc(Location.id)).limit(1))
            origen = "Sin ubicación"
            if anterior:
                origen = f"{anterior.biblioteca.nombre if anterior.biblioteca else 'Central'} / {anterior.sala} / {anterior.estante}"
            sala = sala.strip()
            estante = estante.strip()
            session.add(Location(libro_id=libro_id, biblioteca_id=biblioteca.id, tipo_ubicacion=tipo_ubicacion, sala=sala, estante=estante))
            session.add(Movement(libro_id=libro_id, tipo_movimiento="ubicacion", origen=origen, destino=f"{biblioteca.nombre} / {sala} / {estante}", usuario_id=usuario_id, detalle="Ubicación física actualizada"))
        return True, "Ubicación actualizada."

    def historial(self, libro_id: int) -> list[Movement]:
        with self.database.session() as session:
            return list(session.scalars(select(Movement).where(Movement.libro_id == libro_id).order_by(desc(Movement.fecha), desc(Movement.id))))