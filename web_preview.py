import argparse
import json
import os
import secrets
import tempfile
import webbrowser
from datetime import date
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sqlalchemy import select

from config import DATABASE_PATH
from controllers.auth_controller import AuthController
from controllers.backup_controller import BackupController
from controllers.biblioteca_controller import BibliotecaController
from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
from controllers.fichero_controller import FicheroController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from controllers.ubicacion_controller import UbicacionController
from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Package, User
from services.excel_service import ExcelService
from services.audit_service import AuditService
from services.pdf_service import PDFService


WEB_DIR = Path(__file__).resolve().parent / "web"
DEMO_DATABASE_PATH = Path(tempfile.gettempdir()) / "biblioteca-central-web-demo.sqlite3"


def seed_demo_catalog(database: DatabaseManager) -> None:
    muestras = [
        ("Relatos del río grande", "Marina Solís", "Ediciones del Parque", 2022, "978-0000000101", 184, "863.6", "S684r", "Dewey", "863.6"),
        ("Cartografía de los pueblos del Caribe", "Tomás Rivas", "Horizonte Editorial", 2021, "978-0000000102", 236, "", "R618c", "LC", "G155.C27"),
        ("Botánica para jardines escolares", "Elena Paredes", "Aula Abierta", 2020, "978-0000000103", 198, "581", "P227b", "Dewey", "581"),
        ("Introducción a la energía solar", "Gabriel Mora", "Taller Científico", 2023, "978-0000000104", 212, "621.47", "M827i", "Dewey", "621.47"),
        ("Voces y lenguas de la montaña", "Irene Campos", "Casa de Letras", 2019, "978-0000000105", 164, "498", "C198v", "Dewey", "498"),
        ("Memoria de una ciudad portuaria", "Luis Acosta", "Archivo Vivo", 2018, "978-0000000106", 275, "972.9", "A185m", "Dewey", "972.9"),
        ("Cuaderno de música popular", "Rafael Medina", "Son del Sur", 2024, "978-0000000107", 142, "", "M491c", "LC", "M125"),
        ("Guía práctica de catalogación", "Nora Fuentes", "Biblioteca Abierta", 2022, "978-0000000108", 128, "025.3", "F954g", "Dewey", "025.3"),
    ]
    with database.session() as session:
        if session.scalar(select(Library.id).where(Library.nombre == "Biblioteca Sucursal Norte")) is None:
            session.add(Library(
                nombre="Biblioteca Sucursal Norte", direccion="Av. Principal, edificio cultural",
                encargado="Equipo de prueba", telefono="000-000-0000", email="sucursal@example.test",
            ))
        if session.scalar(select(Book.id).limit(1)) is not None:
            return
        for indice, muestra in enumerate(muestras, start=1):
            titulo, autor, editorial, anio, isbn, paginas, dewey, cutter, sistema, codigo = muestra
            cota = f"{codigo}\n{cutter}\n{anio}"
            libro = Book(
                titulo=titulo, autor=autor, editorial=editorial, anio=anio, isbn=isbn,
                edicion="Primera edición", idioma="Español", paginas=paginas,
                procedencia="donacion", estado="catalogado", cota=cota,
                codigo_dewey=dewey, numero_registro=f"REG-2026-{indice:05d}",
            )
            session.add(libro)
            session.flush()
            session.add(Cataloging(
                libro_id=libro.id, clasificacion=sistema,
                codigo_clasificacion=codigo, cota_completa=cota, cutter=cutter,
            ))
        session.add(Book(
            titulo="Manual de conservación de colecciones", autor="Clara Benítez",
            editorial="Ediciones del Parque", anio=2025, isbn="978-0000000109",
            edicion="Primera edición", idioma="Español", paginas=176,
            procedencia="compra", estado="recibido",
            numero_registro="REG-2026-00009",
        ))


