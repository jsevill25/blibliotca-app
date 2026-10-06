from pathlib import Path

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from config import APP_NAME
from controllers.auth_controller import AuthController
from controllers.backup_controller import BackupController
from controllers.biblioteca_controller import BibliotecaController
from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
from controllers.etiqueta_controller import EtiquetaController
from controllers.fichero_controller import FicheroController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from controllers.ubicacion_controller import UbicacionController
from database.db_manager import DatabaseManager
from database.models import User
from views.catalogacion_view import CatalogacionView
from views.bibliotecas_view import BibliotecasView
from views.distribucion_view import DistribucionView
from views.etiquetas_view import EtiquetasView
from views.fichero_view import FicheroView
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

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(central)

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("sidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setFixedWidth(240)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 14)
        sidebar_layout.setSpacing(6)
        sidebar_scroll.setWidget(sidebar)
        root_layout.addWidget(sidebar_scroll)

        brand = QLabel("BIBLIOTECA CENTRAL")
        brand.setObjectName("sidebarBrand")
        brand.setWordWrap(True)
        sidebar_layout.addWidget(brand)
        user_label = QLabel(f"{user.nombre_completo or user.username}\n{user.rol}")
        user_label.setObjectName("sidebarUser")
        user_label.setWordWrap(True)
        sidebar_layout.addWidget(user_label)
        sidebar_layout.addSpacing(18)

        self.pages = QStackedWidget()
        self.navigation = {}
        root_layout.addWidget(self.pages, 1)

        self.manual_view = ManualView()
        self._add_page("Manual de uso", self.manual_view, sidebar_layout)
        recepcion = RecepcionController(database)
        catalogacion = CatalogacionController(database)
        ubicacion = UbicacionController(database)
        self._add_page("Recepción", RecepcionView(recepcion, user.id), sidebar_layout)
        self._add_page("Catalogación", CatalogacionView(catalogacion, user.id), sidebar_layout)
        etiquetas = EtiquetaController()
        self._add_page("Fichero e inventario", FicheroView(FicheroController(database), etiquetas), sidebar_layout)
        distribucion = DistribucionView(DistribucionController(database), user.id)
        self._add_page("Distribución", distribucion, sidebar_layout)
        self._add_page("Ubicación y búsqueda", UbicacionView(ubicacion, user.id), sidebar_layout)
        self._add_page("Etiquetas de lomo", EtiquetasView(ubicacion, etiquetas), sidebar_layout)
        self._add_page(
            "Reportes y backup",
            ReportesView(
                ReportesController(database), ubicacion, self.backup, database.engine,
                can_export_all=user.rol == "admin",
            ),
            sidebar_layout,
        )
        if user.rol == "admin":
            self._add_page("Usuarios", UsuariosView(AuthController(database), user.id), sidebar_layout)
            bibliotecas = BibliotecasView(BibliotecaController(database))
            bibliotecas.actualizadas.connect(distribucion._cargar_destinos)
            self._add_page("Sucursales", bibliotecas, sidebar_layout)

        sidebar_layout.addStretch(1)
        logout = QPushButton("Cerrar sesión")
        logout.setObjectName("sidebarNav")
        logout.clicked.connect(self.close)
        sidebar_layout.addWidget(logout)
        self._show_page("Manual de uso")

    def _add_page(self, title: str, view: QWidget, sidebar_layout: QVBoxLayout) -> None:
        view.setObjectName("moduleView")
        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        card = QFrame()
        card.setObjectName("contentCard")
        card.setMinimumWidth(0)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        card_layout.addWidget(view)
        scroll.setWidget(card)
        self.pages.addWidget(scroll)

        button = QPushButton(title)
        button.setObjectName("sidebarNav")
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False, page=title: self._show_page(page))
        sidebar_layout.addWidget(button)
        self.navigation[title] = (button, card)

    def _show_page(self, title: str) -> None:
        button, page = self.navigation[title]
        self.pages.setCurrentWidget(page)
        for nav_button, _page in self.navigation.values():
            nav_button.setChecked(nav_button is button)

    def closeEvent(self, event) -> None:
        exito, resultado = self.backup.crear_backup()
        if not exito and QMessageBox.question(self, "Backup fallido", f"No se pudo crear el respaldo: {resultado}\n¿Cerrar de todos modos?") != QMessageBox.StandardButton.Yes:
            event.ignore()
            return
        event.accept()