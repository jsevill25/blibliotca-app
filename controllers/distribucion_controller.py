from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from database.db_manager import DatabaseManager
from database.models import Book, BookStock, Library, Location, Movement, Package


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
                stock_central = session.scalar(select(BookStock).where(BookStock.libro_id == libro.id, BookStock.biblioteca_id == central.id)) if central else None
                stock_destino = session.scalar(select(BookStock).where(BookStock.libro_id == libro.id, BookStock.biblioteca_id == destino.id))
                cantidad_envio = max(1, min(libro.cantidad or 1, 1))
                if stock_central is not None:
                    stock_central.cantidad = max(0, stock_central.cantidad - cantidad_envio)
                    stock_central.actualizado_en = datetime.now()
                if stock_destino is None:
                    session.add(BookStock(libro_id=libro.id, biblioteca_id=destino.id, cantidad=cantidad_envio, actualizado_en=datetime.now()))
                else:
                    stock_destino.cantidad += cantidad_envio
                    stock_destino.actualizado_en = datetime.now()
                libro.cantidad = max(0, (libro.cantidad or 1) - cantidad_envio)
                libro.estado = "distribuido"
                session.add(Location(libro_id=libro.id, biblioteca_id=destino.id, tipo_ubicacion="biblioteca_distribucion"))
                session.add(Movement(
                    libro_id=libro.id, tipo_movimiento="distribucion",
                    origen=central.nombre if central else "Biblioteca Central", destino=destino.nombre,
                    usuario_id=usuario_id, detalle=f"Envío {paquete.codigo_envio}: cantidad {cantidad_envio}",
                ))
            codigo = paquete.codigo_envio
        return True, codigo

    def sugerir_genero_para_envio(self, libro_ids: list[int]) -> str:
        if not libro_ids:
            return ""
        with self.database.session() as session:
            libros = list(session.scalars(select(Book).where(Book.id.in_(libro_ids), Book.activo.is_(True))))
        if not libros:
            return ""
        conteos = {
            "Novela": 0, "Poesía": 0, "Teatro": 0, "Ensayo": 0,
            "Matemática": 0, "Tecnología": 0, "Historia": 0, "No ficción": 0,
        }
        for libro in libros:
            codigo = str(libro.codigo_dewey or "").strip()
            if codigo.startswith("861"):
                conteos["Poesía"] += 1
            elif codigo.startswith("862"):
                conteos["Teatro"] += 1
            elif codigo.startswith("863"):
                conteos["Novela"] += 1
            elif codigo.startswith("81"):
                conteos["Poesía"] += 1
            elif codigo.startswith("82"):
                conteos["Teatro"] += 1
            elif codigo.startswith("80"):
                conteos["Ensayo"] += 1
            elif codigo.startswith("51"):
                conteos["Matemática"] += 1
            elif codigo.startswith("60"):
                conteos["Tecnología"] += 1
            elif codigo.startswith("9"):
                conteos["Historia"] += 1
            else:
                conteos["No ficción"] += 1
        if not any(conteos.values()):
            return ""
        return max(conteos, key=conteos.get)

    def listar_bibliotecas(self) -> list[Library]:
        with self.database.session() as session:
            return list(session.scalars(select(Library).where(Library.activa.is_(True)).order_by(Library.nombre)))

    def obtener_envio(self, codigo: str) -> tuple[dict, list[dict]] | None:
        with self.database.session() as session:
            paquete = session.scalar(
                select(Package)
                .options(
                    joinedload(Package.biblioteca_destino),
                    selectinload(Package.libros).selectinload(Book.recepcion),
                )
                .where(Package.codigo_envio == codigo)
            )
            if paquete is None:
                return None
            datos_bulto = {
                "codigo_envio": paquete.codigo_envio,
                "destino": paquete.biblioteca_destino.nombre,
                "direccion": paquete.biblioteca_destino.direccion,
                "municipio": paquete.biblioteca_destino.municipio,
                "encargada": paquete.biblioteca_destino.encargado,
                "fecha": paquete.fecha_envio.strftime("%Y-%m-%d %H:%M"),
                "cantidad_libros": paquete.cantidad_libros,
                "cantidad_volumenes": sum(libro.numero_volumenes or 1 for libro in paquete.libros),
            }
            libros = [{
                "titulo": libro.titulo, "autor": libro.autor, "cota": libro.cota,
                "numero_registro": libro.numero_registro,
                "organismo": (
                    libro.recepcion.institucion_origen
                    or libro.recepcion.proveedor_nombre
                    or libro.recepcion.donante_nombre
                    if libro.recepcion else ""
                ),
                "procedencia": libro.procedencia,
                "numero_volumenes": libro.numero_volumenes,
                "precio_unitario": libro.precio_unitario,
            } for libro in paquete.libros]
            return datos_bulto, libros

    def listar_envios(self, limite: int = 100) -> list[dict]:
        with self.database.session() as session:
            paquetes = session.scalars(
                select(Package)
                .options(joinedload(Package.biblioteca_destino))
                .order_by(Package.fecha_envio.desc(), Package.id.desc())
                .limit(limite)
            )
            return [{
                "codigo_envio": paquete.codigo_envio,
                "destino": paquete.biblioteca_destino.nombre,
                "fecha": paquete.fecha_envio.strftime("%d/%m/%Y"),
            } for paquete in paquetes]
