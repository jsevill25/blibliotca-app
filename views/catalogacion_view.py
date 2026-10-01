from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from controllers.catalogacion_controller import CatalogacionController


class CatalogacionView(QWidget):
    def __init__(self, controller: CatalogacionController, usuario_id: int):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.libro_id: int | None = None
        layout = QVBoxLayout(self)
        titulo = QLabel("Catalogación pendiente")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar título, autor o ISBN")
        self.filtro.textChanged.connect(self.refrescar)
        layout.addWidget(self.filtro)
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Título", "Autor", "ISBN"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)

        form = QFormLayout()
        self.clasificacion = QComboBox()
        self.clasificacion.addItems(["Dewey", "LC"])
        self.codigo = QLineEdit()
        self.cutter = QLineEdit()
        self.cota = QTextEdit()
        self.cota.setMaximumHeight(70)
        self.anio_actual = ""
        self.codigo.textChanged.connect(self._refrescar_cota)
        self.cutter.textChanged.connect(self._refrescar_cota)
        form.addRow("Sistema", self.clasificacion)
        form.addRow("Clasificación", self.codigo)
        form.addRow("Cutter sugerido", self.cutter)
        form.addRow("Cota completa", self.cota)
        layout.addLayout(form)
        actions = QHBoxLayout()
        sugerir = QPushButton("Sugerir Cutter")
        sugerir.clicked.connect(self.sugerir)
        guardar = QPushButton("Catalogar libro")
        guardar.clicked.connect(self.guardar)
        actions.addWidget(sugerir)
        actions.addWidget(guardar)
        layout.addLayout(actions)
        self.refrescar()

    def refrescar(self, *_args) -> None:
        libros = self.controller.pendientes(self.filtro.text() if hasattr(self, "filtro") else "")
        self.tabla.setRowCount(len(libros))
        for row, libro in enumerate(libros):
            for column, value in enumerate((str(libro.id), libro.titulo, libro.autor, libro.isbn)):
                self.tabla.setItem(row, column, QTableWidgetItem(value))
        self.tabla.resizeColumnsToContents()

    def seleccionar(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        self.libro_id = int(self.tabla.item(fila, 0).text())
        libro = next((item for item in self.controller.pendientes() if item.id == self.libro_id), None)
        if libro:
            self.anio_actual = str(libro.anio or "")
            self.codigo.clear()
            self.cutter.setText(self.controller.sugerir_cutter(libro.autor))
            self._refrescar_cota()

    def sugerir(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        libro_id = int(self.tabla.item(fila, 0).text())
        libro = next((item for item in self.controller.pendientes() if item.id == libro_id), None)
        if libro:
            self.anio_actual = str(libro.anio or "")
            self.cutter.setText(self.controller.sugerir_cutter(libro.autor))
            self._refrescar_cota()

    def _refrescar_cota(self, *_args) -> None:
        self.actualizar_cota(self.anio_actual)

    def actualizar_cota(self, anio) -> None:
        self.cota.setPlainText("\n".join(part for part in (self.codigo.text().strip(), self.cutter.text().strip(), str(anio or "")) if part))

    def guardar(self) -> None:
        if not self.libro_id:
            QMessageBox.warning(self, "Catalogación", "Seleccione un libro pendiente.")
            return
        cota = self.cota.toPlainText()
        ok, mensaje = self.controller.catalogar(
            self.libro_id, self.clasificacion.currentText(), self.codigo.text(),
            self.cutter.text(), cota, self.usuario_id,
        )
        if not ok and "multivolumen" in mensaje and QMessageBox.question(self, "Cota duplicada", f"{mensaje}\n¿Continuar de todos modos?") == QMessageBox.StandardButton.Yes:
            ok, mensaje = self.controller.catalogar(
                self.libro_id, self.clasificacion.currentText(), self.codigo.text(),
                self.cutter.text(), cota, self.usuario_id, permitir_cota_duplicada=True,
            )
        if not ok:
            QMessageBox.warning(self, "Catalogación", mensaje)
            return
        QMessageBox.information(self, "Catalogación", mensaje)
        self.libro_id = None
        self.refrescar()