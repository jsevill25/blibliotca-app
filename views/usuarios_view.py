from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.auth_controller import AuthController


class UsuariosView(QWidget):
    def __init__(self, controller: AuthController, usuario_id: int):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.usuario_seleccionado: int | None = None
        layout = QVBoxLayout(self)
        titulo = QLabel("Administración de usuarios")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        form = QFormLayout()
        self.username = QLineEdit()
        self.nombre = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.rol = QComboBox()
        self.rol.addItem("Bibliotecario", "bibliotecario")
        self.rol.addItem("Administrador", "admin")
        form.addRow("Usuario", self.username)
        form.addRow("Nombre completo", self.nombre)
        form.addRow("Contraseña inicial", self.password)
        form.addRow("Rol", self.rol)
        layout.addLayout(form)
        acciones = QHBoxLayout()
        crear = QPushButton("Crear usuario")
        crear.clicked.connect(self.crear)
        actualizar = QPushButton("Guardar cambios")
        actualizar.clicked.connect(self.actualizar)
        estado = QPushButton("Activar / desactivar")
        estado.clicked.connect(self.cambiar_estado)
        acciones.addWidget(crear)
        acciones.addWidget(actualizar)
        acciones.addWidget(estado)
        layout.addLayout(acciones)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre", "Rol", "Estado"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self.seleccionar)
        layout.addWidget(self.tabla, 1)
        self.refrescar()

    def refrescar(self) -> None:
        usuarios = self.controller.listar_usuarios(self.usuario_id)
        self.tabla.setRowCount(len(usuarios))
        for row, user in enumerate(usuarios):
            for column, value in enumerate((str(user.id), user.username, user.nombre_completo, user.rol, "Activo" if user.activo else "Inactivo")):
                self.tabla.setItem(row, column, QTableWidgetItem(value))
        self.tabla.resizeColumnsToContents()

    def seleccionar(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            self.usuario_seleccionado = None
            return
        self.usuario_seleccionado = int(self.tabla.item(fila, 0).text())
        self.username.setText(self.tabla.item(fila, 1).text())
        self.nombre.setText(self.tabla.item(fila, 2).text())
        self.rol.setCurrentIndex(max(0, self.rol.findData(self.tabla.item(fila, 3).text())))
        self.password.clear()

    def crear(self) -> None:
        exito, mensaje = self.controller.crear_usuario(
            self.username.text(), self.nombre.text(), self.password.text(), self.rol.currentData(), self.usuario_id,
        )
        if not exito:
            QMessageBox.warning(self, "Usuarios", mensaje)
            return
        QMessageBox.information(self, "Usuarios", mensaje)
        self.username.clear()
        self.nombre.clear()
        self.password.clear()
        self.usuario_seleccionado = None
        self.refrescar()

    def actualizar(self) -> None:
        if self.usuario_seleccionado is None:
            return
        exito, mensaje = self.controller.actualizar_usuario(
            self.usuario_seleccionado, self.username.text(), self.nombre.text(),
            self.rol.currentData(), self.password.text(), self.usuario_id,
        )
        (QMessageBox.information if exito else QMessageBox.warning)(self, "Usuarios", mensaje)
        self.refrescar()

    def cambiar_estado(self) -> None:
        if self.usuario_seleccionado is None:
            return
        user = next((item for item in self.controller.listar_usuarios(self.usuario_id) if item.id == self.usuario_seleccionado), None)
        if user is None:
            return
        exito, mensaje = self.controller.cambiar_estado_usuario(user.id, not user.activo, self.usuario_id)
        (QMessageBox.information if exito else QMessageBox.warning)(self, "Usuarios", mensaje)
        self.refrescar()