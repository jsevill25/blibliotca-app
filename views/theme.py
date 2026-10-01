from config import COLORS


def apply_theme(widget) -> None:
    widget.setStyleSheet(f"""
        QWidget {{ background: {COLORS['surface']}; color: {COLORS['black']}; font-family: 'Noto Sans', 'Segoe UI', sans-serif; font-size: 10pt; }}
        QMainWindow, QDialog {{ background: {COLORS['surface']}; }}
        QLabel {{ background: transparent; }}
        QFrame#sidebar {{ background: {COLORS['black']}; border-right: 2px solid {COLORS['yellow']}; }}
        QLabel#sidebarBrand {{ background: transparent; color: {COLORS['white']}; font-size: 12pt; font-weight: bold; }}
        QLabel#sidebarUser {{ background: transparent; color: #D1D5DB; }}
        QPushButton#sidebarNav {{ background: transparent; color: #D1D5DB; border: 0; border-radius: 4px; padding: 10px 12px; text-align: left; }}
        QPushButton#sidebarNav:hover {{ background: #262626; color: {COLORS['white']}; }}
        QPushButton#sidebarNav:checked {{ background: #262626; color: {COLORS['yellow']}; font-weight: bold; border-left: 3px solid {COLORS['yellow']}; }}
        QFrame#contentCard {{ background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-top: 3px solid {COLORS['yellow']}; border-radius: 6px; }}
        QWidget#moduleView {{ background: transparent; }}
        QLineEdit, QComboBox, QSpinBox, QTableWidget, QTextEdit {{ background: {COLORS['white']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 5px; selection-background-color: {COLORS['yellow']}; selection-color: {COLORS['black']}; }}
        QHeaderView::section {{ background: {COLORS['black']}; color: {COLORS['yellow']}; padding: 6px; border: 0; font-weight: bold; }}
        QPushButton {{ background: {COLORS['yellow']}; color: {COLORS['black']}; border: 1px solid {COLORS['yellow']}; border-radius: 4px; padding: 8px 12px; font-weight: bold; }}
        QPushButton:hover {{ background: #FACC15; border-color: #FACC15; }}
        QPushButton:disabled {{ background: #D1D5DB; color: #6B7280; border-color: #D1D5DB; }}
        QLabel#pageTitle {{ font-size: 16pt; font-weight: bold; }}
        QLabel#muted {{ color: {COLORS['gray']}; }}
    """)