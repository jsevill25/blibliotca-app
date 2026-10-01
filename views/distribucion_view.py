from PySide6.QtWidgets import QFileDialog, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from controllers.distribucion_controller import DistribucionController
from controllers.etiqueta_controller import EtiquetaController


class DistribucionView(QWidget):
    def __init__(self, controller: DistribucionController, usuario_id: int):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.etiquetas = EtiquetaController()
        layout = QVBoxLayout(self)
        titulo = QLabel("Distribución a bibliotecas")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        form = QFormLayout()
        self.destino = QComboBox()
        self.bibliotecas = self.controller.listar_bibliotecas()
        self._cargar_destinos()
        self.genero = QLineEdit()
        self.observaciones = QTextEdit()
        self.observaciones.setMaximumHeight(65)
        form.addRow("Biblioteca destino", self.destino)
        form.addRow("Género / tipo", self.genero)
        form.addRow("Observaciones", self.observaciones)
        layout.addLayout(form)
        self.filtro = QLineEdit()
        self.filtro.setPlaceholderText("Buscar libros catalogados")
        self.filtro.textChanged.connect(self.refrescar)
        layout.addWidget(self.filtro)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Título", "Autor", "Cota", "Registro"])
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)
        acciones = QHBoxLayout()
        enviar = QPushButton("Crear envío")
        enviar.clicked.connect(self.enviar)
        actualizar = QPushButton("Actualizar libros")
        actualizar.clicked.connect(self.refrescar)
        actualizar_sucursales = QPushButton("Actualizar sucursales")
        actualizar_sucursales.clicked.connect(self._cargar_destinos)
        acciones.addWidget(enviar)
        acciones.addWidget(actualizar)
        acciones.addWidget(actualizar_sucursales)
        layout.addLayout(acciones)
        self.refrescar()

    def refrescar(self, *_args) -> None:
        libros = self.controller.libros_disponibles(self.filtro.text() if hasattr(self, "filtro") else "")
        self.tabla.setRowCount(len(libros))
        for row, libro in enumerate(libros):
            for column, valor in enumerate((str(libro.id), libro.titulo, libro.autor, libro.cota, libro.numero_registro)):
                self.tabla.setItem(row, column, QTableWidgetItem(valor))
        self.tabla.resizeColumnsToContents()

    def _cargar_destinos(self) -> None:
        seleccionado = self.destino.currentData() if hasattr(self, "destino") else None
        self.destino.clear()
        self.bibliotecas = self.controller.listar_bibliotecas()
        for biblioteca in self.bibliotecas:
            if biblioteca.nombre != "Biblioteca Central Rómulo Gallegos":
                self.destino.addItem(biblioteca.nombre, biblioteca.id)
        if seleccionado is not None:
            indice = self.destino.findData(seleccionado)
            if indice >= 0:
                self.destino.setCurrentIndex(indice)

    def enviar(self) -> None:
        filas = sorted({item.row() for item in self.tabla.selectedItems()})
        if not filas or self.destino.currentData() is None:
            QMessageBox.warning(self, "Distribución", "Seleccione la sucursal y uno o más libros.")
            return
        ids = [int(self.tabla.item(row, 0).text()) for row in filas]
        exito, mensaje = self.controller.crear_bulto(self.destino.currentData(), ids, self.usuario_id, self.genero.text(), self.observaciones.toPlainText())
        if not exito:
            QMessageBox.warning(self, "Distribución", mensaje)
            return
        QMessageBox.information(self, "Envío creado", f"Código de envío: {mensaje}")
        if QMessageBox.question(self, "Documentos de envío", "¿Desea generar el documento de envío y la mini-ficha para la caja?") == QMessageBox.StandardButton.Yes:
            self.exportar_documentos(mensaje)
        self.refrescar()

    def exportar_documentos(self, codigo: str) -> None:
        datos = self.controller.obtener_envio(codigo)
        if datos is None:
            QMessageBox.warning(self, "Envío", "No se encontró el envío generado.")
            return
        bulto, libros = datos
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar documento de envío", f"{codigo}.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        try:
            self.etiquetas.exportar_envio(bulto, libros, ruta)
            ruta_mini, _ = QFileDialog.getSaveFileName(self, "Guardar mini-ficha", f"{codigo}_caja.pdf", "PDF (*.pdf)")
            if ruta_mini:
                self.etiquetas.exportar_mini_ficha(bulto, ruta_mini)
            QMessageBox.information(self, "Documentos", "Documentos generados correctamente.")
        except Exception as error:
            QMessageBox.critical(self, "Documentos", str(error))