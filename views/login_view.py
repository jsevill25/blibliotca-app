from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QLabel

from config import APP_NAME
from controllers.auth_controller import AuthController
from views.theme import apply_theme


class LoginView(QDialog):
    def __init__(self, controller: AuthController):
        super().__init__()
        self.controller = controller
        self.current_user = None
        self.setWindowTitle(f"Iniciar sesión | {APP_NAME}")
        self.setMinimumWidth(390)
        apply_theme(self)

        layout = QVBoxLayout(self)
        title = QLabel("Biblioteca Central\nRómulo Gallegos")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Acceso al sistema bibliotecario"))
        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Nombre de usuario")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Contraseña")
        self.password.returnPressed.connect(self.submit)
        form.addRow("Usuario", self.username)
        form.addRow("Contraseña", self.password)
        layout.addLayout(form)
        button = QPushButton("Iniciar sesión")
        button.clicked.connect(self.submit)
        layout.addWidget(button)

    def submit(self) -> None:
        valido, resultado = self.controller.autenticar(self.username.text(), self.password.text())
        if not valido:
            QMessageBox.warning(self, "Acceso denegado", str(resultado))
            return
        user = resultado
        if user.debe_cambiar_clave:
            clave, ok = self._pedir_clave("Cambio obligatorio", "Nueva contraseña (mínimo 10 caracteres):")
            if not ok:
                return
            confirmacion, ok = self._pedir_clave("Confirmar contraseña", "Repita la nueva contraseña:")
            if not ok:
                return
            if clave != confirmacion:
                QMessageBox.warning(self, "Contraseña", "Las contraseñas no coinciden.")
                return
            cambio, mensaje = self.controller.cambiar_clave(user.id, self.password.text(), clave)
            if not cambio:
                QMessageBox.warning(self, "Contraseña", mensaje)
                return
            valido, resultado = self.controller.autenticar(self.username.text(), clave)
            if not valido:
                QMessageBox.critical(self, "Acceso", "No se pudo validar la nueva contraseña.")
                return
            user = resultado
        self.current_user = user
        self.accept()

    def _pedir_clave(self, titulo: str, texto: str) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog

        return QInputDialog.getText(self, titulo, texto, QLineEdit.EchoMode.Password)