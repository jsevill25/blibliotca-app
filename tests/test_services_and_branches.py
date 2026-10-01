import sqlite3
from zipfile import is_zipfile

from controllers.biblioteca_controller import BibliotecaController
from database.db_manager import DatabaseManager
from openpyxl import load_workbook
from services.backup_service import BackupService
from services.excel_service import ExcelService
from services.pdf_service import PDFService


def test_backup_excel_y_pdf_se_generan_y_rotan(tmp_path):
    database = DatabaseManager(tmp_path / "central.db")
    database.initialize()
    backups = BackupService(database.database_path, tmp_path / "backups", max_backups=7)
    for _ in range(8):
        exito, resultado = backups.crear_backup()
        assert exito is True, resultado
    copias = list((tmp_path / "backups").glob("biblioteca_*.db"))
    assert len(copias) == 7
    with sqlite3.connect(resultado) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    ExcelService().exportar({"Inventario": [{"titulo": "Libro", "estado": "recibido"}]}, tmp_path / "inventario.xlsx")
    assert is_zipfile(tmp_path / "inventario.xlsx")
    respaldo_excel = tmp_path / "respaldo_completo.xlsx"
    ExcelService().exportar_base_datos(database.engine, respaldo_excel)
    libro_excel = load_workbook(respaldo_excel, read_only=True)
    assert {"libros", "usuarios", "movimientos", "bulto_libros"} <= set(libro_excel.sheetnames)
    libro_excel.close()
    pdf = PDFService()
    bulto = {"codigo_envio": "ENV-20260930-001", "destino": "Sucursal", "fecha": "2026-09-30", "cantidad_libros": 1}
    libros = [{"titulo": "Libro <de prueba> & otros", "autor": "Autora & co.", "cota": "863.6\nA123\n2024", "numero_registro": "REG-2026-00001"}]
    for ruta in (tmp_path / "cotas.pdf", tmp_path / "fichas.pdf", tmp_path / "envio.pdf", tmp_path / "mini.pdf"):
        if ruta.name == "cotas.pdf":
            pdf.generar_cotas(libros, ruta, ancho_cm=1.6, alto_cm=4.2)
        elif ruta.name == "fichas.pdf":
            pdf.generar_fichas(libros, ruta)
        elif ruta.name == "envio.pdf":
            pdf.generar_documento_envio(bulto, libros, ruta)
        else:
            pdf.generar_mini_ficha(bulto, ruta)
        assert ruta.read_bytes().startswith(b"%PDF-")
    reporte = tmp_path / "reporte.pdf"
    pdf.generar_reporte("Reporte & catálogo", [("Libros", ["Título", "Registro"], [["Libro <A>", "REG-1"]])], reporte)
    assert reporte.read_bytes().startswith(b"%PDF-")
    database.close()


def test_sucursales_pueden_crearse_y_desactivarse_sin_desactivar_central(tmp_path):
    database = DatabaseManager(tmp_path / "central.db")
    database.initialize()
    controller = BibliotecaController(database)
    creado, mensaje = controller.crear("Sucursal Sur", "Avenida 1", "Encargada", "555-0100", "sur@example.org")
    assert creado is True, mensaje
    sucursal = next(item for item in controller.listar() if item.nombre == "Sucursal Sur")
    assert controller.desactivar(sucursal.id)[0] is True
    assert all(item.nombre != "Sucursal Sur" for item in controller.listar())
    central = next(item for item in controller.listar() if item.nombre == "Biblioteca Central Rómulo Gallegos")
    assert controller.desactivar(central.id)[0] is False
    database.close()