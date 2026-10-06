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

    def generar_cota_automatica(self, libro_id: int, codigo_clasificacion: str, datos: dict) -> dict:
        with self.database.session() as session:
            libro = session.get(Book, libro_id)
            if libro is None or libro.estado != "recibido":
                raise ValueError("Sólo se pueden generar cotas para libros recibidos.")

            genero = self._normalizar(datos.get("genero", "No ficción"))
            seccion = self._normalizar(datos.get("seccion", ""))
            material = self._normalizar(datos.get("material", ""))
            paginas = libro.paginas
            alto = self._numero(datos.get("alto"))
            ancho = self._numero(datos.get("ancho"))
            prefijo = ""
            if paginas is not None and paginas < 50:
                prefijo = "Foll."
            elif (alto is not None and alto > 30) or (ancho is not None and ancho > 30):
                prefijo = "F"
            elif seccion == "referencia":
                prefijo = "R"
            elif seccion == "infantil":
                prefijo = "X"
            elif seccion == "juvenil":
                prefijo = "J"
            elif material == "musica escrita":
                prefijo = "M"

            codigo = str(codigo_clasificacion or "").strip()
            if genero == "biografia individual":
                clasificacion = "B"
            elif genero == "biografia colectiva":
                clasificacion = "B2"
            elif genero in {"novela", "poesia", "teatro", "ensayo"}:
                letras = {"novela": "N", "poesia": "P", "teatro": "T", "ensayo": "E"}
                venezolana = self._normalizar(datos.get("nacionalidad", "")) in {"venezolana", "venezolano", "venezuela"}
                clasificacion = f"{letras[genero]}{'V' if venezolana else ''}"
            else:
                clasificacion = self._dewey_limitado(codigo)

            if libro.anio is None:
                raise ValueError("Indique el año de publicación antes de generar la cota.")

            autores = str(libro.autor or "").strip()
            nombre_biografiado = str(datos.get("biografiado", "")).strip()
            cantidad_autores = self._numero_autores(datos.get("numero_autores"), autores)
            if clasificacion in {"B", "B2"}:
                base = self._apellido(nombre_biografiado)
                if not base:
                    raise ValueError("Indique el personaje biografiado para generar el Cutter.")
            elif not autores or cantidad_autores >= 4:
                base = self._primera_palabra_titulo(libro.titulo)
            else:
                base = self._apellido(self._primer_autor(autores))
            cutter = self.sugerir_cutter(base)

            lineas = [linea for linea in (prefijo, clasificacion, cutter, str(libro.anio)) if linea]
            tomo = str(datos.get("tomo", "")).strip()
            if tomo:
                tipo_tomo = "t" if self._normalizar(datos.get("tipo_tomo", "v")) == "t" else "v"
                lineas.append(f"{tipo_tomo}.{tomo}")
            cota_base = "\n".join(lineas)

            usados = set()
            for cota_existente in session.scalars(select(Book.cota).where(Book.cota != "")):
                partes = str(cota_existente).splitlines()
                ejemplar = re.fullmatch(r"ej\.(\d+)", partes[-1].strip(), re.IGNORECASE) if partes else None
                if ejemplar:
                    partes.pop()
                if "\n".join(partes) == cota_base:
                    usados.add(int(ejemplar.group(1)) if ejemplar else 1)
            siguiente = 2
            while siguiente in usados:
                siguiente += 1
            cota = cota_base if not usados else f"{cota_base}\nej.{siguiente}"
            return {"cota": cota, "cutter": cutter, "clasificacion": clasificacion}

    @staticmethod
    def _normalizar(valor) -> str:
        texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode().lower()
        return re.sub(r"\s+", " ", texto).strip()

    @staticmethod
    def _numero(valor) -> float | None:
        try:
            return float(str(valor).replace(",", ".")) if valor not in (None, "") else None
        except ValueError:
            return None

    @staticmethod
    def _dewey_limitado(codigo: str) -> str:
        if not re.fullmatch(r"\d{1,3}(?:\.\d+)?", codigo):
            raise ValueError("Para generar automáticamente una obra no ficcional, indique un número Dewey válido.")
        entero, separador, decimales = codigo.partition(".")
        return entero + (separador + decimales[:5] if separador else "")

    @staticmethod
    def _apellido(nombre: str) -> str:
        nombre = nombre.strip()
        if "," in nombre:
            return nombre.split(",", 1)[0].strip()
        return nombre.split()[-1] if nombre else ""

    @staticmethod
    def _primer_autor(autores: str) -> str:
        return re.split(r"\s*(?:;|\s+y\s+|\s+and\s+)\s*", autores, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    @staticmethod
    def _cantidad_autores(autores: str) -> int:
        return len(re.split(r"\s*(?:;|\s+y\s+|\s+and\s+)\s*", autores, flags=re.IGNORECASE))

    @classmethod
    def _numero_autores(cls, valor, autores: str) -> int:
        try:
            cantidad = int(valor)
            return cantidad if cantidad > 0 else cls._cantidad_autores(autores)
        except (TypeError, ValueError):
            return cls._cantidad_autores(autores)

    @staticmethod
    def _primera_palabra_titulo(titulo: str) -> str:
        articulos = {"el", "la", "los", "las", "un", "una", "unos", "unas"}
        palabras = re.findall(r"[\wÀ-ÿ]+", titulo)
        while palabras and CatalogacionController._normalizar(palabras[0]) in articulos:
            palabras.pop(0)
        return palabras[0] if palabras else "X"

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