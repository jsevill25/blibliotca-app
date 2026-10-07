from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.ubicacion_controller import UbicacionController


class UbicacionView(QWidget):
    ESTADOS = ["Todos", "recibido", "en_catalogacion", "catalogado", "distribuido", "prestado"]

    def __init__(self, controller: UbicacionController, usuario_id: int | None = None):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        layout = QVBoxLayout(self)
        titulo = QLabel("Búsqueda global y ubicación")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        filtros = QHBoxLayout()
        self.busqueda = QLineEdit()
        self.busqueda.setPlaceholderText("Título, autor, ISBN, cota o número de registro")
        self.busqueda.returnPressed.connect(self.refrescar)
        self.estado = QComboBox()
        self.estado.addItems(self.ESTADOS)
        self.filtro_biblioteca = QComboBox()
        self.filtro_biblioteca.addItem("Todas las bibliotecas", None)
        for biblioteca in self.controller.listar_bibliotecas():
            self.filtro_biblioteca.addItem(biblioteca.nombre, biblioteca.id)
        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItem("Todos los tipos", "")
        self.filtro_tipo.addItem("Sala", "sala")
        self.filtro_tipo.addItem("Depósito", "deposito")
        self.filtro_tipo.addItem("Biblioteca destino", "biblioteca_distribucion")
        self.filtro_sala = QLineEdit()
        self.filtro_sala.setPlaceholderText("Sala")
        self.filtro_estante = QLineEdit()
        self.filtro_estante.setPlaceholderText("Estante")
        buscar = QPushButton("Buscar")
        buscar.clicked.connect(self.refrescar)
        detalle = QPushButton("Historial de movimientos")
        detalle.clicked.connect(self.mostrar_historial)
        filtros.addWidget(self.busqueda, 1)
        filtros.addWidget(self.estado)
        filtros.addWidget(self.filtro_biblioteca)
        filtros.addWidget(self.filtro_tipo)
        filtros.addWidget(self.filtro_sala)
        filtros.addWidget(self.filtro_estante)
        filtros.addWidget(buscar)
        filtros.addWidget(detalle)
        layout.addLayout(filtros)
        ubicacion_form = QFormLayout()
        self.biblioteca_nueva = QComboBox()
        self.tipo_nuevo = QComboBox()
        self.tipo_nuevo.addItem("Sala", "sala")
        self.tipo_nuevo.addItem("Depósito", "deposito")
        self.sala_nueva = QLineEdit()
        self.estante_nuevo = QLineEdit()
        for biblioteca in self.controller.listar_bibliotecas():
            self.biblioteca_nueva.addItem(biblioteca.nombre, biblioteca.id)
        ubicacion_form.addRow("Biblioteca", self.biblioteca_nueva)
        ubicacion_form.addRow("Tipo", self.tipo_nuevo)
        ubicacion_form.addRow("Sala", self.sala_nueva)
        ubicacion_form.addRow("Estante", self.estante_nuevo)
        layout.addLayout(ubicacion_form)
        asignar = QPushButton("Actualizar ubicación del libro seleccionado")
        asignar.clicked.connect(self.actualizar_ubicacion)
        layout.addWidget(asignar)
        self.tabla = QTableWidget(0, 10)
        self.tabla.setHorizontalHeaderLabels(["ID", "Registro", "Título", "Autor", "Cota", "Estado", "Biblioteca", "Sala", "Estante", "Último movimiento"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)
        self.refrescar()

    def refrescar(self) -> None:
        estado = self.estado.currentText()
        filas = self.controller.buscar(
            self.busqueda.text(), "" if estado == "Todos" else estado,
            self.filtro_biblioteca.currentData(), self.filtro_tipo.currentData(),
            self.filtro_sala.text(), self.filtro_estante.text(),
        )
        self.tabla.setRowCount(len(filas))
        for row, info in enumerate(filas):
            libro = info["libro"]
            movimiento = info["ultimo_movimiento"]
            ultimo = f"{movimiento.fecha:%Y-%m-%d} {movimiento.tipo_movimiento}" if movimiento else "Sin movimientos"
            valores = (
                str(libro.id), libro.numero_registro, libro.titulo, libro.autor,
                libro.cota or "", libro.estado, info["biblioteca"], info["sala"],
                info["estante"], ultimo,
            )
            for column, valor in enumerate(valores):
                self.tabla.setItem(row, column, QTableWidgetItem(str(valor or "")))
        self.tabla.resizeColumnsToContents()

    def actualizar_ubicacion(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Ubicación", "Seleccione un libro.")
            return
        exito, mensaje = self.controller.actualizar_ubicacion(
            int(self.tabla.item(fila, 0).text()), self.biblioteca_nueva.currentData(),
            self.tipo_nuevo.currentData(), self.sala_nueva.text(), self.estante_nuevo.text(), self.usuario_id,
        )
        (QMessageBox.information if exito else QMessageBox.warning)(self, "Ubicación", mensaje)
        if exito:
            self.refrescar()

    def mostrar_historial(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Historial", "Seleccione un libro.")
            return
        libro_id = int(self.tabla.item(fila, 0).text())
        historial = self.controller.historial(libro_id)
        detalle = "\n".join(f"{mov.fecha:%Y-%m-%d %H:%M} | {mov.tipo_movimiento} | {mov.origen} → {mov.destino} | {mov.detalle}" for mov in historial)
        QMessageBox.information(self, "Historial del libro", detalle or "Sin movimientos registrados.")