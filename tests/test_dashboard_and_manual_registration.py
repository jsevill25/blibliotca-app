from datetime import date

from sqlalchemy import select

from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from database.db_manager import DatabaseManager
from database.models import Book, BookStock, Library, Location, Movement, Reception


def test_manual_reception_preserves_existing_records_and_dashboard_tracks_transfer(tmp_path):
    database = DatabaseManager(tmp_path / "biblioteca.db")
    database.initialize()
    with database.session() as session:
        central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
        existente = Book(
            titulo="Registro existente",
            autor="Autora existente",
            procedencia="donacion",
            estado="recibido",
            numero_registro="REG-2026-00008",
            cantidad=2,
        )
        sucursal = Library(nombre="Sucursal de prueba", activa=True)
        session.add_all([existente, sucursal])
        session.flush()
        central_id = central.id
        session.add_all([
            Reception(libro_id=existente.id, tipo_ingreso="donacion"),
            Location(libro_id=existente.id, biblioteca_id=central.id, tipo_ubicacion="deposito"),
            BookStock(libro_id=existente.id, biblioteca_id=central.id, cantidad=2),
        ])
        existente_id = existente.id
        sucursal_id = sucursal.id

    recepcion = RecepcionController(database)
    registrado, numero_registro = recepcion.registrar({
        "titulo": "Nuevo libro para prueba",
        "autor": "Autora de prueba",
        "isbn": "978-TEST-REGISTRO-1",
        "procedencia": "donacion",
        "cantidad": "4",
    }, None)
    assert registrado is True, numero_registro
    nuevo = recepcion.listar(texto="978-TEST-REGISTRO-1")[0]
    assert nuevo.numero_registro == numero_registro
    assert nuevo.cantidad == 4
    assert nuevo.recepcion is not None
    with database.session() as session:
        assert session.get(Book, existente_id).titulo == "Registro existente"
        assert session.scalar(select(BookStock.cantidad).where(BookStock.libro_id == nuevo.id)) == 4

    catalogacion = CatalogacionController(database)
    assert catalogacion.catalogar(nuevo.id, "Dewey", "863.6", "G216", "863.6\nG216\n2024", None)[0] is True
    enviado, codigo = DistribucionController(database).crear_bulto(sucursal_id, [nuevo.id], None)
    assert enviado is True, codigo
    with database.session() as session:
        cantidades = {
            biblioteca_id: cantidad
            for biblioteca_id, cantidad in session.execute(
                select(BookStock.biblioteca_id, BookStock.cantidad).where(BookStock.libro_id == nuevo.id)
            )
        }
        assert cantidades == {central_id: 3, sucursal_id: 1}
        assert session.get(Book, nuevo.id).cantidad == 4
        assert session.get(Book, existente_id).cantidad == 2

    resumen = ReportesController(database).estadisticas_panel()
    stats_central = next(fila for fila in resumen["bibliotecas"] if fila["nombre"] == "Biblioteca Central Rómulo Gallegos")
    stats_sucursal = next(fila for fila in resumen["bibliotecas"] if fila["id"] == sucursal_id)
    assert stats_central["ejemplares"] == 5
    assert stats_sucursal["ejemplares"] == 1
    registro_reciente = next(fila for fila in resumen["libros"] if fila["registro"] == numero_registro)
    assert registro_reciente["cantidad_registrada"] == 4
    assert registro_reciente["ejemplares_en_bibliotecas"] == 4
    database.close()


def test_existing_book_without_stock_is_migrated_to_its_last_library(tmp_path):
    path = tmp_path / "biblioteca.db"
    database = DatabaseManager(path)
    database.initialize()
    with database.session() as session:
        central = session.scalar(select(Library).where(Library.nombre == "Biblioteca Central Rómulo Gallegos"))
        libro = Book(
            titulo="Libro heredado",
            procedencia="compra",
            estado="catalogado",
            numero_registro=f"REG-{date.today().year}-90001",
            cantidad=3,
        )
        session.add(libro)
        session.flush()
        session.add(Location(libro_id=libro.id, biblioteca_id=central.id, tipo_ubicacion="sala"))
        libro_id = libro.id

    database.close()
    database = DatabaseManager(path)
    database.initialize()
    with database.session() as session:
        stock = session.scalar(select(BookStock).where(BookStock.libro_id == libro_id))
        assert stock is not None
        assert stock.cantidad == 3
        assert stock.biblioteca.nombre == "Biblioteca Central Rómulo Gallegos"
    database.close()


def test_default_database_seeds_sample_records_for_each_branch_idempotently(tmp_path):
    path = tmp_path / "data" / "biblioteca_central.db"
    database = DatabaseManager(path)
    database.initialize()
    database.initialize()

    resumen = ReportesController(database).estadisticas_panel()
    sedes = {fila["nombre"]: fila for fila in resumen["bibliotecas"]}
    assert sedes["Biblioteca Central Rómulo Gallegos"]["ejemplares"] > 0
    assert sedes["Sede de prueba Norte"]["ejemplares"] == 2
    assert sedes["Sede de prueba Sur"]["ejemplares"] == 3
    assert sedes["Sede de prueba Este"]["recibidos"] == 1
    assert len({libro["registro"] for libro in resumen["libros"]}) == len(resumen["libros"])
    database.close()
