from datetime import date, datetime, time, timedelta
import re
import unicodedata

from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.orm import aliased

from database.db_manager import DatabaseManager
from database.models import Book, BookStock, Cataloging, Library, Location, Package, package_books


class ReportesController:
    AREAS_MATRICIALES = (
        "000", "100", "200", "300", "400", "500", "600", "700", "800", "900",
        "Biografías", "Pub. Oficiales", "Pub. Periódicas", "No Bibliográfico",
    )

    def __init__(self, database: DatabaseManager):
        self.database = database

    def resumen_distribucion_areas(self) -> dict:
        with self.database.session() as session:
            ultima_ubicacion_id = (
                select(Location.id)
                .where(Location.libro_id == Book.id)
                .order_by(desc(Location.fecha_ubicacion), desc(Location.id))
                .limit(1)
                .correlate(Book)
                .scalar_subquery()
            )
            ubicacion_actual = aliased(Location)
            filas = session.execute(
                select(Book, Library.nombre)
                .select_from(Book)
                .outerjoin(ubicacion_actual, ubicacion_actual.id == ultima_ubicacion_id)
                .outerjoin(Library, Library.id == ubicacion_actual.biblioteca_id)
                .where(Book.activo.is_(True))
                .order_by(Library.nombre, Book.numero_registro)
            ).all()
            bibliotecas = list(session.scalars(select(Library).order_by(Library.nombre)))

        def normalizar(nombre: str) -> str:
            descompuesto = unicodedata.normalize("NFKD", nombre)
            texto = "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter)).casefold()
            if texto.strip().startswith("bic. nat. del libertador"):
                texto = texto.replace("bic. nat. del libertador", "biblioteca nacional del libertador", 1)
            return " ".join("".join(caracter if caracter.isalnum() else " " for caracter in texto).split())

        def coincide(nombre_oficial: str, nombre_registrado: str) -> bool:
            oficial = normalizar(nombre_oficial).split()
            registrado = normalizar(nombre_registrado).split()
            return bool(oficial) and len(oficial) <= len(registrado) and any(
                all(registrado[inicio + indice].startswith(token) for indice, token in enumerate(oficial))
                for inicio in range(len(registrado) - len(oficial) + 1)
            )

        from controllers.fichero_controller import FicheroController

        nombres_oficiales = list(FicheroController.BIBLIOTECAS_MATRIZ)
        bibliotecas_por_nombre = {}
        for nombre in nombres_oficiales:
            equivalentes = [registrada for registrada in bibliotecas if coincide(nombre, registrada.nombre)]
            nombre_visible = "Biblioteca Central 'Rómulo Gallegos'" if normalizar(nombre) == "romulo gallegos" else nombre
            bibliotecas_por_nombre[nombre_visible] = equivalentes[0] if equivalentes else None
        for biblioteca in bibliotecas:
            if not any(coincide(oficial, biblioteca.nombre) for oficial in nombres_oficiales):
                bibliotecas_por_nombre[biblioteca.nombre] = biblioteca
        bibliotecas_por_nombre["Sin ubicación"] = None

        acumulados = {}
        for nombre_visible in bibliotecas_por_nombre:
            acumulados[nombre_visible] = {
                area: {"T": 0, "V": 0} for area in self.AREAS_MATRICIALES
            }
            acumulados[nombre_visible]["Total"] = {"T": 0, "V": 0}
            acumulados[nombre_visible]["Total General"] = {"T": 0, "V": 0}

        nombre_actual_a_visible = {
            biblioteca.nombre: nombre_visible
            for nombre_visible, biblioteca in bibliotecas_por_nombre.items()
            if biblioteca is not None
        }
        areas_dewey = {f"{numero:03d}" for numero in range(0, 1000, 100)}
        for libro, biblioteca_actual in filas:
            sucursal = nombre_actual_a_visible.get(biblioteca_actual or "", "Sin ubicación")
            dew = re.match(r"^\s*(\d{1,3})(?:\.\d+)?", libro.codigo_dewey or "")
            numero_dewey = int(dew.group(1)) if dew else None
            if numero_dewey is None:
                categoria = None
            elif 920 <= numero_dewey <= 929:
                categoria = "Biografías"
            elif 50 <= numero_dewey <= 59:
                categoria = "Pub. Periódicas"
            else:
                categoria = f"{(numero_dewey // 100) * 100:03d}"
                if categoria not in self.AREAS_MATRICIALES:
                    categoria = "No Bibliográfico"

            titulos = 1
            volumenes = max(libro.numero_volumenes or 1, 1)
            if categoria is not None:
                valores = acumulados[sucursal][categoria]
                valores["T"] += titulos
                valores["V"] += volumenes
                if categoria in areas_dewey:
                    acumulados[sucursal]["Total"]["T"] += titulos
                    acumulados[sucursal]["Total"]["V"] += volumenes
            acumulados[sucursal]["Total General"]["T"] += titulos
            acumulados[sucursal]["Total General"]["V"] += volumenes

        totales_generales = {
            area: {
                metrica: sum(datos[area][metrica] for datos in acumulados.values())
                for metrica in ("T", "V")
            }
            for area in (*self.AREAS_MATRICIALES, "Total", "Total General")
        }
        return {
            "anio": date.today().year,
            "sucursales": [
                {
                    "biblioteca": nombre,
                    "municipio": biblioteca.municipio if biblioteca else "",
                    "categorias": cantidades,
                }
                for nombre, cantidades in acumulados.items()
                for biblioteca in (bibliotecas_por_nombre[nombre],)
            ],
            "totales_generales": totales_generales,
            "nota_clasificacion": (
                "Biografías se identifica con Dewey 920-929 y Pub. Periódicas con 050-059. "
                "La base actual no distingue publicaciones oficiales ni material no bibliográfico; "
                "los registros sin código Dewey cuentan en Total General, pero no se asignan a esas categorías."
            ),
        }

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

    def estadisticas_panel(self) -> dict:
        with self.database.session() as session:
            bibliotecas = session.execute(
                select(
                    Library.id,
                    Library.nombre,
                    Library.municipio,
                    func.count(func.distinct(case((BookStock.cantidad > 0, Book.id)))),
                    func.coalesce(
                        func.sum(case((and_(Book.id.is_not(None), BookStock.cantidad > 0), BookStock.cantidad), else_=0)),
                        0,
                    ),
                    func.count(func.distinct(case((and_(BookStock.cantidad > 0, Book.estado == "recibido"), Book.id)))),
                    func.count(func.distinct(case((and_(BookStock.cantidad > 0, Book.estado == "catalogado"), Book.id)))),
                    func.count(func.distinct(case((and_(BookStock.cantidad > 0, Book.estado == "distribuido"), Book.id)))),
                )
                .select_from(Library)
                .outerjoin(BookStock, BookStock.biblioteca_id == Library.id)
                .outerjoin(Book, (Book.id == BookStock.libro_id) & Book.activo.is_(True))
                .where(Library.activa.is_(True))
                .group_by(Library.id, Library.nombre, Library.municipio)
                .order_by(Library.nombre)
            ).all()
            libros = session.execute(
                select(
                    Book.numero_registro,
                    Book.titulo,
                    Book.autor,
                    Book.estado,
                    Book.fecha_ingreso,
                    Book.cantidad,
                    func.coalesce(func.sum(BookStock.cantidad), 0),
                )
                .outerjoin(BookStock, BookStock.libro_id == Book.id)
                .where(Book.activo.is_(True))
                .group_by(Book.id)
                .order_by(Book.fecha_ingreso.desc(), Book.id.desc())
                .limit(12)
            ).all()

        return {
            "bibliotecas": [
                {
                    "id": fila[0],
                    "nombre": fila[1],
                    "municipio": fila[2],
                    "registros": fila[3],
                    "ejemplares": fila[4],
                    "recibidos": fila[5],
                    "catalogados": fila[6],
                    "distribuidos": fila[7],
                }
                for fila in bibliotecas
            ],
            "libros": [
                {
                    "registro": fila[0],
                    "titulo": fila[1],
                    "autor": fila[2],
                    "estado": fila[3],
                    "fecha": fila[4].strftime("%d/%m/%Y"),
                    "cantidad_registrada": fila[5],
                    "ejemplares_en_bibliotecas": fila[6],
                }
                for fila in libros
            ],
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