from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QToolBox, QVBoxLayout, QWidget


class ManualView(QWidget):
    def __init__(self):
        super().__init__()
        principal = QVBoxLayout(self)
        principal.setContentsMargins(18, 16, 18, 16)
        principal.setSpacing(12)

        titulo = QLabel("Manual de usuario")
        titulo.setObjectName("pageTitle")
        principal.addWidget(titulo)
        introduccion = QLabel(
            "Guía rápida para registrar, procesar y distribuir libros. "
            "Esta pantalla se abre al iniciar sesión; también puede volver desde Ayuda o desde esta pestaña."
        )
        introduccion.setWordWrap(True)
        principal.addWidget(introduccion)

        flujo = QFrame()
        flujo.setObjectName("manualFlow")
        flujo.setStyleSheet("QFrame#manualFlow { background: white; border: 1px solid #D4D4D0; }")
        flujo_layout = QHBoxLayout(flujo)
        flujo_layout.setContentsMargins(12, 12, 12, 12)
        flujo_layout.setSpacing(8)
        etapas = (
            ("1", "Recepción", "Registrar ingreso y procedencia."),
            ("2", "Catalogación", "Asignar clasificación y cota."),
            ("3", "Etiquetas", "Imprimir cotas y fichas."),
            ("4", "Distribución", "Preparar envío a una sucursal."),
            ("5", "Seguimiento", "Consultar ubicación e historial."),
        )
        for indice, (numero, nombre, descripcion) in enumerate(etapas):
            tarjeta = QFrame()
            tarjeta.setMinimumWidth(145)
            tarjeta.setStyleSheet("QFrame { background: #F4F4F1; border: 1px solid #1A1A1A; }")
            tarjeta_layout = QVBoxLayout(tarjeta)
            tarjeta_layout.setContentsMargins(10, 8, 10, 8)
            numero_label = QLabel(numero)
            numero_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            numero_label.setStyleSheet("background: #F5C518; color: #1A1A1A; font-size: 15pt; font-weight: bold; border: 0;")
            nombre_label = QLabel(nombre)
            nombre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nombre_label.setStyleSheet("font-weight: bold; border: 0;")
            descripcion_label = QLabel(descripcion)
            descripcion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            descripcion_label.setWordWrap(True)
            descripcion_label.setStyleSheet("color: #6B6B6B; border: 0;")
            tarjeta_layout.addWidget(numero_label)
            tarjeta_layout.addWidget(nombre_label)
            tarjeta_layout.addWidget(descripcion_label, 1)
            flujo_layout.addWidget(tarjeta, 1)
            if indice < len(etapas) - 1:
                flecha = QLabel("→")
                flecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
                flecha.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1A1A1A;")
                flujo_layout.addWidget(flecha)
        principal.addWidget(flujo)

        ayuda = QLabel("Seleccione un tema para ver los pasos. Los módulos disponibles dependen de su rol.")
        ayuda.setObjectName("muted")
        principal.addWidget(ayuda)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        self.temas = QToolBox()
        self.temas.setStyleSheet("""
            QToolBox::tab { background: #1A1A1A; color: #F5C518; padding: 9px; border: 1px solid #1A1A1A; }
            QToolBox::tab:selected { background: #F5C518; color: #1A1A1A; font-weight: bold; }
            QToolBox QWidget { background: white; }
        """)
        self._agregar_tema("Primer acceso", [
            "1. Inicie sesión con la cuenta asignada. En la primera ejecución, la cuenta inicial es admin / admin123.",
            "2. Cambie la contraseña inicial conocida cuando el sistema lo solicite. Use una contraseña de al menos 10 caracteres y no comparta la clave inicial.",
            "3. La pestaña Manual de uso abre primero. Para volver en cualquier momento, selecciónela o use Ayuda > Abrir manual.",
            "4. El administrador ve además Usuarios y Sucursales. El bibliotecario trabaja con los módulos operativos.",
        ])
        self._agregar_tema("Recepción", [
            "1. Abra Recepción y complete el título; es obligatorio. ISBN, autor, editorial, edición, año, páginas e idioma complementan el registro. Precio unitario (Bs.) y número de volúmenes son opcionales.",
            "2. Seleccione Donación, Compra o Biblioteca Nacional. Aparecerán los campos correspondientes al origen.",
            "3. Pulse Registrar / guardar cambios. Se asigna un número REG-AAAA-NNNNN y el libro queda en estado recibido.",
            "4. Busque por título, autor o ISBN; use los filtros de procedencia y fechas para acotar la lista.",
            "5. Seleccione un libro recibido para corregirlo y guarde los cambios. La corrección queda asociada al usuario y fecha.",
        ])
        self._agregar_tema("Catalogación", [
            "1. Busque y seleccione un libro recibido en la lista de pendientes.",
            "2. Elija Dewey o LC, escriba el código real de clasificación y revise el Cutter sugerido.",
            "3. La cota se forma con clasificación, Cutter y año. Puede corregir el texto antes de catalogar.",
            "4. Si la cota ya existe, confirme sólo cuando sea un volumen que deba compartirla. Al guardar, el estado pasa a catalogado.",
        ])
        self._agregar_tema("Etiquetas y fichas", [
            "1. Actualice la lista de libros catalogados. Seleccione filas concretas o deje la selección vacía para exportar todos.",
            "2. Ajuste ancho y alto de la etiqueta de lomo en centímetros si su papel lo requiere.",
            "3. Exporte cotas PDF o fichas catalográficas individuales. Las fichas se imprimen cuatro por hoja Carta con guías punteadas de corte; los espacios sobrantes quedan vacíos.",
            "4. Imprima al 100 % de escala; desactive opciones del controlador como Ajustar a página para conservar las medidas.",
        ])
        self._agregar_tema("Distribución", [
            "1. Elija una sucursal activa y, si corresponde, indique género/tipo y observaciones.",
            "2. Busque y seleccione uno o más libros catalogados. Los libros recibidos no se pueden enviar sin catalogar.",
            "3. Pulse Crear envío. Se genera un código ENV-AAAAMMDD-NNN y se registra la ubicación/movimiento.",
            "4. Confirme para generar el Control de Envío al Sistema Nacional de Bibliotecas Públicas, con totales cuando precio y volúmenes estén registrados; también puede guardar la mini-ficha de caja.",
            "5. Seleccione un envío de la lista y pulse Nota de entrega. Verifique los datos de sucursal y complete el nombre y la cédula exacta de quien recibe antes de guardar el PDF.",
            "6. Registre el municipio de la sucursal en Bibliotecas para que aparezca automáticamente en la Nota de Entrega.",
        ])
        self._agregar_tema("Fichero e inventario", [
            "Busque libros catalogados y seleccione un solo libro para generar la Matriz de Control por Sucursales.",
            "La matriz indica I (Ingreso), D (Disponibilidad) y P (Préstamo) según la ubicación más reciente y el estado del libro registrados en el sistema.",
            "En Etiquetas y Fichas, las fichas catalográficas individuales se organizan cuatro por página Carta; revise escala, márgenes y guías al imprimir.",
        ])
        self._agregar_tema("Reportes", [
            "Use Resumen de distribución por áreas de conocimiento para generar la matriz anual por biblioteca y municipio, con títulos y volúmenes por rangos Dewey.",
            "La matriz toma la ubicación más reciente de cada libro; biografías y publicaciones periódicas se aproximan por rangos Dewey. No se asignan publicaciones oficiales ni materiales no bibliográficos si no están clasificados en los datos.",
        ])
        self._agregar_tema("Ubicación e historial", [
            "1. Busque por título, autor, ISBN, cota o número de registro; combine estado, biblioteca, tipo, sala y estante.",
            "2. La tabla presenta el estado, la ubicación actual y el último movimiento.",
            "3. Para registrar una ubicación física, seleccione el libro, elija biblioteca/tipo e indique sala y estante; pulse Actualizar ubicación.",
            "4. Use Historial de movimientos para revisar la trazabilidad completa del libro.",
        ])
        self._agregar_tema("Reportes y respaldos", [
            "1. Defina las fechas Desde/Hasta y actualice el resumen para consultar recepción, catalogación y distribución del período.",
            "2. Exporte el reporte periódico a PDF o Excel. El Excel incluye hojas por inventario, recepción, catalogación, distribución y ubicación.",
            "3. Exportar todas las tablas está reservado al administrador y omite hashes y sales de usuarios. Los textos que podrían convertirse en fórmulas se exportan como texto.",
            "4. Crear backup ahora copia la base SQLite y comprueba su integridad. Al cerrar la aplicación también se intenta crear un respaldo; se conservan los siete más recientes.",
            "5. Los eventos de acceso, cambios de contraseña, administración, exportaciones y respaldos quedan registrados en la bitácora. No contiene contraseñas ni tokens y no reemplaza un procedimiento institucional de auditoría.",
            "6. Los respaldos no están cifrados ni sustituyen copias externas. Verifique la copia y coordine su custodia antes de usar datos reales.",
        ])
        self._agregar_tema("Usuarios y sucursales (admin)", [
            "1. En Usuarios, cree cuentas con rol bibliotecario o admin. Para editar, seleccione una fila, corrija los datos y pulse Guardar cambios.",
            "2. La contraseña puede dejarse vacía para conservarla; si se cambia, debe tener al menos 10 caracteres.",
            "3. Use Activar / desactivar para conservar el historial sin borrar cuentas. No se puede desactivar el admin inicial ni dejar el sistema sin administrador activo.",
            "4. En Sucursales puede registrar o desactivar bibliotecas. La Biblioteca Central no se puede desactivar.",
        ])
        contenido_layout.addWidget(self.temas)
        scroll.setWidget(contenido)
        principal.addWidget(scroll, 1)

    def _agregar_tema(self, titulo: str, instrucciones: list[str]) -> None:
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        for instruccion in instrucciones:
            texto = QLabel(instruccion)
            texto.setWordWrap(True)
            texto.setTextFormat(Qt.TextFormat.PlainText)
            texto.setStyleSheet("padding: 4px 0; border: 0;")
            layout.addWidget(texto)
        layout.addStretch(1)
        self.temas.addItem(pagina, titulo)