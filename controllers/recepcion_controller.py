from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.db_manager import DatabaseManager
from database.models import Book, Library, Location, Movement, Reception


class RecepcionController:
    PROCEDENCIAS = {"donacion", "compra", "biblioteca_nacional"}

    def __init__(self, database: DatabaseManager):
        self.database = database

    def registrar(self, datos: dict, usuario_id: int | None) -> tuple[bool, str]:
        titulo = str(datos.get("titulo", "")).strip()
        procedencia = str(datos.get("procedencia", "")).strip()
        if not titulo or procedencia not in self.PROCEDENCIAS:
            return False, "El título y una procedencia válida son obligatorios."
        try:
            anio = int(datos["anio"]) if datos.get("anio") not in (None, "") else None
            paginas = int(datos["paginas"]) if datos.get("paginas") not in (None, "") else None
        except (TypeError, ValueError):
            return False, "Año y páginas deben ser números enteros."
        if anio is not None and not 0 < anio <= date.today().year + 1:
            return False, "El año de publicación no es válido."
        if paginas is not None and paginas <= 0:
            return False, "El número de páginas debe ser mayor que cero."

        with self.database.session() as session:
            central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
            if central is None:
                return False, "No está registrada la biblioteca central."
            prefijo = f"REG-{date.today().year}-"
            ultimo = session.scalar(select(Book.numero_registro).where(Book.numero_registro.like(f"{prefijo}%")).order_by(Book.numero_registro.desc()).limit(1))
            secuencia = int(ultimo.rsplit("-", 1)[1]) + 1 if ultimo else 1
            libro = Book(
                titulo=titulo, autor=str(datos.get("autor", "")).strip(),
                editorial=str(datos.get("editorial", "")).strip(), anio=anio,
                isbn=str(datos.get("isbn", "")).strip(), edicion=str(datos.get("edicion", "")).strip(),
                idioma=str(datos.get("idioma", "Español")).strip() or "Español", paginas=paginas,
                procedencia=procedencia, procedencia_detalle=str(datos.get("procedencia_detalle", "")).strip(),
                fecha_ingreso=date.today(), numero_registro=f"{prefijo}{secuencia:05d}",
                observaciones=str(datos.get("observaciones", "")).strip(), estado="recibido",
            )
            session.add(libro)
            session.flush()
            session.add(Reception(
                libro_id=libro.id, tipo_ingreso=procedencia,
                donante_nombre=str(datos.get("donante_nombre", "")).strip(),
                proveedor_nombre=str(datos.get("proveedor_nombre", "")).strip(),
                institucion_origen=str(datos.get("institucion_origen", "")).strip(),
                observaciones=libro.observaciones, registrado_por=usuario_id,
            ))
            session.add(Location(libro_id=libro.id, biblioteca_id=central.id, tipo_ubicacion="deposito", sala="Recepción"))
            session.add(Movement(libro_id=libro.id, tipo_movimiento="recepcion", destino=central.nombre, usuario_id=usuario_id, detalle=f"Ingreso {libro.numero_registro}"))
            numero_registro = libro.numero_registro
        return True, numero_registro

    def listar(self, texto: str = "", procedencia: str = "", inicio: date | None = None, fin: date | None = None) -> list[Book]:
        with self.database.session() as session:
            query = select(Book).options(joinedload(Book.recepcion)).order_by(Book.fecha_ingreso.desc(), Book.id.desc())
            if texto.strip():
                patron = f"%{texto.strip()}%"
                query = query.where((Book.titulo.ilike(patron)) | (Book.autor.ilike(patron)) | (Book.isbn.ilike(patron)))
            if procedencia:
                query = query.where(Book.procedencia == procedencia)
            if inicio:
                query = query.where(Book.fecha_ingreso >= inicio)
            if fin:
                query = query.where(Book.fecha_ingreso <= fin)
            return list(session.scalars(query).unique())

    def editar(self, libro_id: int, datos: dict, usuario_id: int | None) -> tuple[bool, str]:
        with self.database.session() as session:
            libro = session.get(Book, libro_id)
            if libro is None or libro.recepcion is None:
                return False, "No se encontró el registro de recepción."
            if libro.estado != "recibido":
                return False, "La recepción sólo puede editarse antes de catalogar el libro."
            if not str(datos.get("titulo", "")).strip():
                return False, "El título es obligatorio."
            procedencia = datos.get("procedencia", libro.procedencia)
            if procedencia not in self.PROCEDENCIAS:
                return False, "Seleccione una procedencia válida."
            try:
                anio = int(datos["anio"]) if datos.get("anio") not in (None, "") else None
                paginas = int(datos["paginas"]) if datos.get("paginas") not in (None, "") else None
            except (TypeError, ValueError):
                return False, "Año y páginas deben ser números enteros."
            libro.anio = anio
            libro.paginas = paginas
            libro.procedencia = procedencia
            if anio is not None and not 0 < anio <= date.today().year + 1:
                return False, "El año de publicación no es válido."
            if paginas is not None and paginas <= 0:
                return False, "El número de páginas debe ser mayor que cero."
            for campo in ("titulo", "autor", "editorial", "isbn", "edicion", "idioma", "procedencia_detalle", "observaciones"):
                if campo in datos:
                    setattr(libro, campo, str(datos[campo]).strip())
            libro.recepcion.modificado = True
            libro.recepcion.modificado_por = usuario_id
            libro.recepcion.fecha_modificacion = datetime.now()
            libro.recepcion.tipo_ingreso = procedencia
            libro.recepcion.donante_nombre = str(datos.get("donante_nombre", "")).strip()
            libro.recepcion.proveedor_nombre = str(datos.get("proveedor_nombre", "")).strip()
            libro.recepcion.institucion_origen = str(datos.get("institucion_origen", "")).strip()
        return True, "Recepción actualizada."