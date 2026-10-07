from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.reportes_controller import ReportesController


class DashboardView(QWidget):
    def __init__(self, reportes: ReportesController):
        super().__init__()
        self.reportes = reportes
        layout = QVBoxLayout(self)

        titulo = QLabel("Panel principal")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        self.resumen = QLabel()
        layout.addWidget(self.resumen)

        actualizar = QPushButton("Actualizar estadísticas")
        actualizar.clicked.connect(self.actualizar)
        layout.addWidget(actualizar)

        layout.addWidget(QLabel("Existencias por biblioteca"))
        self.tabla_bibliotecas = QTableWidget(0, 7)
        self.tabla_bibliotecas.setHorizontalHeaderLabels([
            "Biblioteca", "Municipio", "Registros con stock", "Ejemplares", "Recibidos", "Catalogados", "Distribuidos",
        ])
        self.tabla_bibliotecas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_bibliotecas.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_bibliotecas.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla_bibliotecas, 1)

        layout.addWidget(QLabel("Registros recientes de libros"))
        self.tabla_libros = QTableWidget(0, 7)
        self.tabla_libros.setHorizontalHeaderLabels([
            "N° de registro", "Título", "Autor", "Estado", "Fecha de ingreso", "Cantidad registrada", "Ejemplares en bibliotecas",
        ])
        self.tabla_libros.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_libros.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_libros.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla_libros, 1)

        self.actualizar()

    def actualizar(self, *_args) -> None:
        datos = self.reportes.estadisticas_panel()
        bibliotecas = datos["bibliotecas"]
        registros = sum(fila["registros"] for fila in bibliotecas)
        ejemplares = sum(fila["ejemplares"] for fila in bibliotecas)
        pendientes = sum(fila["recibidos"] for fila in bibliotecas)
        self.resumen.setText(
            f"Bibliotecas activas: {len(bibliotecas)}  |  Registros con existencias: {registros}  |  "
            f"Ejemplares en inventario: {ejemplares}  |  Pendientes de catalogación: {pendientes}"
        )

        self.tabla_bibliotecas.setRowCount(len(bibliotecas))
        for row, biblioteca in enumerate(bibliotecas):
            valores = (
                biblioteca["nombre"], biblioteca["municipio"], biblioteca["registros"],
                biblioteca["ejemplares"], biblioteca["recibidos"], biblioteca["catalogados"],
                biblioteca["distribuidos"],
            )
            for column, valor in enumerate(valores):
                self.tabla_bibliotecas.setItem(row, column, QTableWidgetItem(str(valor)))
        self.tabla_bibliotecas.resizeColumnsToContents()

        libros = datos["libros"]
        self.tabla_libros.setRowCount(len(libros))
        for row, libro in enumerate(libros):
            valores = (
                libro["registro"], libro["titulo"], libro["autor"], libro["estado"],
                libro["fecha"], libro["cantidad_registrada"], libro["ejemplares_en_bibliotecas"],
            )
            for column, valor in enumerate(valores):
                self.tabla_libros.setItem(row, column, QTableWidgetItem(str(valor)))
        self.tabla_libros.resizeColumnsToContents()
