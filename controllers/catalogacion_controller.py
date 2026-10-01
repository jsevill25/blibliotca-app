import re
import unicodedata

from sqlalchemy import select

from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Location, Movement


class CatalogacionController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def sugerir_cutter(self, autor: str) -> str:
        apellido = (autor.strip().split()[-1] if autor.strip() else "X")
        apellido = unicodedata.normalize("NFKD", apellido).encode("ascii", "ignore").decode().upper()
        letras = re.sub("[^A-Z]", "", apellido) or "X"
        numero = sum(ord(letra) for letra in letras) % 900 + 100
        return f"{letras[0]}{numero:03d}"

    def pendientes(self, texto: str = "") -> list[Book]:
        with self.database.session() as session:
            query = select(Book).where(Book.estado == "recibido", Book.activo.is_(True)).order_by(Book.fecha_ingreso, Book.id)
            if texto.strip():
                patron = f"%{texto.strip()}%"
                query = query.where((Book.titulo.ilike(patron)) | (Book.autor.ilike(patron)) | (Book.isbn.ilike(patron)))
            return list(session.scalars(query))

    def catalogar(self, libro_id: int, clasificacion: str, codigo_clasificacion: str, cutter: str, cota: str, usuario_id: int | None, permitir_cota_duplicada: bool = False) -> tuple[bool, str]:
        cota = cota.strip()
        codigo_clasificacion = codigo_clasificacion.strip()
        if clasificacion not in {"Dewey", "LC"} or not codigo_clasificacion or not cota:
            return False, "Seleccione Dewey o LC e indique el código de clasificación y la cota completa."
        with self.database.session() as session:
            libro = session.get(Book, libro_id)
            if libro is None or libro.estado != "recibido":
                return False, "Sólo se pueden catalogar libros recibidos."
            duplicada = session.scalar(select(Book.id).where(Book.cota == cota, Book.id != libro_id))
            if duplicada and not permitir_cota_duplicada:
                return False, "Ya existe esa cota; confirme si se trata de un multivolumen."
            central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
            libro.cota = cota
            libro.codigo_dewey = codigo_clasificacion if clasificacion == "Dewey" else ""
            libro.estado = "catalogado"
            session.add(Cataloging(
                libro_id=libro.id, clasificacion=clasificacion,
                codigo_clasificacion=codigo_clasificacion, cutter=cutter.strip(),
                cota_completa=cota, catalogado_por=usuario_id,
            ))
            session.add(Location(libro_id=libro.id, biblioteca_id=central.id if central else None, tipo_ubicacion="sala", sala="Catalogación"))
            session.add(Movement(libro_id=libro.id, tipo_movimiento="catalogacion", origen="Recepción", destino=cota, usuario_id=usuario_id, detalle="Catalogación completada"))
        return True, "Libro catalogado."