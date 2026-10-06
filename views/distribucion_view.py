from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from controllers.distribucion_controller import DistribucionController
from controllers.etiqueta_controller import EtiquetaController


class DistribucionView(QWidget):
    def __init__(self, controller: DistribucionController, usuario_id: int):
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.etiquetas = EtiquetaController(controller.database, usuario_id)
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
        self.codigo_consulta = QLineEdit()
        self.codigo_consulta.setPlaceholderText("Código ENV-AAAAMMDD-NNN")
        consultar_envio = QPushButton("Consultar envío y generar control")
        consultar_envio.clicked.connect(self.consultar_envio)
        self.envios_combo = QComboBox()
        self.envios_combo.setMinimumWidth(280)
        actualizar_envios = QPushButton("Actualizar envíos")
        actualizar_envios.clicked.connect(self.actualizar_envios)
        nota_entrega = QPushButton("Nota de entrega del envío seleccionado")
        nota_entrega.clicked.connect(self.nota_entrega_seleccionada)
        acciones.addWidget(enviar)
        acciones.addWidget(self.codigo_consulta)
        acciones.addWidget(consultar_envio)
        acciones.addWidget(self.envios_combo)
        acciones.addWidget(nota_entrega)
        acciones.addWidget(actualizar_envios)
        acciones.addWidget(actualizar)
        acciones.addWidget(actualizar_sucursales)
        layout.addLayout(acciones)
        self.actualizar_envios()
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
        if QMessageBox.question(self, "Documentos de envío", "¿Desea generar el control institucional de envío y la mini-ficha para la caja?") == QMessageBox.StandardButton.Yes:
            self.exportar_documentos(mensaje)
        self.actualizar_envios(mensaje)
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
            self.etiquetas.exportar_control_envio(bulto, libros, ruta)
            ruta_mini, _ = QFileDialog.getSaveFileName(self, "Guardar mini-ficha", f"{codigo}_caja.pdf", "PDF (*.pdf)")
            if ruta_mini:
                self.etiquetas.exportar_mini_ficha(bulto, ruta_mini)
            QMessageBox.information(self, "Documentos", "Documentos generados correctamente.")
        except Exception as error:
            QMessageBox.critical(self, "Documentos", str(error))

    def consultar_envio(self) -> None:
        codigo = self.codigo_consulta.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Envío", "Escriba el código del envío que desea consultar.")
            return
        self.exportar_documentos(codigo)

    def actualizar_envios(self, codigo_seleccionado: str = "") -> None:
        envios = self.controller.listar_envios()
        self.envios_combo.clear()
        for envio in envios:
            texto = f"{envio['codigo_envio']} · {envio['destino']} · {envio['fecha']}"
            self.envios_combo.addItem(texto, envio["codigo_envio"])
        if codigo_seleccionado:
            indice = self.envios_combo.findData(codigo_seleccionado)
            if indice >= 0:
                self.envios_combo.setCurrentIndex(indice)

    def nota_entrega_seleccionada(self) -> None:
        codigo = self.envios_combo.currentData()
        if not codigo:
            QMessageBox.warning(self, "Nota de entrega", "Seleccione un envío de la lista.")
            return
        datos = self.controller.obtener_envio(str(codigo))
        if datos is None:
            QMessageBox.warning(self, "Nota de entrega", "No se encontró el envío seleccionado.")
            self.actualizar_envios()
            return
        bulto, _libros = datos
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Verificar datos de recepción")
        formulario = QFormLayout(dialogo)
        formulario.addRow("Sucursal", QLabel(bulto.get("destino") or "No registrada"))
        formulario.addRow("Dirección", QLabel(bulto.get("direccion") or "No registrada"))
        formulario.addRow("Municipio", QLabel(bulto.get("municipio") or "No registrado"))
        formulario.addRow("Volúmenes", QLabel(str(bulto.get("cantidad_volumenes", 0))))
        formulario.addRow("Fecha del envío", QLabel(bulto.get("fecha") or ""))
        nombre = QLineEdit(bulto.get("encargada") or "")
        cedula = QLineEdit()
        cedula.setPlaceholderText("Cédula exacta de quien recibe")
        formulario.addRow("Nombre de quien recibe *", nombre)
        formulario.addRow("Cédula de Identidad *", cedula)
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        formulario.addRow(botones)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        if not nombre.text().strip() or not cedula.text().strip():
            QMessageBox.warning(self, "Nota de entrega", "Complete el nombre y la cédula de quien recibe.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Nota de Entrega", f"{codigo}_nota_entrega.pdf", "PDF (*.pdf)",
        )
        if not ruta:
            return
        try:
            self.etiquetas.exportar_nota_entrega(
                bulto, {"nombre": nombre.text(), "cedula": cedula.text()}, ruta,
            )
            QMessageBox.information(self, "Nota de entrega", "La Nota de Entrega se generó correctamente.")
        except Exception as error:
            QMessageBox.critical(self, "Nota de entrega", str(error))