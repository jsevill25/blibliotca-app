import re
import sqlite3
import time

from controllers.fichero_controller import FicheroController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Location
from services.backup_service import BackupService
from services.excel_service import ExcelService
from services.pdf_service import PDFService
def test_isolated_synthetic_catalog_search_performance_and_report(tmp_path):
    database = DatabaseManager(tmp_path / "readiness-catalog.sqlite")
    database.initialize()
    with database.session() as session:
        central = session.query(Library).filter_by(nombre="Biblioteca Central Rómulo Gallegos").one()
        libros = []
        for indice in range(300):
            numero_dewey = (indice % 10) * 100
            libro = Book(
                titulo=f"Validación sintética volumen {indice:04d}",
                autor=f"Autor de prueba {indice:04d}",
                editorial="Editorial de simulación",
                anio=2020 + indice % 7,
                paginas=100 + indice % 250,
                procedencia="donacion",
                estado="catalogado",
                codigo_dewey=f"{numero_dewey:03d}.1",
                cota=f"{numero_dewey:03d}.1\nA100\n2026",
                numero_registro=f"REG-2026-{indice + 1:05d}",
            )
            libros.append(libro)
        session.add_all(libros)
        session.flush()
        session.add_all([
            Cataloging(
                libro_id=libro.id, clasificacion="Dewey",
                codigo_clasificacion=libro.codigo_dewey,
                cota_completa=libro.cota, cutter="A100",
            )
            for libro in libros
        ])
        session.add_all([
            Location(libro_id=libro.id, biblioteca_id=central.id, tipo_ubicacion="deposito")
            for libro in libros
        ])

    inicio = time.perf_counter()
    resultados = FicheroController(database).buscar("sintética volumen 0299")
    duracion = time.perf_counter() - inicio
    assert len(resultados) == 1
    assert duracion < 2.0

    datos_matriz = ReportesController(database).resumen_distribucion_areas()
    total_general = datos_matriz["totales_generales"]["Total General"]
    assert total_general == {"T": 300, "V": 300}
    central = next(
        fila for fila in datos_matriz["sucursales"]
        if fila["biblioteca"] == "Biblioteca Central 'Rómulo Gallegos'"
    )
    assert central["categorias"]["Total General"] == {"T": 300, "V": 300}

    ruta_pdf = tmp_path / "inventario-sintetico.pdf"
    PDFService().generar_reporte("Inventario sintético", [
        ("Registros", ["Registro", "Título"], [
            [f"REG-SINT-{indice + 1:04d}", f"Volumen sintético {indice + 1:04d}"]
            for indice in range(300)
        ]),
    ], ruta_pdf)
    contenido_pdf = ruta_pdf.read_bytes()
    assert contenido_pdf.startswith(b"%PDF-")
    assert len(re.findall(rb"/Type\s*/Page\b", contenido_pdf)) > 1
    database.close()


def test_backup_restore_round_trip_keeps_rows_and_relations(tmp_path):
    ruta_db = tmp_path / "operacion.sqlite"
    database = DatabaseManager(ruta_db)
    database.initialize()
    creado, numero = RecepcionController(database).registrar({
        "titulo": "Registro ficticio para restauración",
        "autor": "Equipo de pruebas",
        "procedencia": "donacion",
    }, None)
    assert creado is True

    backup = BackupService(ruta_db, tmp_path / "backups")
    correcto, resultado = backup.crear_backup()
    assert correcto is True, resultado
    database.close()

    ruta_restaurada = tmp_path / "restauracion" / "restaurada.sqlite"
    ruta_restaurada.parent.mkdir(parents=True)
    with sqlite3.connect(resultado) as origen, sqlite3.connect(ruta_restaurada) as destino:
        origen.backup(destino)
        assert destino.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    restaurada = DatabaseManager(ruta_restaurada)
    restaurada.initialize()
    libro = RecepcionController(restaurada).listar(texto="Registro ficticio para restauración")[0]
    assert libro.numero_registro == numero
    assert libro.titulo == "Registro ficticio para restauración"
    assert libro.recepcion is not None
    assert ReportesController(restaurada).resumen()["total"] == 1
    restaurada.close()
