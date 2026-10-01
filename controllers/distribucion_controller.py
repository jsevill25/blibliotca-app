from datetime import date, datetime

from sqlalchemy import select

from database.db_manager import DatabaseManager
from database.models import Book, Library, Location, Movement, Package


class DistribucionController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def libros_disponibles(self, texto: str = "") -> list[Book]:
        with self.database.session() as session:
            query = select(Book).where(Book.estado == "catalogado", Book.activo.is_(True)).order_by(Book.titulo)
            if texto.strip():
                patron = f"%{texto.strip()}%"
                query = query.where((Book.titulo.ilike(patron)) | (Book.autor.ilike(patron)) | (Book.cota.ilike(patron)))
            return list(session.scalars(query))

    def crear_bulto(self, biblioteca_id: int, libro_ids: list[int], usuario_id: int | None, genero: str = "", observaciones: str = "") -> tuple[bool, str]:
        ids = list(dict.fromkeys(libro_ids))
        if not ids:
            return False, "Seleccione al menos un libro."
        with self.database.session() as session:
            destino = session.get(Library, biblioteca_id)
            if destino is None or not destino.activa:
                return False, "La biblioteca destino no existe o está inactiva."
            central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
            libros = list(session.scalars(select(Book).where(Book.id.in_(ids))))
            if len(libros) != len(ids) or any(libro.estado != "catalogado" for libro in libros):
                return False, "Todos los libros deben existir y estar catalogados."
            prefijo = f"ENV-{date.today():%Y%m%d}-"
            ultimo = session.scalar(select(Package.codigo_envio).where(Package.codigo_envio.like(f"{prefijo}%")).order_by(Package.codigo_envio.desc()).limit(1))
            secuencia = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
            paquete = Package(
                codigo_envio=f"{prefijo}{secuencia:03d}", biblioteca_destino_id=destino.id,
                fecha_envio=datetime.now(), cantidad_libros=len(libros), genero=genero.strip(),
                observaciones=observaciones.strip(), creado_por=usuario_id, libros=libros,
            )
            session.add(paquete)
            for libro in libros:
                libro.estado = "distribuido"
                session.add(Location(libro_id=libro.id, biblioteca_id=destino.id, tipo_ubicacion="biblioteca_distribucion"))
                session.add(Movement(
                    libro_id=libro.id, tipo_movimiento="distribucion",
                    origen=central.nombre if central else "Biblioteca Central", destino=destino.nombre,
                    usuario_id=usuario_id, detalle=f"Envío {paquete.codigo_envio}",
                ))
            codigo = paquete.codigo_envio
        return True, codigo

    def listar_bibliotecas(self) -> list[Library]:
        with self.database.session() as session:
            return list(session.scalars(select(Library).where(Library.activa.is_(True)).order_by(Library.nombre)))

    def obtener_envio(self, codigo: str) -> tuple[dict, list[dict]] | None:
        with self.database.session() as session:
            paquete = session.scalar(select(Package).where(Package.codigo_envio == codigo))
            if paquete is None:
                return None
            datos_bulto = {
                "codigo_envio": paquete.codigo_envio,
                "destino": paquete.biblioteca_destino.nombre,
                "fecha": paquete.fecha_envio.strftime("%Y-%m-%d %H:%M"),
                "cantidad_libros": paquete.cantidad_libros,
            }
            libros = [{
                "titulo": libro.titulo, "autor": libro.autor, "cota": libro.cota,
                "numero_registro": libro.numero_registro,
            } for libro in paquete.libros]
            return datos_bulto, libros