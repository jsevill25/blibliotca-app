import hashlib
import secrets
from datetime import date
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from config import DATABASE_PATH, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from database.models import Book, BookStock, Cataloging, Library, Location, Movement, Reception, User


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 310_000).hex()


def seed_initial_data(session: Session, database_path: str | object | None = None) -> None:
    if session.scalar(select(User.id).where(User.username == DEFAULT_ADMIN_USERNAME)) is None:
        salt = secrets.token_hex(16)
        session.add(User(
            username=DEFAULT_ADMIN_USERNAME,
            nombre_completo="Administrador del sistema",
            rol="admin",
            salt=salt,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD, salt),
            debe_cambiar_clave=True,
        ))

    central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
    if central is None:
        central = Library(nombre="Biblioteca Central Rómulo Gallegos", activa=True)
        session.add(central)
        session.flush()

    path_esperada = str(Path(database_path).resolve()) if database_path else ""
    usar_datos_demo = path_esperada.endswith("biblioteca_central.db") or path_esperada == str(DATABASE_PATH.resolve())

    if usar_datos_demo:
        bibliotecas_demo = [
            ("Sede de prueba Norte", "Avenida Bolívar, bloque A", "Maracaibo", "Luz Pérez"),
            ("Sede de prueba Sur", "Calle 7, urbanización Los Ángeles", "Valencia", "Ana López"),
            ("Sede de prueba Este", "Carrera 5, sector Jardines", "Barquisimeto", "José Rivera"),
        ]
        for nombre, direccion, municipio, encargado in bibliotecas_demo:
            if session.scalar(select(Library.id).where(Library.nombre == nombre)) is None:
                session.add(Library(nombre=nombre, direccion=direccion, municipio=municipio, encargado=encargado, activa=True))

    session.flush()

    libros_columns = {row[1] for row in session.execute(text("PRAGMA table_info(libros)")).all()}
    if "isbn" not in libros_columns or not usar_datos_demo:
        session.commit()
        return

    libros_demo = [
            {
                "titulo": "Cien años de soledad",
                "autor": "Gabriel García Márquez",
                "editorial": "Editorial Sudamericana",
                "anio": 1967,
                "isbn": "978-980-000-001",
                "procedencia": "compra",
                "procedencia_detalle": "Pedido inicial de prueba",
                "numero_registro": "REG-2026-00001",
                "estado": "catalogado",
                "cantidad": 4,
                "numero_volumenes": 4,
                "precio_unitario": 58.50,
                "codigo_dewey": "863.6",
                "cota": "G216",
                "sala": "Sala general",
                "estante": "A-01",
                "biblioteca": central,
            },
            {
                "titulo": "La ciudad y los perros",
                "autor": "Mario Vargas Llosa",
                "editorial": "Seix Barral",
                "anio": 1963,
                "isbn": "978-980-000-002",
                "procedencia": "donacion",
                "procedencia_detalle": "Donación institucional",
                "numero_registro": "REG-2026-00002",
                "estado": "catalogado",
                "cantidad": 2,
                "numero_volumenes": 2,
                "precio_unitario": 42.00,
                "codigo_dewey": "863.3",
                "cota": "V217",
                "sala": "Sala juvenil",
                "estante": "B-04",
                "biblioteca": central,
            },
            {
                "titulo": "Poesía y memoria",
                "autor": "María Antonieta",
                "editorial": "Aurelia",
                "anio": 2021,
                "isbn": "978-980-000-003",
                "procedencia": "biblioteca_nacional",
                "procedencia_detalle": "Intercambio nacional",
                "numero_registro": "REG-2026-00003",
                "estado": "recibido",
                "cantidad": 3,
                "numero_volumenes": 3,
                "precio_unitario": 30.25,
                "codigo_dewey": "861",
                "cota": "A890",
                "sala": "Recepción",
                "estante": "R-02",
                "biblioteca": central,
            },
            {
                "titulo": "Guía de bibliotecas escolares",
                "autor": "Equipo editorial de prueba",
                "editorial": "Ediciones de prueba",
                "anio": 2022,
                "isbn": "978-980-000-004",
                "procedencia": "donacion",
                "procedencia_detalle": "Registro de ejemplo para sucursal Norte",
                "estado": "catalogado",
                "cantidad": 2,
                "numero_volumenes": 1,
                "precio_unitario": 25.00,
                "codigo_dewey": "027.8",
                "cota": "G943",
                "sala": "Sala de consulta",
                "estante": "N-01",
                "biblioteca": session.scalar(select(Library).where(Library.nombre == "Sede de prueba Norte")),
            },
            {
                "titulo": "Geografía regional de Venezuela",
                "autor": "Equipo editorial de prueba",
                "editorial": "Ediciones de prueba",
                "anio": 2020,
                "isbn": "978-980-000-005",
                "procedencia": "compra",
                "procedencia_detalle": "Registro de ejemplo para sucursal Sur",
                "estado": "catalogado",
                "cantidad": 3,
                "numero_volumenes": 1,
                "precio_unitario": 34.50,
                "codigo_dewey": "918.7",
                "cota": "G345",
                "sala": "Sala general",
                "estante": "S-02",
                "biblioteca": session.scalar(select(Library).where(Library.nombre == "Sede de prueba Sur")),
            },
            {
                "titulo": "Introducción a la catalogación",
                "autor": "Equipo editorial de prueba",
                "editorial": "Ediciones de prueba",
                "anio": 2023,
                "isbn": "978-980-000-006",
                "procedencia": "biblioteca_nacional",
                "procedencia_detalle": "Registro de ejemplo para sucursal Este",
                "estado": "recibido",
                "cantidad": 1,
                "numero_volumenes": 1,
                "precio_unitario": 19.00,
                "codigo_dewey": "025.3",
                "cota": "",
                "sala": "Recepción",
                "estante": "E-01",
                "biblioteca": session.scalar(select(Library).where(Library.nombre == "Sede de prueba Este")),
            },
    ]
    prefijo = f"REG-{date.today().year}-"
    numeros_registro = list(session.scalars(select(Book.numero_registro).where(Book.numero_registro.like(f"{prefijo}%"))))
    secuencia = max(
        (
            int(numero.rsplit("-", 1)[1])
            for numero in numeros_registro
            if numero.rsplit("-", 1)[-1].isdigit()
        ),
        default=0,
    ) + 1
    for datos in libros_demo:
        libro = session.scalar(select(Book).where(Book.isbn == datos["isbn"]))
        if libro is None:
            while f"{prefijo}{secuencia:05d}" in numeros_registro:
                secuencia += 1
            numero_registro = datos.get("numero_registro", f"{prefijo}{secuencia:05d}")
            while numero_registro in numeros_registro:
                secuencia += 1
                numero_registro = f"{prefijo}{secuencia:05d}"
            numeros_registro.append(numero_registro)
            secuencia += 1
            libro = Book(
                titulo=datos["titulo"],
                autor=datos["autor"],
                editorial=datos["editorial"],
                anio=datos["anio"],
                isbn=datos["isbn"],
                procedencia=datos["procedencia"],
                procedencia_detalle=datos["procedencia_detalle"],
                fecha_ingreso=date.today(),
                estado=datos["estado"],
                numero_registro=numero_registro,
                numero_volumenes=datos["numero_volumenes"],
                precio_unitario=datos["precio_unitario"],
                cantidad=datos["cantidad"],
                codigo_dewey=datos["codigo_dewey"],
                cota=datos["cota"],
                observaciones="Datos de prueba para validación del sistema",
            )
            session.add(libro)
            session.flush()
            session.add(Location(libro_id=libro.id, biblioteca_id=datos["biblioteca"].id, tipo_ubicacion="deposito", sala=datos["sala"], estante=datos["estante"]))
            session.add(BookStock(libro_id=libro.id, biblioteca_id=datos["biblioteca"].id, cantidad=datos["cantidad"]))
            session.add(Movement(
                libro_id=libro.id,
                tipo_movimiento="recepcion",
                origen="Sistema",
                destino=datos["biblioteca"].nombre,
                detalle=f"Carga inicial de prueba ({datos['cantidad']} ejemplares)",
            ))
        if libro.recepcion is None:
            session.add(Reception(
                libro_id=libro.id,
                tipo_ingreso=datos["procedencia"],
                observaciones="Datos de prueba para validación del sistema",
            ))
        if datos["estado"] == "catalogado" and libro.catalogacion is None:
            session.add(Cataloging(
                libro_id=libro.id,
                clasificacion="Dewey",
                codigo_clasificacion=datos["codigo_dewey"],
                cota_completa=f"{datos['codigo_dewey']}\n{datos['cota']}\n{datos['anio']}",
                cutter=datos["cota"],
            ))

    session.commit()