from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.recepcion_controller import RecepcionController


class RecepcionView(QWidget):
    def __init__(self, controller: RecepcionController, usuario_id: int):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.libro_id: int | None = None
        layout = QVBoxLayout(self)
        titulo = QLabel("Recepción de libros")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)

        form = QFormLayout()
        self.fields = {name: QLineEdit() for name in ("titulo", "autor", "isbn", "editorial", "anio", "edicion", "paginas", "numero_volumenes", "precio_unitario", "idioma", "procedencia_detalle", "donante_nombre", "proveedor_nombre", "institucion_origen", "observaciones")}
        self.fields["titulo"].setPlaceholderText("Título del libro")
        self.procedencia = QComboBox()
        self.procedencia.addItem("Donación", "donacion")
        self.procedencia.addItem("Compra", "compra")
        self.procedencia.addItem("Biblioteca Nacional", "biblioteca_nacional")
        form.addRow("Procedencia", self.procedencia)
        labels = {"titulo": "Título *", "autor": "Autor", "isbn": "ISBN", "editorial": "Editorial", "anio": "Año", "edicion": "Edición", "paginas": "Páginas", "numero_volumenes": "N° de volúmenes (opcional)", "precio_unitario": "Precio unitario (Bs., opcional)", "idioma": "Idioma", "procedencia_detalle": "Detalle de procedencia", "donante_nombre": "Donante", "proveedor_nombre": "Proveedor", "institucion_origen": "Institución de origen", "observaciones": "Observaciones"}
        self.labels_procedencia = {}
        for key, field in self.fields.items():
            form.addRow(labels[key], field)
            self.labels_procedencia[key] = form.labelForField(field)
        self.procedencia.currentIndexChanged.connect(self._actualizar_campos_procedencia)
        self._actualizar_campos_procedencia()
        layout.addLayout(form)

        actions = QHBoxLayout()
        guardar = QPushButton("Registrar / guardar cambios")
        guardar.clicked.connect(self.guardar)
        limpiar = QPushButton("Limpiar formulario")
        limpiar.clicked.connect(self.limpiar)
        actions.addWidget(guardar)
        actions.addWidget(limpiar)
        layout.addLayout(actions)

        filtros = QHBoxLayout()
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar por título, autor o ISBN")
        self.filtro.textChanged.connect(self.refrescar)
        self.filtro_procedencia = QComboBox()
        self.filtro_procedencia.addItem("Todas las procedencias", "")
        self.filtro_procedencia.addItem("Donación", "donacion")
        self.filtro_procedencia.addItem("Compra", "compra")
        self.filtro_procedencia.addItem("Biblioteca Nacional", "biblioteca_nacional")
        self.filtro_procedencia.currentIndexChanged.connect(self.refrescar)
        fecha_minima = QDate(1900, 1, 1)
        self.filtro_desde = QDateEdit(fecha_minima)
        self.filtro_hasta = QDateEdit(fecha_minima)
        for selector in (self.filtro_desde, self.filtro_hasta):
            selector.setCalendarPopup(True)
            selector.setMinimumDate(fecha_minima)
            selector.setMaximumDate(QDate.currentDate())
            selector.setSpecialValueText("Sin límite")
            selector.dateChanged.connect(self.refrescar)
        self.filtro_desde.setDisplayFormat("dd/MM/yyyy")
        self.filtro_hasta.setDisplayFormat("dd/MM/yyyy")
        self.filtro_desde.setToolTip("Fecha inicial; 1900 significa sin límite")
        self.filtro_hasta.setToolTip("Fecha final; 1900 significa sin límite")
        filtros.addWidget(self.filtro)
        filtros.addWidget(self.filtro_procedencia)
        filtros.addWidget(self.filtro_desde)
        filtros.addWidget(self.filtro_hasta)
        layout.addLayout(filtros)
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Título", "Autor", "Registro", "Estado", "Procedencia"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)
        self.refrescar()

    def refrescar(self, *_args) -> None:
        desde = self.filtro_desde.date().toPython() if hasattr(self, "filtro_desde") and self.filtro_desde.date() != self.filtro_desde.minimumDate() else None
        hasta = self.filtro_hasta.date().toPython() if hasattr(self, "filtro_hasta") and self.filtro_hasta.date() != self.filtro_hasta.minimumDate() else None
        libros = self.controller.listar(
            texto=self.filtro.text() if hasattr(self, "filtro") else "",
            procedencia=self.filtro_procedencia.currentData() if hasattr(self, "filtro_procedencia") else "",
            inicio=desde, fin=hasta,
        )
        self.tabla.setRowCount(len(libros))
        for row, libro in enumerate(libros):
            valores = (str(libro.id), libro.titulo, libro.autor, libro.numero_registro, libro.estado, libro.procedencia)
            for column, value in enumerate(valores):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, libro.id)
                self.tabla.setItem(row, column, item)
        self.tabla.resizeColumnsToContents()

    def _actualizar_campos_procedencia(self, *_args) -> None:
        procedencia = self.procedencia.currentData()
        campos = {
            "donante_nombre": procedencia == "donacion",
            "proveedor_nombre": procedencia == "compra",
            "institucion_origen": procedencia == "biblioteca_nacional",
        }
        for nombre, visible in campos.items():
            self.fields[nombre].setVisible(visible)
            etiqueta = self.labels_procedencia.get(nombre)
            if etiqueta:
                etiqueta.setVisible(visible)

    def seleccionar(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        self.libro_id = int(self.tabla.item(fila, 0).text())
        libro = next((item for item in self.controller.listar() if item.id == self.libro_id), None)
        if libro is None:
            return
        self.procedencia.setCurrentIndex(max(0, self.procedencia.findData(libro.procedencia)))
        valores = {
            "titulo": libro.titulo, "autor": libro.autor, "isbn": libro.isbn, "editorial": libro.editorial,
            "anio": libro.anio or "", "edicion": libro.edicion, "paginas": libro.paginas or "", "idioma": libro.idioma,
            "numero_volumenes": libro.numero_volumenes if libro.numero_volumenes is not None else "",
            "precio_unitario": libro.precio_unitario if libro.precio_unitario is not None else "",
            "procedencia_detalle": libro.procedencia_detalle, "observaciones": libro.observaciones,
        }
        if libro.recepcion:
            valores.update({
                "donante_nombre": libro.recepcion.donante_nombre,
                "proveedor_nombre": libro.recepcion.proveedor_nombre,
                "institucion_origen": libro.recepcion.institucion_origen,
            })
        for key, value in valores.items():
            self.fields[key].setText(str(value))

    def guardar(self) -> None:
        datos = {key: field.text().strip() for key, field in self.fields.items()}
        datos["procedencia"] = self.procedencia.currentData()
        if self.libro_id:
            exito, mensaje = self.controller.editar(self.libro_id, datos, self.usuario_id)
        else:
            exito, mensaje = self.controller.registrar(datos, self.usuario_id)
        if not exito:
            QMessageBox.warning(self, "Recepción", mensaje)
            return
        QMessageBox.information(self, "Recepción", f"Registro guardado: {mensaje}")
        self.limpiar()
        self.refrescar()

    def limpiar(self) -> None:
        self.libro_id = None
        self.tabla.clearSelection()
        for field in self.fields.values():
            field.clear()
        self.procedencia.setCurrentIndex(0)