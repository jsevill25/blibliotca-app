from collections import defaultdict
import unicodedata

from sqlalchemy import select

from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Location


class FicheroController:
    BIBLIOTECAS_MATRIZ = (
        "Rómulo Gallegos", "Bolivariana", "Carmelo Castillo", "José Luis Arismestique",
        "Juan Bautista González", "Mercedes Vargas C.", "Héctor Arias", "La Paragua",
        "Bic. Nat. del Libertador", "Miguel de Cervantes", "Andrés Eloy B.",
        "Mario Briceño I.", "Ana Emilia Delón", "Carlos Rodríguez J.", "Juan Fernández",
        "Juan Vicente González", "Menca de Leoni", "Viola de Billings",
        "Horacio Cabrera S.", "María C. de Rosales", "Lucas Fernández", "Andrés Bello",
        "Alejandro Vargas", "Hortensia de Pinto", "José M. Siso Martínez", "Simón Rodríguez",
    )
    AREAS_DEWEY = {
        0: "Generalidades",
        1: "Filosofía y psicología",
        2: "Religión",
        3: "Ciencias sociales",
        4: "Lenguas",
        5: "Ciencias naturales y matemáticas",
        6: "Tecnología y ciencias aplicadas",
        7: "Artes y recreación",
        8: "Literatura",
        9: "Historia y geografía",
    }
    AREAS_LC = {
        "A": "Generalidades",
        "B": "Filosofía y religión",
        "C": "Historia",
        "D": "Historia",
        "E": "Historia de América",
        "F": "Historia de América",
        "G": "Geografía",
        "H": "Ciencias sociales",
        "J": "Ciencias políticas",
        "K": "Derecho",
        "L": "Educación",
        "M": "Música",
        "N": "Artes",
        "P": "Lengua y literatura",
        "Q": "Ciencias",
        "R": "Medicina",
        "S": "Agricultura",
        "T": "Tecnología",
        "U": "Ciencia militar",
        "V": "Ciencia naval",
        "Z": "Bibliografía y bibliotecología",
    }

    def __init__(self, database: DatabaseManager):
        self.database = database

    def buscar(self, texto: str = "") -> list[dict]:
        with self.database.session() as session:
            query = (
                select(Book, Cataloging)
                .outerjoin(Cataloging, Cataloging.libro_id == Book.id)
                .where(Book.activo.is_(True), Book.estado == "catalogado")
                .order_by(Book.titulo, Book.id)
            )
            if texto.strip():
                patron = f"%{texto.strip()}%"
                query = query.where(
                    Book.titulo.ilike(patron)
                    | Book.autor.ilike(patron)
                    | Book.isbn.ilike(patron)
                    | Book.cota.ilike(patron)
                    | Book.numero_registro.ilike(patron)
                )
            return [self._ficha(libro, catalogacion) for libro, catalogacion in session.execute(query)]

    def resumen_inventario(self) -> list[dict]:
        with self.database.session() as session:
            filas = session.execute(
                select(Book, Cataloging)
                .outerjoin(Cataloging, Cataloging.libro_id == Book.id)
                .where(Book.activo.is_(True))
                .order_by(Book.titulo, Book.id)
            ).all()

        resumen = defaultdict(lambda: {"catalogados": 0, "pendientes": 0, "total": 0})
        for libro, catalogacion in filas:
            sistema = catalogacion.clasificacion if catalogacion else "Sin clasificar"
            area = self._area_tematica(libro.codigo_dewey, sistema, catalogacion.codigo_clasificacion if catalogacion else "")
            grupo = resumen[(area, sistema)]
            grupo["total"] += 1
            grupo["catalogados" if libro.estado == "catalogado" else "pendientes"] += 1

        return [
            {"area": area, "sistema": sistema, **cantidades}
            for (area, sistema), cantidades in sorted(resumen.items())
        ]

    @staticmethod
    def normalizar_nombre(nombre: str) -> str:
        sin_acentos = unicodedata.normalize("NFKD", nombre)
        texto = "".join(caracter for caracter in sin_acentos if not unicodedata.combining(caracter)).casefold()
        if texto.strip().startswith("bic. nat. del libertador"):
            texto = texto.replace("bic. nat. del libertador", "biblioteca nacional del libertador", 1)
        return " ".join("".join(caracter if caracter.isalnum() else " " for caracter in texto).split())

    @classmethod
    def bibliotecas_para_matriz(cls, bibliotecas: list[Library]) -> list[str]:
        nombres = list(cls.BIBLIOTECAS_MATRIZ)
        extras = sorted(
            {
                biblioteca.nombre for biblioteca in bibliotecas
                if not any(
                    cls._coincide(nombre, biblioteca.nombre)
                    for nombre in cls.BIBLIOTECAS_MATRIZ
                )
            },
            key=str.casefold,
        )
        nombres.extend(extras)
        return nombres

    @classmethod
    def _coincide(cls, nombre_oficial: str, nombre_registrado: str) -> bool:
        buscado = cls.normalizar_nombre(nombre_oficial).split()
        registrado = cls.normalizar_nombre(nombre_registrado).split()
        if not buscado or len(buscado) > len(registrado):
            return False
        return any(
            all(registrado[inicio + indice].startswith(token) for indice, token in enumerate(buscado))
            for inicio in range(len(registrado) - len(buscado) + 1)
        )

    def obtener_matriz_sucursales(self, libro_id: int) -> dict | None:
        with self.database.session() as session:
            libro = session.get(Book, libro_id)
            if libro is None or not libro.activo:
                return None
            ultima_ubicacion_id = (
                select(Location.id)
                .where(Location.libro_id == libro.id)
                .order_by(Location.fecha_ubicacion.desc(), Location.id.desc())
                .limit(1)
                .correlate(Book)
                .scalar_subquery()
            )
            ubicacion = session.scalar(
                select(Location)
                .where(Location.id == ultima_ubicacion_id)
            )
            bibliotecas = list(session.scalars(select(Library).order_by(Library.nombre)))
            nombres = self.bibliotecas_para_matriz(bibliotecas)
            filas = []
            for nombre in nombres:
                coincidencias = [
                    registro for registro in bibliotecas
                    if self._coincide(nombre, registro.nombre)
                ]
                biblioteca = next(
                    (registro for registro in coincidencias if ubicacion and registro.id == ubicacion.biblioteca_id),
                    next((registro for registro in coincidencias if self.normalizar_nombre(registro.nombre) == self.normalizar_nombre(nombre)), None),
                )
                registrada = bool(
                    libro.activo
                    and ubicacion is not None
                    and biblioteca is not None
                    and ubicacion.biblioteca_id == biblioteca.id
                )
                prestamo = registrada and libro.estado == "prestado"
                disponible = registrada and libro.estado in {"catalogado", "distribuido"}
                filas.append({
                    "biblioteca": nombre,
                    "ingreso": registrada,
                    "disponibilidad": disponible,
                    "prestamo": prestamo,
                })

            return {
                "titulo": libro.titulo,
                "autor": libro.autor,
                "numero_registro": libro.numero_registro,
                "cota": libro.cota,
                "anio": libro.anio,
                "estado": libro.estado,
                "biblioteca_actual": ubicacion.biblioteca.nombre if ubicacion and ubicacion.biblioteca else "",
                "filas": filas,
            }

    @staticmethod
    def _area_tematica(codigo_dewey: str, sistema: str, codigo_clasificacion: str) -> str:
        if sistema == "Dewey":
            try:
                centena = int(codigo_dewey.strip().split(".", 1)[0]) // 100
                return FicheroController.AREAS_DEWEY[centena]
            except (AttributeError, ValueError, KeyError):
                return "Sin área temática"
        if sistema == "LC" and codigo_clasificacion.strip():
            letra = codigo_clasificacion.strip()[0].upper()
            return FicheroController.AREAS_LC.get(letra, "Sin área temática")
        return "Sin clasificar"

    @staticmethod
    def _ficha(libro: Book, catalogacion: Cataloging | None) -> dict:
        return {
            "id": libro.id,
            "titulo": libro.titulo,
            "autor": libro.autor,
            "editorial": libro.editorial,
            "anio": libro.anio,
            "edicion": libro.edicion,
            "paginas": libro.paginas,
            "idioma": libro.idioma,
            "isbn": libro.isbn,
            "cota": libro.cota,
            "codigo_dewey": libro.codigo_dewey,
            "sistema": catalogacion.clasificacion if catalogacion else "",
            "codigo_clasificacion": catalogacion.codigo_clasificacion if catalogacion else "",
            "area": FicheroController._area_tematica(
                libro.codigo_dewey,
                catalogacion.clasificacion if catalogacion else "",
                catalogacion.codigo_clasificacion if catalogacion else "",
            ),
            "numero_registro": libro.numero_registro,
        }