import os
import sqlite3
import tempfile

import pytest

from controllers.libro_controller import LibroController
from models.database import inicializar_base_datos


def _new_app(tmp_path):
    # Crea una DB temporal y re-inicializa el esquema/semilla.
    db_path = os.path.join(tmp_path, "biblioteca_test.db")
    inicializar_base_datos(db_path)

    # Asegurar sede existente para cumplir FK de ejemplares.
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO bibliotecas (nombre, direccion, tipo, encargado_nombre, encargado_contacto)
        VALUES (?, ?, ?, ?, ?)
    """, ("Sede Test", "Direccion Test", "Central", "Encargado Test", "Contacto Test"))
    con.commit()
    con.close()


    # El modelo por defecto usa "biblioteca.db"; por eso inyectamos ruta.
    controller = LibroController()
    controller.model.db_path = db_path

    return controller, db_path


def _count_by_estado(db_path, isbn):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT estado, COUNT(*) FROM ejemplares WHERE isbn = ? GROUP BY estado", (isbn,))
    rows = cur.fetchall()
    con.close()
    return {estado: n for estado, n in rows}


def test_registrar_recepcion_crea_ejemplares_en_recibido(tmp_path):
    controller, db_path = _new_app(tmp_path)

    exito, msg = controller.registrar_recepcion(
        isbn="978-TEST-0001-1",
        titulo="Libro de Prueba",
        autor="Autor de Prueba",
        editorial="Editorial Test",
        anio="2026",
        origen="Biblioteca Nacional",
        cantidad="3",
    )
    assert exito is True, msg

    estados = _count_by_estado(db_path, "978-TEST-0001-1")
    assert estados.get("recibido", 0) == 3


def test_registrar_recepcion_rechaza_cantidad_cero(tmp_path):
    controller, _ = _new_app(tmp_path)

    exito, msg = controller.registrar_recepcion(
        isbn="978-TEST-0002-2",
        titulo="Libro de Prueba 2",
        autor="Autor de Prueba 2",
        editorial="Editorial Test",
        anio="2026",
        origen="Donación Particular",
        cantidad="0",
    )
    assert exito is False
    assert "mayor que cero" in msg.lower()


def test_registrar_recepcion_rechaza_campos_obligatorios(tmp_path):
    controller, _ = _new_app(tmp_path)

    exito, msg = controller.registrar_recepcion(
        isbn="",
        titulo="",
        autor="Autor",
        editorial="Editorial",
        anio="2026",
        origen="",
        cantidad="1",
    )
    assert exito is False
    # Debe mencionar al menos ISBN, Título y Origen
    assert "isbn" in msg.lower()
    assert "título" in msg.lower() or "titulo" in msg.lower()
    assert "origen" in msg.lower()