class PreviewHandler(BaseHTTPRequestHandler):
    database: DatabaseManager
    demo_mode = False
    session_store: dict[str, int] = {}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._send_file("index.html", "text/html; charset=utf-8")
            return
        if parsed.path in {"/styles.css", "/app.js"}:
            content_type = "text/css; charset=utf-8" if parsed.path.endswith(".css") else "text/javascript; charset=utf-8"
            self._send_file(parsed.path.lstrip("/"), content_type)
            return
        if parsed.path == "/api/session":
            user = self._current_user()
            payload = self._user_payload(user) if user else {"authenticated": False}
            payload["demo"] = self.demo_mode
            self._send_json(payload)
            return
        if parsed.path.startswith("/api/"):
            user = self._current_user()
            if user is None:
                self._send_json({"error": "Inicie sesión para continuar."}, 401)
                return
            if not AuthController(self.database).acceso_operativo_permitido(user.id):
                self._send_json({"error": "Cambie su contraseña antes de utilizar el sistema."}, 403)
                return
        controller = FicheroController(self.database)
        if parsed.path == "/api/books":
            texto = parse_qs(parsed.query).get("q", [""])[0]
            self._send_json(controller.buscar(texto))
            return
        if parsed.path == "/api/inventory":
            self._send_json(controller.resumen_inventario())
            return
        if parsed.path == "/api/summary":
            grupos = controller.resumen_inventario()
            self._send_json({
                "total": sum(grupo["total"] for grupo in grupos),
                "catalogados": sum(grupo["catalogados"] for grupo in grupos),
                "pendientes": sum(grupo["pendientes"] for grupo in grupos),
                "demo": self.demo_mode,
            })
            return
        if parsed.path == "/api/dashboard":
            self._send_json({
                "summary": ReportesController(self.database).resumen(),
                "inventory": controller.resumen_inventario(),
            })
            return
        query = parse_qs(parsed.query)
        if parsed.path == "/api/recepcion":
            libros = RecepcionController(self.database).listar(query.get("q", [""])[0])
            self._send_json([self._book_data(libro) for libro in libros])
            return
        if parsed.path == "/api/catalogacion":
            libros = CatalogacionController(self.database).pendientes(query.get("q", [""])[0])
            self._send_json([self._book_data(libro) for libro in libros])
            return
        if parsed.path == "/api/distribucion":
            libros = DistribucionController(self.database).libros_disponibles(query.get("q", [""])[0])
            self._send_json({
                "books": [self._book_data(libro) for libro in libros],
                "libraries": self._libraries(), "shipments": self._shipments(),
            })
            return
        if parsed.path == "/api/ubicacion":
            filas = UbicacionController(self.database).buscar(
                texto=query.get("q", [""])[0], estado=query.get("estado", [""])[0],
                biblioteca_id=self._optional_int(query.get("biblioteca", [""])[0]),
            )
            self._send_json([{
                **self._book_data(fila["libro"]), "biblioteca": fila["biblioteca"],
                "tipo_ubicacion": fila["tipo_ubicacion"], "sala": fila["sala"],
                "estante": fila["estante"],
                "ultimo_movimiento": fila["ultimo_movimiento"].tipo_movimiento if fila["ultimo_movimiento"] else "Sin movimientos",
            } for fila in filas])
            return
        if parsed.path == "/api/history":
            libro_id = self._optional_int(query.get("id", [""])[0])
            if libro_id is None:
                self._send_json({"error": "Indique un libro válido."}, 400)
                return
            movimientos = UbicacionController(self.database).historial(libro_id)
            self._send_json([{
                "fecha": movimiento.fecha.isoformat(sep=" ", timespec="minutes"),
                "tipo": movimiento.tipo_movimiento, "origen": movimiento.origen,
                "destino": movimiento.destino, "detalle": movimiento.detalle,
            } for movimiento in movimientos])
            return
        if parsed.path == "/api/libraries":
            self._send_json(self._libraries(include_inactive=True))
            return
        if parsed.path == "/api/reportes":
            try:
                inicio = self._optional_date(query.get("desde", [""])[0])
                fin = self._optional_date(query.get("hasta", [""])[0])
            except ValueError:
                self._send_json({"error": "Use fechas con formato AAAA-MM-DD."}, 400)
                return
            reportes = ReportesController(self.database)
            self._send_json({
                "summary": reportes.resumen(inicio, fin),
                "inventory": reportes.inventario(inicio, fin),
            })
            return
        if parsed.path == "/api/users":
            if user.rol != "admin":
                self._send_json({"error": "Esta sección requiere rol administrador."}, 403)
                return
            usuarios = AuthController(self.database).listar_usuarios(user.id)
            self._send_json([{
                "id": user.id, "username": user.username, "nombre": user.nombre_completo,
                "rol": user.rol, "activo": user.activo,
            } for user in usuarios])
            return
        self.send_error(404, "Recurso no encontrado")

    def do_POST(self) -> None:
        try:
            datos = self._read_json()
            ruta = urlparse(self.path).path
            if ruta == "/api/login":
                valido, resultado = AuthController(self.database).autenticar(
                    str(datos.get("username", "")), str(datos.get("password", "")),
                    origen=self.client_address[0],
                )
                if not valido:
                    self._send_json({"error": str(resultado)}, 401)
                    return
                token = secrets.token_urlsafe(32)
                self.session_store[token] = resultado.id
                payload = self._user_payload(resultado)
                payload["demo"] = self.demo_mode
                cookie = self._session_cookie(token)
                self._send_json(payload, extra_headers=[(
                    "Set-Cookie", cookie,
                )])
                return
            if ruta == "/api/logout":
                token = self._session_token()
                if token:
                    self.session_store.pop(token, None)
                self._send_json({"ok": True}, extra_headers=[(
                    "Set-Cookie", self._session_cookie("", expired=True),
                )])
                return
            current_user = self._current_user()
            if ruta == "/api/password":
                if current_user is None:
                    self._send_json({"error": "Inicie sesión para continuar."}, 401)
                    return
                exito, mensaje = AuthController(self.database).cambiar_clave(
                    current_user.id, str(datos.get("actual", "")), str(datos.get("nueva", "")),
                    origen=self.client_address[0],
                )
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            if current_user is None:
                self._send_json({"error": "Inicie sesión para continuar."}, 401)
                return
            if not AuthController(self.database).acceso_operativo_permitido(current_user.id):
                self._send_json({"error": "Cambie su contraseña antes de utilizar el sistema."}, 403)
                return
            if not self.demo_mode and ruta in {
                "/api/recepcion", "/api/catalogacion", "/api/distribucion",
                "/api/ubicacion", "/api/libraries", "/api/users",
            }:
                self._send_json(
                    {"error": "Las operaciones de escritura sólo están habilitadas en modo demostración."},
                    403,
                )
                return
            usuario_id = current_user.id
            if ruta == "/api/fichas":
                ids = self._ids(datos, 4)
                disponibles = {libro["id"]: libro for libro in FicheroController(self.database).buscar()}
                self._require_books(ids, disponibles, "Seleccione sólo libros catalogados.")
                self._download_pdf(lambda destino: PDFService().generar_fichas([disponibles[i] for i in ids], destino), "cedulas_libros.pdf")
                return
            if ruta == "/api/recepcion":
                exito, mensaje = RecepcionController(self.database).registrar(datos, usuario_id)
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            if ruta == "/api/catalogacion":
                exito, mensaje = CatalogacionController(self.database).catalogar(
                    int(datos.get("id", 0)), str(datos.get("sistema", "")),
                    str(datos.get("codigo", "")), str(datos.get("cutter", "")),
                    str(datos.get("cota", "")), usuario_id,
                    permitir_cota_duplicada=bool(datos.get("permitir_duplicada", False)),
                )
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            if ruta == "/api/cota":
                resultado = CatalogacionController(self.database).generar_cota_automatica(
                    int(datos.get("id", 0)), str(datos.get("codigo", "")), datos,
                )
                self._send_json(resultado)
                return
            if ruta == "/api/cutter":
                self._send_json({"cutter": CatalogacionController(self.database).sugerir_cutter(str(datos.get("autor", "")))})
                return
            if ruta == "/api/distribucion":
                ids = self._ids(datos, 1)
                exito, resultado = DistribucionController(self.database).crear_bulto(
                    int(datos.get("biblioteca_id", 0)), ids, usuario_id,
                    str(datos.get("genero", "")), str(datos.get("observaciones", "")),
                )
                self._send_json({"ok": exito, "message": resultado, "codigo": resultado if exito else ""}, 200 if exito else 400)
                return
            if ruta == "/api/distribution-document":
                datos_envio = DistribucionController(self.database).obtener_envio(str(datos.get("codigo", "")))
                if datos_envio is None:
                    raise ValueError("No se encontró el envío solicitado.")
                bulto, libros = datos_envio
                self._download_pdf(lambda destino: PDFService().generar_control_envio_snbp(bulto, libros, destino), "control_envio.pdf")
                return
            if ruta == "/api/ubicacion":
                exito, mensaje = UbicacionController(self.database).actualizar_ubicacion(
                    int(datos.get("id", 0)), int(datos.get("biblioteca_id", 0)),
                    str(datos.get("tipo", "")), str(datos.get("sala", "")),
                    str(datos.get("estante", "")), usuario_id,
                )
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            if ruta == "/api/labels":
                ids = self._ids(datos, 1)
                disponibles = {item["id"]: item for item in FicheroController(self.database).buscar()}
                self._require_books(ids, disponibles, "Seleccione libros catalogados.")
                ancho, alto = float(datos.get("ancho", 1.4)), float(datos.get("alto", 4.0))
                self._download_pdf(lambda destino: PDFService().generar_cotas([disponibles[i] for i in ids], destino, ancho, alto), "cotas_lomo.pdf")
                return
            if ruta == "/api/reportes/pdf":
                inicio, fin = self._date_range(datos)
                self._download_pdf(lambda destino: self._create_report_pdf(inicio, fin, destino), "reporte_bibliotecario.pdf")
                return
            if ruta == "/api/reportes/excel":
                inicio, fin = self._date_range(datos)
                self._download_file(lambda destino: self._create_report_excel(inicio, fin, destino), "reporte_bibliotecario.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                return
            if ruta == "/api/backup":
                ok, message = BackupController(
                    self.database, Path(self.database.database_path).parent / "backups",
                ).crear_backup(usuario_id, self.client_address[0])
                self._send_json({"ok": ok, "message": message}, 200 if ok else 500)
                return
            if ruta == "/api/libraries":
                if current_user.rol != "admin":
                    self._send_json({"error": "Esta operación requiere rol administrador."}, 403)
                    return
                exito, mensaje = BibliotecaController(self.database).crear(
                    str(datos.get("nombre", "")), str(datos.get("direccion", "")),
                    str(datos.get("encargado", "")), str(datos.get("telefono", "")),
                    str(datos.get("email", "")),
                    usuario_id=usuario_id, origen=self.client_address[0],
                )
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            if ruta == "/api/users":
                if current_user.rol != "admin":
                    self._send_json({"error": "Esta operación requiere rol administrador."}, 403)
                    return
                exito, mensaje = AuthController(self.database).crear_usuario(
                    str(datos.get("username", "")), str(datos.get("nombre", "")),
                    str(datos.get("password", "")), str(datos.get("rol", "bibliotecario")),
                    usuario_id, self.client_address[0],
                )
                self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
                return
            self.send_error(404, "Recurso no encontrado")
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error) or "Solicitud no válida."}, 400)

    def do_PATCH(self) -> None:
        try:
            datos = self._read_json()
            ruta = urlparse(self.path).path
            current_user = self._current_user()
            if current_user is None:
                self._send_json({"error": "Inicie sesión para continuar."}, 401)
                return
            if not AuthController(self.database).acceso_operativo_permitido(current_user.id):
                self._send_json({"error": "Cambie su contraseña antes de utilizar el sistema."}, 403)
                return
            if not self.demo_mode:
                self._send_json(
                    {"error": "Las operaciones de escritura sólo están habilitadas en modo demostración."},
                    403,
                )
                return
            if current_user.rol != "admin":
                self._send_json({"error": "Esta operación requiere rol administrador."}, 403)
                return
            if ruta == "/api/libraries":
                exito, mensaje = BibliotecaController(self.database).desactivar(
                    int(datos.get("id", 0)), current_user.id, self.client_address[0],
                )
            elif ruta == "/api/users":
                exito, mensaje = AuthController(self.database).cambiar_estado_usuario(
                    int(datos.get("id", 0)), bool(datos.get("activo")),
                    current_user.id, self.client_address[0],
                )
            else:
                self.send_error(404, "Recurso no encontrado")
                return
            self._send_json({"ok": exito, "message": mensaje}, 200 if exito else 400)
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error) or "Solicitud no válida."}, 400)

    def _read_json(self) -> dict:
        largo = int(self.headers.get("Content-Length", "0"))
        if largo > 16384:
            raise ValueError("La solicitud es demasiado grande.")
        datos = json.loads(self.rfile.read(largo) or b"{}")
        if not isinstance(datos, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON.")
        return datos

    @staticmethod
    def _optional_int(value: str) -> int | None:
        return int(value) if value not in (None, "") else None

    @staticmethod
    def _optional_date(value: str) -> date | None:
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _book_data(book: Book) -> dict:
        return {name: getattr(book, name) for name in (
            "id", "titulo", "autor", "editorial", "anio", "isbn", "edicion", "idioma",
            "paginas", "procedencia", "procedencia_detalle", "fecha_ingreso", "estado",
            "cota", "codigo_dewey", "numero_registro", "observaciones",
        )}

    def _libraries(self, include_inactive: bool = False) -> list[dict]:
        return [{
            "id": library.id, "nombre": library.nombre, "direccion": library.direccion,
            "encargado": library.encargado, "telefono": library.telefono,
            "email": library.email, "activa": library.activa,
        } for library in BibliotecaController(self.database).listar(incluir_inactivas=include_inactive)]

    def _shipments(self) -> list[dict]:
        with self.database.session() as session:
            packages = session.scalars(select(Package).order_by(Package.fecha_envio.desc())).all()
            return [{
                "codigo": item.codigo_envio, "destino": item.biblioteca_destino.nombre,
                "fecha": item.fecha_envio.isoformat(sep=" ", timespec="minutes"),
                "cantidad": item.cantidad_libros, "genero": item.genero,
            } for item in packages]

    def _session_token(self) -> str | None:
        cookies = SimpleCookie()
        cookies.load(self.headers.get("Cookie", ""))
        morsel = cookies.get("bliblioteca_session")
        return morsel.value if morsel else None

    @staticmethod
    def _session_cookie(token: str, expired: bool = False) -> str:
        atributos = ["HttpOnly", "SameSite=Strict", "Path=/"]
        entorno = os.getenv("BLIBLIOTECA_ENV", os.getenv("APP_ENV", "")).casefold()
        cookie_segura = (
            entorno in {"production", "prod"}
            or os.getenv("BLIBLIOTECA_COOKIE_SECURE", "").casefold() in {"1", "true", "yes"}
        )
        if cookie_segura:
            atributos.append("Secure")
        if expired:
            atributos.append("Max-Age=0")
        return f"bliblioteca_session={token}; " + "; ".join(atributos)

    def _current_user(self) -> User | None:
        token = self._session_token()
        user_id = self.session_store.get(token) if token else None
        if user_id is None:
            return None
        with self.database.session() as session:
            user = session.get(User, user_id)
            if user is None or not user.activo:
                self.session_store.pop(token, None)
                return None
            return user

    @staticmethod
    def _user_payload(user: User) -> dict:
        return {
            "authenticated": True, "username": user.username,
            "nombre": user.nombre_completo, "rol": user.rol,
            "debe_cambiar_clave": user.debe_cambiar_clave,
        }

    @staticmethod
    def _ids(datos: dict, minimum: int) -> list[int]:
        ids = datos.get("ids")
        if not isinstance(ids, list) or len(ids) < minimum:
            raise ValueError(f"Seleccione al menos {minimum} libro(s).")
        valores = [int(item) for item in ids]
        if len(set(valores)) != len(valores):
            raise ValueError("La selección contiene registros repetidos.")
        return valores

    @staticmethod
    def _require_books(ids: list[int], disponibles: dict, mensaje: str) -> None:
        if any(libro_id not in disponibles for libro_id in ids):
            raise ValueError(mensaje)

    def _date_range(self, datos: dict):
        return self._optional_date(str(datos.get("desde", ""))), self._optional_date(str(datos.get("hasta", "")))

    def _download_pdf(self, create, filename: str) -> None:
        self._download_file(create, filename, "application/pdf")

    def _download_file(self, create, filename: str, content_type: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as archivo:
            ruta = Path(archivo.name)
        try:
            create(ruta)
            user = self._current_user()
            if user is not None:
                AuditService(self.database).registrar(
                    "EXPORTACION_DATOS", user.id, self.client_address[0],
                    f"Descargó '{filename}' desde {urlparse(self.path).path}.",
                )
            self._send_bytes(ruta.read_bytes(), content_type, attachment=filename)
        finally:
            ruta.unlink(missing_ok=True)

    def _create_report_pdf(self, inicio, fin, destino) -> None:
        reportes = ReportesController(self.database)
        resumen, filas = reportes.resumen(inicio, fin), reportes.inventario(inicio, fin)
        PDFService().generar_reporte("Reporte bibliotecario", [
            ("Recepción por procedencia", ["Procedencia", "Cantidad"], [[key, value] for key, value in resumen["recepcion"].items()]),
            ("Inventario por estado", ["Estado", "Cantidad"], [[key, value] for key, value in resumen["estados"].items()]),
            ("Inventario", ["Registro", "Título", "Autor", "Estado", "Cota"], [[row[key] for key in ("registro", "titulo", "autor", "estado", "cota")] for row in filas]),
        ], destino)

    def _create_report_excel(self, inicio, fin, destino) -> None:
        reportes = ReportesController(self.database)
        resumen = reportes.resumen(inicio, fin)
        ExcelService().exportar({
            "Inventario": reportes.inventario(inicio, fin),
            "Estados": [{"estado": key, "cantidad": value} for key, value in resumen["estados"].items()],
            "Recepcion": [{"procedencia": key, "cantidad": value} for key, value in resumen["recepcion"].items()],
            "Distribucion": [{"biblioteca": nombre, "cantidad": cantidad} for nombre, cantidad in resumen["distribucion"]],
        }, destino)

    def _send_file(self, nombre: str, content_type: str) -> None:
        ruta = WEB_DIR / nombre
        if not ruta.is_file():
            self.send_error(404, "Vista no encontrada")
            return
        self._send_bytes(ruta.read_bytes(), content_type)

    def _send_json(self, datos, status: int = 200, extra_headers: list[tuple[str, str]] | None = None) -> None:
        contenido = json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8")
        self._send_bytes(contenido, "application/json; charset=utf-8", status, headers=extra_headers)

    def _send_bytes(self, contenido: bytes, content_type: str, status: int = 200, attachment: str = "", headers: list[tuple[str, str]] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
        for nombre, valor in headers or []:
            self.send_header(nombre, valor)
        self.end_headers()
        self.wfile.write(contenido)

    def log_message(self, formato: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {formato % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vista web local de prueba del sistema bibliotecario.")
    parser.add_argument("--host", default="127.0.0.1", help="Interfaz de escucha (por defecto, sólo local).")
    parser.add_argument("--port", type=int, default=8765, help="Puerto HTTP de prueba.")
    parser.add_argument("--demo", action="store_true", help="Usa una base aislada con libros de muestra.")
    parser.add_argument("--database", type=Path, default=None, help="Ruta de la base existente; no combinar con --demo.")
    args = parser.parse_args()
    if args.demo and args.database:
        parser.error("Use --demo o --database, no ambos.")

    ruta_db = DEMO_DATABASE_PATH if args.demo else (args.database or DATABASE_PATH)
    database = DatabaseManager(ruta_db)
    database.initialize()
    if args.demo:
        seed_demo_catalog(database)

    try:
        run_web_preview(database, args.host, args.port, args.demo)
    finally:
        database.close()


def run_web_preview(database: DatabaseManager, host: str = "127.0.0.1", port: int = 0, demo_mode: bool = False, open_browser: bool = False) -> None:
    handler = type("ConfiguredPreviewHandler", (PreviewHandler,), {
        "database": database, "demo_mode": demo_mode, "session_store": {},
    })
    servidor = ThreadingHTTPServer((host, port), handler)
    puerto_real = servidor.server_address[1]
    url = f"http://{host}:{puerto_real}"
    modo = "demostración aislada" if demo_mode else f"base {database.database_path}"
    print(f"Vista web ({modo}) disponible en {url}")
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor de prueba detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()