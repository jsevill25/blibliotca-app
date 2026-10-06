from PySide6.QtWidgets import QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.etiqueta_controller import EtiquetaController
from controllers.ubicacion_controller import UbicacionController


class EtiquetasView(QWidget):
    def __init__(self, ubicacion: UbicacionController, etiquetas: EtiquetaController):
        super().__init__()
        self.ubicacion = ubicacion
        self.etiquetas = etiquetas
        layout = QVBoxLayout(self)
        titulo = QLabel("Etiquetas y fichas catalográficas")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Registro", "Título", "Autor", "Cota"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)
        acciones = QHBoxLayout()
        recargar = QPushButton("Actualizar libros catalogados")
        recargar.clicked.connect(self.refrescar)
        self.ancho_etiqueta = QDoubleSpinBox()
        self.ancho_etiqueta.setRange(0.5, 10.0)
        self.ancho_etiqueta.setSingleStep(0.1)
        self.ancho_etiqueta.setValue(1.4)
        self.ancho_etiqueta.setSuffix(" cm ancho")
        self.alto_etiqueta = QDoubleSpinBox()
        self.alto_etiqueta.setRange(0.5, 15.0)
        self.alto_etiqueta.setSingleStep(0.1)
        self.alto_etiqueta.setValue(4.0)
        self.alto_etiqueta.setSuffix(" cm alto")
        cotas = QPushButton("Exportar cotas PDF")
        cotas.clicked.connect(self.exportar_cotas)
        fichas = QPushButton("Exportar fichas catalográficas (4 por hoja carta)")
        fichas.clicked.connect(self.exportar_fichas)
        for boton in (recargar, cotas, fichas):
            acciones.addWidget(boton)
        acciones.addWidget(self.ancho_etiqueta)
        acciones.addWidget(self.alto_etiqueta)
        layout.addLayout(acciones)
        self.refrescar()

    def refrescar(self) -> None:
        self.libros = [info["libro"] for info in self.ubicacion.buscar(estado="catalogado")]
        self.tabla.setRowCount(len(self.libros))
        for row, libro in enumerate(self.libros):
            for column, value in enumerate((libro.id, libro.numero_registro, libro.titulo, libro.autor, libro.cota)):
                self.tabla.setItem(row, column, QTableWidgetItem(str(value or "")))
        self.tabla.resizeColumnsToContents()

    def _seleccionados(self) -> list[dict]:
        filas = sorted({item.row() for item in self.tabla.selectedItems()})
        libros = self.libros if not filas else [self.libros[row] for row in filas]
        return [{
            "titulo": libro.titulo, "autor": libro.autor, "cota": libro.cota,
            "edicion": libro.edicion, "editorial": libro.editorial, "anio": libro.anio,
            "paginas": libro.paginas, "numero_volumenes": getattr(libro, "numero_volumenes", None),
            "observaciones": libro.observaciones, "ciudad": getattr(libro, "ciudad", ""),
            "isbn": libro.isbn, "numero_registro": libro.numero_registro,
        } for libro in libros]

    def exportar_cotas(self) -> None:
        generador = lambda libros, ruta: self.etiquetas.exportar_cotas(
            libros, ruta, self.ancho_etiqueta.value(), self.alto_etiqueta.value(),
        )
        self._exportar("cotas.pdf", generador)

    def exportar_fichas(self) -> None:
        self._exportar(
            "fichas_catalograficas.pdf",
            self.etiquetas.exportar_fichas,
        )

    def _exportar(self, nombre: str, generador) -> None:
        libros = self._seleccionados()
        if not libros:
            QMessageBox.information(self, "Etiquetas", "No hay libros catalogados para exportar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", nombre, "PDF (*.pdf)")
        if not ruta:
            return
        try:
            generador(libros, ruta)
            QMessageBox.information(self, "PDF", f"Archivo generado:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "PDF", str(error))