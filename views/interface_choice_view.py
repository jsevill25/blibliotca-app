from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame

from config import APP_NAME
from views.theme import apply_theme


class InterfaceChoiceView(QDialog):
    def __init__(self):
        super().__init__()
        self.mode: str | None = None
        self.setWindowTitle(f"Seleccionar interfaz | {APP_NAME}")
        self.setMinimumWidth(560)
        apply_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(10)

        brand = QLabel("B")
        brand.setObjectName("loginMark")
        brand.setFixedSize(42, 42)
        layout.addWidget(brand)

        title = QLabel("Biblioteca Central\nRómulo Gallegos")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("Elija cómo desea trabajar hoy")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        choices = QHBoxLayout()
        choices.setSpacing(12)
        for mode, heading, description in (
            ("desktop", "Escritorio", "Aplicación instalada\nVentanas y controles Qt"),
            ("web", "Web", "Abrir en el navegador\nMisma cuenta y biblioteca"),
        ):
            panel = QFrame()
            panel.setObjectName("interfaceChoice")
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(14, 14, 14, 14)
            button = QPushButton(f"{heading}\n\n{description}")
            button.setObjectName("interfaceChoiceButton")
            button.setMinimumHeight(112)
            button.clicked.connect(lambda _checked=False, value=mode: self._select(value))
            panel_layout.addWidget(button)
            choices.addWidget(panel)
        layout.addLayout(choices)

        note = QLabel("Puede volver a elegir la interfaz cada vez que inicie el sistema.")
        note.setObjectName("muted")
        layout.addWidget(note)

    def _select(self, mode: str) -> None:
        self.mode = mode
        self.accept()