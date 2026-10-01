from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from config import APP_NAME
from controllers.auth_controller import AuthController
from controllers.backup_controller import BackupController
from controllers.biblioteca_controller import BibliotecaController
from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from controllers.ubicacion_controller import UbicacionController
from database.db_manager import DatabaseManager
from database.models import User
from views.catalogacion_view import CatalogacionView
from views.bibliotecas_view import BibliotecasView
from views.distribucion_view import DistribucionView
from views.etiquetas_view import EtiquetasView
from views.manual_view import ManualView
from views.recepcion_view import RecepcionView
from views.reportes_view import ReportesView
from views.theme import apply_theme
from views.ubicacion_view import UbicacionView
from views.usuarios_view import UsuariosView


class MainWindow(QMainWindow):
    def __init__(self, database: DatabaseManager, user: User):
        super().__init__()
        self.database = database
        self.user = user
        self.setWindowTitle(f"{APP_NAME} | {user.nombre_completo or user.username}")
        self.resize(1280, 820)
        apply_theme(self)
        self.backup = BackupController(database, Path(database.database_path).parent / "backups")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.manual_view = ManualView()
        self.tabs.addTab(self.manual_view, "Manual de uso")
        recepcion = RecepcionController(database)
        catalogacion = CatalogacionController(database)
        ubicacion = UbicacionController(database)
        self.tabs.addTab(RecepcionView(recepcion, user.id), "Recepción")
        self.tabs.addTab(CatalogacionView(catalogacion, user.id), "Catalogación")
        distribucion = DistribucionView(DistribucionController(database), user.id)
        self.tabs.addTab(distribucion, "Distribución")
        self.tabs.addTab(UbicacionView(ubicacion, user.id), "Ubicación y búsqueda")
        self.tabs.addTab(EtiquetasView(ubicacion, __import__("controllers.etiqueta_controller", fromlist=["EtiquetaController"]).EtiquetaController()), "Etiquetas")
        self.tabs.addTab(ReportesView(ReportesController(database), ubicacion, self.backup, database.engine), "Reportes y backup")
        if user.rol == "admin":
            self.tabs.addTab(UsuariosView(AuthController(database), user.id), "Usuarios")
            bibliotecas = BibliotecasView(BibliotecaController(database))
            bibliotecas.actualizadas.connect(distribucion._cargar_destinos)
            self.tabs.addTab(bibliotecas, "Sucursales")
        ayuda = self.menuBar().addMenu("Ayuda")
        abrir_manual = QAction("Abrir manual de usuario", self)
        abrir_manual.triggered.connect(lambda: self.tabs.setCurrentWidget(self.manual_view))
        ayuda.addAction(abrir_manual)
        salir = QAction("Cerrar sesión", self)
        salir.triggered.connect(self.close)
        self.menuBar().addAction(salir)

    def closeEvent(self, event) -> None:
        exito, resultado = self.backup.crear_backup()
        if not exito and QMessageBox.question(self, "Backup fallido", f"No se pudo crear el respaldo: {resultado}\n¿Cerrar de todos modos?") != QMessageBox.StandardButton.Yes:
            event.ignore()
            return
        event.accept()