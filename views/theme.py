from config import COLORS


def apply_theme(widget) -> None:
    widget.setStyleSheet(f"""
        QWidget {{ background: {COLORS['surface']}; color: {COLORS['black']}; font-family: 'Noto Sans', 'Segoe UI', sans-serif; font-size: 10pt; }}
        QMainWindow, QDialog {{ background: {COLORS['surface']}; }}
        QTabWidget::pane {{ border: 1px solid {COLORS['border']}; background: white; }}
        QTabBar::tab {{ background: {COLORS['black']}; color: white; padding: 9px 16px; margin-right: 2px; }}
        QTabBar::tab:selected {{ background: {COLORS['yellow']}; color: {COLORS['black']}; font-weight: bold; }}
        QLineEdit, QComboBox, QSpinBox, QTableWidget, QTextEdit {{ background: white; border: 1px solid {COLORS['border']}; padding: 5px; selection-background-color: {COLORS['yellow']}; selection-color: {COLORS['black']}; }}
        QHeaderView::section {{ background: {COLORS['black']}; color: {COLORS['yellow']}; padding: 6px; border: 0; font-weight: bold; }}
        QPushButton {{ background: {COLORS['black']}; color: white; border: 1px solid {COLORS['black']}; padding: 8px 12px; font-weight: bold; }}
        QPushButton:hover {{ background: #333333; }}
        QPushButton:disabled {{ background: #888888; }}
        QLabel#pageTitle {{ font-size: 16pt; font-weight: bold; }}
        QLabel#muted {{ color: {COLORS['gray']}; }}
    """)