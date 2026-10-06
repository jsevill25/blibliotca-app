from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.biblioteca_controller import BibliotecaController


class BibliotecasView(QWidget):
    actualizadas = Signal()

    def __init__(self, controller: BibliotecaController, usuario_id: int | None = None):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        layout = QVBoxLayout(self)
        titulo = QLabel("Bibliotecas sucursales")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        form = QFormLayout()
        self.nombre = QLineEdit()
        self.direccion = QLineEdit()
        self.municipio = QLineEdit()
        self.encargado = QLineEdit()
        self.telefono = QLineEdit()
        self.email = QLineEdit()
        for label, widget in (("Nombre", self.nombre), ("Dirección", self.direccion), ("Municipio", self.municipio), ("Encargado", self.encargado), ("Teléfono", self.telefono), ("Correo", self.email)):
            form.addRow(label, widget)
        layout.addLayout(form)
        acciones = QHBoxLayout()
        guardar = QPushButton("Registrar sucursal")
        guardar.clicked.connect(self.guardar)
        desactivar = QPushButton("Desactivar seleccionada")
        desactivar.clicked.connect(self.desactivar)
        acciones.addWidget(guardar)
        acciones.addWidget(desactivar)
        layout.addLayout(acciones)
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Dirección", "Municipio", "Encargado", "Teléfono", "Correo"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla, 1)
        self.refrescar()

    def refrescar(self) -> None:
        bibliotecas = self.controller.listar(incluir_inactivas=True)
        self.tabla.setRowCount(len(bibliotecas))
        for row, biblioteca in enumerate(bibliotecas):
            nombre = biblioteca.nombre if biblioteca.activa else f"{biblioteca.nombre} (inactiva)"
            valores = (biblioteca.id, nombre, biblioteca.direccion, biblioteca.municipio, biblioteca.encargado, biblioteca.telefono, biblioteca.email)
            for column, value in enumerate(valores):
                self.tabla.setItem(row, column, QTableWidgetItem(str(value or "")))
        self.tabla.resizeColumnsToContents()

    def guardar(self) -> None:
        exito, mensaje = self.controller.crear(
            self.nombre.text(), self.direccion.text(), self.encargado.text(),
            self.telefono.text(), self.email.text(), self.municipio.text(),
            usuario_id=self.usuario_id, origen="escritorio",
        )
        (QMessageBox.information if exito else QMessageBox.warning)(self, "Bibliotecas", mensaje)
        if exito:
            for campo in (self.nombre, self.direccion, self.municipio, self.encargado, self.telefono, self.email):
                campo.clear()
            self.refrescar()
            self.actualizadas.emit()

    def desactivar(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        exito, mensaje = self.controller.desactivar(
            int(self.tabla.item(fila, 0).text()), self.usuario_id, "escritorio",
        )
        (QMessageBox.information if exito else QMessageBox.warning)(self, "Bibliotecas", mensaje)
        self.refrescar()
        if exito:
            self.actualizadas.emit()