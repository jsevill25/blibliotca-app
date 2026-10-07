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
        self.clasificacion.currentTextChanged.connect(self._sincronizar_codigo_por_genero)
        self.modo_cota = QComboBox()
        self.modo_cota.addItems(["Manual", "Automática"])
        self.codigo = QLineEdit()
        self.cutter = QLineEdit()
        self.cota = QTextEdit()
        self.cota.setMaximumHeight(110)
        self.genero = QComboBox()
        self.genero.addItems([
            "No ficción", "Biografía individual", "Biografía colectiva",
            "Novela", "Poesía", "Teatro", "Ensayo", "Matemática", "Tecnología",
        ])
        self.genero.currentTextChanged.connect(self._sincronizar_codigo_por_genero)
        self.numero_autores = QLineEdit()
        self.seccion = QComboBox()
        self.seccion.addItems(["General", "Referencia", "Infantil", "Juvenil"])
        self.nacionalidad = QLineEdit()
        self.material = QComboBox()
        self.material.addItems(["Otro", "Música escrita"])
        self.alto = QLineEdit()
        self.ancho = QLineEdit()
        self.biografiado = QLineEdit()
        self.tomo = QLineEdit()
        self.tipo_tomo = QComboBox()
        self.tipo_tomo.addItems(["v", "t"])
        self.anio_actual = ""
        self.codigo.textChanged.connect(self._refrescar_cota)
        self.cutter.textChanged.connect(self._refrescar_cota)
        self.modo_cota.currentTextChanged.connect(self._cambio_modo)
        form.addRow("Modo de cota", self.modo_cota)
        form.addRow("Sistema", self.clasificacion)
        form.addRow("Clasificación", self.codigo)
        form.addRow("Cutter sugerido", self.cutter)
        form.addRow("Género", self.genero)
        form.addRow("Sección", self.seccion)
        form.addRow("Número de autores", self.numero_autores)
        form.addRow("Nacionalidad del autor", self.nacionalidad)
        form.addRow("Tipo de material", self.material)
        form.addRow("Alto (cm)", self.alto)
        form.addRow("Ancho (cm)", self.ancho)
        form.addRow("Personaje biografiado", self.biografiado)
        form.addRow("Número de volumen/tomo", self.tomo)
        form.addRow("Numeración", self.tipo_tomo)
        form.addRow("Cota completa (editable)", self.cota)
        layout.addLayout(form)
        actions = QHBoxLayout()
        sugerir = QPushButton("Sugerir Cutter")
        sugerir.clicked.connect(self.sugerir)
        generar = QPushButton("Generar cota automática")
        generar.clicked.connect(self.generar_cota)
        guardar = QPushButton("Catalogar libro")
        guardar.clicked.connect(self.guardar)
        actions.addWidget(sugerir)
        actions.addWidget(generar)
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
            self.genero.setCurrentIndex(0)
            self.seccion.setCurrentIndex(0)
            self.material.setCurrentIndex(0)
            self._sincronizar_codigo_por_genero()
            self.numero_autores.clear()
            self.nacionalidad.clear()
            self.material.setCurrentIndex(0)
            self.alto.clear()
            self.ancho.clear()
            self.biografiado.clear()
            self.tomo.clear()
            self.cota.clear()
            self.cutter.setText(self.controller.sugerir_cutter(libro.autor))
            if self.modo_cota.currentText() == "Automática":
                self.generar_cota()
            else:
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

    def _sincronizar_codigo_por_genero(self, *_args) -> None:
        if self.clasificacion.currentText() != "Dewey":
            return
        sugerencia = self.controller.sugerir_datos_por_genero(self.genero.currentText())
        if sugerencia["codigo"]:
            self.codigo.setText(sugerencia["codigo"])
        elif not self.codigo.text().strip():
            self.codigo.clear()
        if sugerencia["seccion"] and self.seccion.currentText() == "General":
            self.seccion.setCurrentText(sugerencia["seccion"])
        if sugerencia["material"] and self.material.currentText() == "Otro":
            self.material.setCurrentText(sugerencia["material"])

    def _refrescar_cota(self, *_args) -> None:
        if self.modo_cota.currentText() == "Manual":
            self.actualizar_cota(self.anio_actual)

    def _cambio_modo(self, modo: str) -> None:
        if modo == "Automática" and self.libro_id:
            self.generar_cota()

    def generar_cota(self) -> None:
        if not self.libro_id:
            QMessageBox.warning(self, "Catalogación", "Seleccione un libro pendiente.")
            return
        try:
            if self.clasificacion.currentText() == "Dewey":
                sugerido = self.controller.sugerir_codigo_dewey_por_genero(self.genero.currentText())
                if sugerido and not self.codigo.text().strip():
                    self.codigo.setText(sugerido)
            resultado = self.controller.generar_cota_automatica(self.libro_id, self.codigo.text(), {
                "genero": self.genero.currentText(), "seccion": self.seccion.currentText(),
                "numero_autores": self.numero_autores.text(),
                "nacionalidad": self.nacionalidad.text(), "material": self.material.currentText(),
                "alto": self.alto.text(), "ancho": self.ancho.text(),
                "biografiado": self.biografiado.text(), "tomo": self.tomo.text(),
                "tipo_tomo": self.tipo_tomo.currentText(),
            })
        except ValueError as error:
            QMessageBox.warning(self, "Generación de cota", str(error))
            return
        self.cutter.setText(resultado["cutter"])
        self.cota.setPlainText(resultado["cota"])

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