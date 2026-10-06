from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controllers.etiqueta_controller import EtiquetaController
from controllers.fichero_controller import FicheroController


class FicheroView(QWidget):
    MINIMO_FICHAS = 4

    def __init__(self, fichero: FicheroController, etiquetas: EtiquetaController):
        super().__init__()
        self.fichero = fichero
        self.etiquetas = etiquetas
        self.libros: list[dict] = []

        layout = QVBoxLayout(self)
        titulo = QLabel("Fichero e inventario central")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        layout.addWidget(QLabel("Cédulas catalográficas y existencias por área temática y sistema."))

        busqueda = QHBoxLayout()
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar título, autor, ISBN, cota o registro")
        self.filtro.textChanged.connect(self.refrescar_fichas)
        busqueda.addWidget(self.filtro, 1)
        actualizar = QPushButton("Actualizar")
        actualizar.clicked.connect(self.refrescar)
        busqueda.addWidget(actualizar)
        layout.addLayout(busqueda)

        self.seleccion = QLabel()
        layout.addWidget(self.seleccion)
        self.tabla_fichas = QTableWidget(0, 6)
        self.tabla_fichas.setHorizontalHeaderLabels(["ID", "Registro", "Título", "Autor", "Cota", "Sistema"])
        self.tabla_fichas.setColumnHidden(0, True)
        self.tabla_fichas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_fichas.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.tabla_fichas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_fichas.horizontalHeader().setStretchLastSection(True)
        self.tabla_fichas.itemSelectionChanged.connect(self.actualizar_seleccion)
        self.tabla_fichas.setMinimumHeight(220)
        layout.addWidget(self.tabla_fichas, 2)

        acciones = QHBoxLayout()
        self.generar = QPushButton("Generar cédulas PDF")
        self.generar.setEnabled(False)
        self.generar.clicked.connect(self.exportar_fichas)
        acciones.addWidget(self.generar)
        self.generar_matriz = QPushButton("Generar matriz de control por sucursales")
        self.generar_matriz.setEnabled(False)
        self.generar_matriz.clicked.connect(self.exportar_matriz_sucursales)
        acciones.addWidget(self.generar_matriz)
        acciones.addStretch(1)
        layout.addLayout(acciones)

        titulo_inventario = QLabel("Inventario por área y tipo de clasificación")
        titulo_inventario.setObjectName("sectionTitle")
        layout.addWidget(titulo_inventario)
        self.tabla_inventario = QTableWidget(0, 5)
        self.tabla_inventario.setHorizontalHeaderLabels(["Área temática", "Sistema", "Catalogados", "Pendientes / otros", "Cantidad"])
        self.tabla_inventario.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_inventario.horizontalHeader().setStretchLastSection(True)
        self.tabla_inventario.setMinimumHeight(170)
        layout.addWidget(self.tabla_inventario, 1)
        self.refrescar()

    def refrescar(self) -> None:
        self.refrescar_fichas()
        grupos = self.fichero.resumen_inventario()
        self.tabla_inventario.setRowCount(len(grupos))
        for fila, grupo in enumerate(grupos):
            valores = (grupo["area"], grupo["sistema"], grupo["catalogados"], grupo["pendientes"], grupo["total"])
            for columna, valor in enumerate(valores):
                self.tabla_inventario.setItem(fila, columna, QTableWidgetItem(str(valor)))
        self.tabla_inventario.resizeColumnsToContents()

    def refrescar_fichas(self, *_args) -> None:
        self.libros = self.fichero.buscar(self.filtro.text())
        self.tabla_fichas.setRowCount(len(self.libros))
        for fila, libro in enumerate(self.libros):
            valores = (libro["id"], libro["numero_registro"], libro["titulo"], libro["autor"], libro["cota"], libro["sistema"])
            for columna, valor in enumerate(valores):
                self.tabla_fichas.setItem(fila, columna, QTableWidgetItem(str(valor or "")))
        self.tabla_fichas.resizeColumnsToContents()
        self.actualizar_seleccion()

    def actualizar_seleccion(self) -> None:
        filas = {item.row() for item in self.tabla_fichas.selectedItems()}
        cantidad = len(filas)
        self.seleccion.setText(f"{cantidad} seleccionados | mínimo {self.MINIMO_FICHAS} para imprimir una hoja")
        self.generar.setEnabled(cantidad >= self.MINIMO_FICHAS)
        self.generar_matriz.setEnabled(cantidad == 1)

    def exportar_fichas(self) -> None:
        filas = sorted({item.row() for item in self.tabla_fichas.selectedItems()})
        if len(filas) < self.MINIMO_FICHAS:
            QMessageBox.information(self, "Fichero", "Seleccione al menos cuatro libros catalogados.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar cédulas", "cedulas_libros.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        libros = [self.libros[fila] for fila in filas]
        try:
            self.etiquetas.exportar_fichas(libros, ruta)
            QMessageBox.information(self, "Fichero", f"Cédulas generadas:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "Fichero", str(error))

    def exportar_matriz_sucursales(self) -> None:
        filas = sorted({item.row() for item in self.tabla_fichas.selectedItems()})
        if len(filas) != 1:
            QMessageBox.information(self, "Fichero", "Seleccione un solo libro catalogado.")
            return
        libro = self.libros[filas[0]]
        ficha = self.fichero.obtener_matriz_sucursales(int(libro["id"]))
        if ficha is None:
            QMessageBox.warning(self, "Fichero", "El libro seleccionado ya no está disponible.")
            self.refrescar()
            return
        registro = str(ficha.get("numero_registro") or "libro")
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar matriz de control por sucursales",
            f"matriz_sucursales_{registro}.pdf", "PDF (*.pdf)",
        )
        if not ruta:
            return
        try:
            self.etiquetas.exportar_matriz_sucursales(ficha, ruta)
            QMessageBox.information(self, "Fichero", f"Matriz de control generada:\n{ruta}")
        except Exception as error:
            QMessageBox.critical(self, "Fichero", str(error))