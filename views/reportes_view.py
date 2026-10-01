from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from controllers.backup_controller import BackupController
from controllers.reportes_controller import ReportesController
from controllers.ubicacion_controller import UbicacionController
from services.excel_service import ExcelService
from services.pdf_service import PDFService


class ReportesView(QWidget):
    def __init__(self, reportes: ReportesController, ubicacion: UbicacionController, backup: BackupController, engine):
        super().__init__()
        self.reportes = reportes
        self.ubicacion = ubicacion
        self.backup = backup
        self.engine = engine
        self.excel = ExcelService()
        self.pdf = PDFService()
        layout = QVBoxLayout(self)
        titulo = QLabel("Reportes, exportación y respaldos")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        self.resumen = QLabel()
        layout.addWidget(self.resumen)
        fechas = QFormLayout()
        self.desde = QDateEdit()
        self.desde.setCalendarPopup(True)
        self.desde.setDate(QDate.currentDate().addDays(-30))
        self.hasta = QDateEdit()
        self.hasta.setCalendarPopup(True)
        self.hasta.setDate(QDate.currentDate())
        fechas.addRow("Desde", self.desde)
        fechas.addRow("Hasta", self.hasta)
        layout.addLayout(fechas)
        filas_botones = (
            (("Actualizar resumen", self.actualizar), ("Exportar inventario Excel", self.exportar_excel), ("Exportar inventario PDF", self.exportar_pdf)),
            (("Exportar todas las tablas", self.exportar_todas_tablas), ("Respaldo completo PDF", self.exportar_respaldo_pdf), ("Crear backup ahora", self.crear_backup)),
        )
        for botones in filas_botones:
            acciones = QHBoxLayout()
            for texto, callback in botones:
                boton = QPushButton(texto)
                boton.clicked.connect(callback)
                acciones.addWidget(boton)
            layout.addLayout(acciones)
        layout.addStretch(1)
        self.actualizar()

    def _rango(self):
        return self.desde.date().toPython(), self.hasta.date().toPython()

    def actualizar(self, *_args) -> None:
        inicio, fin = self._rango()
        datos = self.reportes.resumen(inicio, fin)
        estados = "   |   ".join(f"{estado}: {cantidad}" for estado, cantidad in sorted(datos["estados"].items())) or "Sin libros registrados"
        recepcion = "   |   ".join(f"{origen}: {cantidad}" for origen, cantidad in sorted(datos["recepcion"].items())) or "Sin ingresos"
        distribucion = "   |   ".join(f"{biblioteca}: {cantidad}" for biblioteca, cantidad in datos["distribucion"]) or "Sin envíos"
        catalogacion = datos["catalogacion"]
        self.resumen.setText(
            f"Libros recibidos en el rango: {datos['total']}\nInventario por estado: {estados}\n"
            f"Ingresos por procedencia: {recepcion}\nCatalogados en el rango: {catalogacion['catalogados']} | "
            f"Pendientes actuales: {catalogacion['pendientes']}\nEnvíos por biblioteca: {distribucion}"
        )

    def exportar_excel(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar inventario", "inventario.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        inicio, fin = self._rango()
        libros = self.reportes.inventario(inicio, fin)
        resumen = self.reportes.resumen(inicio, fin)
        try:
            self.excel.exportar({
                "Inventario": libros,
                "Resumen estados": [{"estado": k, "cantidad": v} for k, v in resumen["estados"].items()],
                "Recepcion": [{"procedencia": k, "cantidad": v} for k, v in resumen["recepcion"].items()],
                "Catalogacion": [
                    {"tipo": "Catalogados en el rango", "cantidad": resumen["catalogacion"]["catalogados"]},
                    {"tipo": "Pendientes actuales", "cantidad": resumen["catalogacion"]["pendientes"]},
                ],
                "Distribucion": [{"biblioteca": nombre, "cantidad": cantidad} for nombre, cantidad in resumen["distribucion"]],
                "Ubicaciones": [
                    {"biblioteca": biblioteca, "tipo": tipo, "sala": sala, "estante": estante, "cantidad": cantidad}
                    for biblioteca, tipo, sala, estante, cantidad in resumen["ubicaciones"]
                ],
            }, ruta)
            QMessageBox.information(self, "Excel", f"Archivo generado:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "Excel", str(error))

    def exportar_pdf(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar inventario", "inventario.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        inicio, fin = self._rango()
        filas = self.reportes.inventario(inicio, fin)
        resumen = self.reportes.resumen(inicio, fin)
        try:
            self.pdf.generar_reporte("Reporte bibliotecario", [
                ("Recepción por procedencia", ["Procedencia", "Cantidad"], [[k, v] for k, v in resumen["recepcion"].items()]),
                ("Catalogación", ["Estado", "Cantidad"], [
                    ["Catalogados en el rango", resumen["catalogacion"]["catalogados"]],
                    ["Pendientes actuales", resumen["catalogacion"]["pendientes"]],
                ]),
                ("Distribución por biblioteca", ["Biblioteca", "Cantidad"], [list(fila) for fila in resumen["distribucion"]]),
                ("Inventario por ubicación", ["Biblioteca", "Tipo", "Sala", "Estante", "Cantidad"], [list(fila) for fila in resumen["ubicaciones"]]),
                ("Detalle de inventario", ["Registro", "Título", "Autor", "Estado", "Cota", "Biblioteca", "Sala", "Estante"], [
                    [fila[k] for k in ("registro", "titulo", "autor", "estado", "cota", "biblioteca", "sala", "estante")]
                    for fila in filas
                ]),
            ], ruta)
            QMessageBox.information(self, "PDF", f"Archivo generado:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "PDF", str(error))

    def exportar_respaldo_pdf(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar respaldo completo", "respaldo_inventario.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        filas = self.reportes.inventario()
        columnas = ["registro", "titulo", "autor", "isbn", "estado", "cota", "procedencia", "fecha_ingreso", "biblioteca", "sala", "estante"]
        try:
            self.pdf.generar_reporte("Respaldo completo del inventario", [
                ("Todos los libros activos", columnas, [[fila.get(columna, "") for columna in columnas] for fila in filas]),
            ], ruta)
            QMessageBox.information(self, "PDF", f"Respaldo generado:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "PDF", str(error))

    def exportar_todas_tablas(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar todas las tablas", "respaldo_completo.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        try:
            self.excel.exportar_base_datos(self.engine, ruta)
            QMessageBox.information(self, "Excel", f"Todas las tablas fueron exportadas:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "Excel", str(error))

    def crear_backup(self) -> None:
        exito, resultado = self.backup.crear_backup()
        if exito:
            QMessageBox.information(self, "Backup", f"Respaldo creado:\n{resultado}")
        else:
            QMessageBox.critical(self, "Backup", resultado)