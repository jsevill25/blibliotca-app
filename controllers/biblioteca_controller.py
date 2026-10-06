from sqlalchemy import select

from database.db_manager import DatabaseManager
from database.models import Library


class BibliotecaController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def listar(self, incluir_inactivas: bool = False) -> list[Library]:
        with self.database.session() as session:
            query = select(Library).order_by(Library.nombre)
            if not incluir_inactivas:
                query = query.where(Library.activa.is_(True))
            return list(session.scalars(query))

    def crear(self, nombre: str, direccion: str = "", encargado: str = "", telefono: str = "", email: str = "", municipio: str = "") -> tuple[bool, str]:
        nombre = nombre.strip()
        if not nombre or nombre == "Biblioteca Central Rómulo Gallegos":
            return False, "Indique un nombre válido para la sucursal."
        with self.database.session() as session:
            if session.scalar(select(Library.id).where(Library.nombre == nombre)):
                return False, "Ya existe una biblioteca con ese nombre."
            session.add(Library(
                nombre=nombre, direccion=direccion.strip(), municipio=municipio.strip(),
                encargado=encargado.strip(), telefono=telefono.strip(), email=email.strip(),
            ))
        return True, "Sucursal registrada."

    def desactivar(self, library_id: int) -> tuple[bool, str]:
        with self.database.session() as session:
            library = session.get(Library, library_id)
            if library is None:
                return False, "No se encontró la biblioteca."
            if library.nombre == "Biblioteca Central Rómulo Gallegos":
                return False, "La biblioteca central no se puede desactivar."
            library.activa = False
        return True, "Biblioteca desactivada."