from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFService:
    SENSITIVE_COLUMNS = {"password_hash", "salt"}

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.small = ParagraphStyle("CatalogSmall", parent=self.styles["BodyText"], fontName="Helvetica", fontSize=10, leading=12, alignment=TA_LEFT)

    @staticmethod
    def _document(destino: str | Path, content: list) -> Path:
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        SimpleDocTemplate(str(ruta), pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm).build(content)
        return ruta

    def generar_tabla(self, titulo: str, columnas: list[str], filas: list[list], destino: str | Path) -> Path:
        indices = [indice for indice, columna in enumerate(columnas) if columna.strip().casefold() not in self.SENSITIVE_COLUMNS]
        if not indices:
            raise ValueError("La tabla no contiene columnas exportables.")
        columnas_seguras = [columnas[indice] for indice in indices]
        filas_seguras = [[fila[indice] for indice in indices if indice < len(fila)] for fila in filas]
        contenido = [Paragraph(titulo, self.styles["Title"]), Spacer(1, 0.5 * cm), Table([columnas_seguras, *filas_seguras], repeatRows=1, style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F5C518")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F4F1")]),
        ]))]
        return self._document(destino, contenido)

    def generar_reporte(self, titulo: str, secciones: list[tuple[str, list[str], list[list]]], destino: str | Path) -> Path:
        contenido = [Paragraph(titulo, self.styles["Title"]), Spacer(1, 0.4 * cm)]
        for nombre, columnas, filas in secciones:
            contenido.append(Paragraph(nombre, self.styles["Heading2"]))
            if filas:
                indices = [
                    indice for indice, columna in enumerate(columnas)
                    if columna.strip().casefold() not in self.SENSITIVE_COLUMNS
                ]
                columnas_seguras = [columnas[indice] for indice in indices]
                filas_seguras = [
                    [fila[indice] for indice in indices if indice < len(fila)]
                    for fila in filas
                ]
                if columnas_seguras:
                    contenido.append(Table([columnas_seguras, *filas_seguras], repeatRows=1, style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F5C518")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ])))
                else:
                    contenido.append(Paragraph("No hay campos exportables.", self.styles["BodyText"]))
            else:
                contenido.append(Paragraph("Sin registros para el período seleccionado.", self.styles["BodyText"]))
            contenido.append(Spacer(1, 0.3 * cm))
        return self._document(destino, contenido)

    def generar_resumen_distribucion_bibliotecas(self, datos: dict, destino: str | Path) -> Path:
        estilos = getSampleStyleSheet()
        membrete = ParagraphStyle(
            "MatrizDistribucionMembrete", parent=estilos["BodyText"],
            fontName="Helvetica-Bold", fontSize=8, leading=10, alignment=TA_CENTER,
        )
        titulo = ParagraphStyle(
            "MatrizDistribucionTitulo", parent=estilos["Title"],
            fontName="Helvetica-Bold", fontSize=12, leading=14, alignment=TA_CENTER,
        )
        celda = ParagraphStyle(
            "MatrizDistribucionCelda", parent=estilos["BodyText"],
            fontName="Helvetica", fontSize=6.5, leading=8,
        )
        cabecera = ParagraphStyle(
            "MatrizDistribucionCabecera", parent=celda,
            fontName="Helvetica-Bold", fontSize=5.8, leading=7, alignment=TA_CENTER,
        )
        paginas_grupos = (
            ("Áreas 000–400 y grupos especiales", (
                "000", "100", "200", "300", "400", "Biografías",
                "Pub. Oficiales", "Pub. Periódicas", "Total", "Total General",
            )),
            ("Áreas 500–900 y material no bibliográfico", (
                "500", "600", "700", "800", "900", "No Bibliográfico",
                "Total", "Total General",
            )),
        )
        ancho_pagina, alto_pagina = landscape(letter)
        margen = 0.55 * cm
        ancho_nombre = 3.8 * cm
        contenido = [
            Table(
                [[Paragraph(
                    "<b>GOBERNACIÓN DEL ESTADO BOLÍVAR</b><br/>"
                    "SECRETARÍA DE CULTURA<br/>"
                    "DIRECCIÓN DE FORTALECIMIENTO DEL CONOCIMIENTO Y RAÍCES CULTURALES<br/>"
                    "COORDINACIÓN DE RED ESTATAL DE BIBLIOTECAS PÚBLICAS",
                    membrete,
                )]],
                colWidths=[ancho_pagina - 2 * margen],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#475569")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]),
            ),
            Spacer(1, 0.2 * cm),
            Paragraph(
                f"RESUMEN DE DISTRIBUCIÓN DE BIBLIOTECAS PÚBLICAS POR ÁREAS DE CONOCIMIENTO — {int(datos.get('anio') or date.today().year)}",
                titulo,
            ),
            Spacer(1, 0.15 * cm),
            Paragraph(
                "T = títulos (registros bibliográficos); V = volúmenes (número registrado, "
                "o 1 por título si no se indicó). Se considera la ubicación más reciente. "
                "Total suma las áreas Dewey 000–900; Total General añade registros con Dewey especial o sin clasificación.",
                celda,
            ),
            Spacer(1, 0.2 * cm),
        ]

        for pagina_indice, (subtitulo, grupos_pagina) in enumerate(paginas_grupos):
            if pagina_indice:
                contenido.append(PageBreak())
                contenido.extend([
                    Paragraph(
                        f"RESUMEN DE DISTRIBUCIÓN — {int(datos.get('anio') or date.today().year)}",
                        titulo,
                    ),
                    Spacer(1, 0.15 * cm),
                ])
            contenido.append(Paragraph(subtitulo, estilos["Heading3"]))
            columnas = [Paragraph("<b>Biblioteca / Municipio</b>", cabecera)]
            columnas.extend(Paragraph(f"<b>{grupo}</b>", cabecera) for grupo in grupos_pagina for _ in range(2))
            cabecera_metrica = [Paragraph("", cabecera)]
            cabecera_metrica.extend(Paragraph(f"<b>{metrica}</b>", cabecera) for _ in grupos_pagina for metrica in ("T", "V"))
            tabla_datos = [columnas, cabecera_metrica]
            for sucursal in datos.get("sucursales", []):
                nombre = str(sucursal.get("biblioteca") or "")
                municipio = str(sucursal.get("municipio") or "").strip()
                nombre_visible = f"{nombre} — {municipio}" if municipio else nombre
                fila = [Paragraph(escape(nombre_visible), celda)]
                categorias = sucursal.get("categorias", {})
                for grupo in grupos_pagina:
                    valores = categorias.get(grupo, {})
                    fila.extend((str(valores.get("T", 0)), str(valores.get("V", 0))))
                tabla_datos.append(fila)
            fila_total = [Paragraph("<b>TOTAL GENERAL DE LA RED</b>", cabecera)]
            totales = datos.get("totales_generales", {})
            for grupo in grupos_pagina:
                valores = totales.get(grupo, {})
                fila_total.extend((str(valores.get("T", 0)), str(valores.get("V", 0))))
            tabla_datos.append(fila_total)

            ancho_util = ancho_pagina - 2 * margen
            ancho_numero = (ancho_util - ancho_nombre) / (len(grupos_pagina) * 2)
            tabla = Table(
                tabla_datos,
                colWidths=[ancho_nombre, *([ancho_numero] * len(grupos_pagina) * 2)],
                repeatRows=2,
                hAlign="LEFT",
            )
            comandos = [
                ("BACKGROUND", (0, 0), (-1, 1), colors.HexColor("#263746")),
                ("TEXTCOLOR", (0, 0), (-1, 1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#64748B")),
                ("ROWBACKGROUNDS", (0, 2), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
            for grupo_indice in range(len(grupos_pagina)):
                columna = 1 + grupo_indice * 2
                comandos.append(("SPAN", (columna, 0), (columna + 1, 0)))
            tabla.setStyle(TableStyle(comandos))
            contenido.extend([tabla, Spacer(1, 0.2 * cm)])
            if pagina_indice == len(paginas_grupos) - 1:
                contenido.append(Paragraph(escape(str(datos.get("nota_clasificacion") or "")), celda))

        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        SimpleDocTemplate(
            str(ruta), pagesize=landscape(letter),
            rightMargin=margen, leftMargin=margen, topMargin=0.5 * cm, bottomMargin=1.0 * cm,
        ).build(contenido, onFirstPage=self._pie_resumen_distribucion, onLaterPages=self._pie_resumen_distribucion)
        return ruta

    @staticmethod
    def _pie_resumen_distribucion(pagina, documento) -> None:
        pagina.saveState()
        pagina.setFont("Helvetica", 7)
        pagina.setFillColor(colors.HexColor("#475569"))
        pagina.drawString(0.55 * cm, 0.45 * cm, "GOB-074FM-034/11 | Vigencia: 07/10/2011")
        pagina.drawRightString(landscape(letter)[0] - 0.55 * cm, 0.45 * cm, f"Página {documento.page}")
        pagina.restoreState()

    def generar_cotas(self, libros: list[dict], destino: str | Path, ancho_cm: float = 1.4, alto_cm: float = 4.0) -> Path:
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        pagina = canvas.Canvas(str(ruta), pagesize=A4)
        ancho_pagina, alto_pagina = A4
        if ancho_cm <= 0 or alto_cm <= 0:
            raise ValueError("El ancho y alto de la etiqueta deben ser mayores que cero.")
        ancho, alto, margen = ancho_cm * cm, alto_cm * cm, 1 * cm
        columnas = int((ancho_pagina - 2 * margen) // ancho)
        filas = int((alto_pagina - 2 * margen) // alto)
        if columnas < 1 or filas < 1:
            raise ValueError("Las dimensiones de etiqueta no caben en una hoja A4.")
        por_pagina = columnas * filas
        for inicio in range(0, max(len(libros), 1), por_pagina):
            for indice, libro in enumerate(libros[inicio:inicio + por_pagina]):
                columna, fila = indice % columnas, indice // columnas
                x = margen + columna * ancho
                y = alto_pagina - margen - (fila + 1) * alto
                pagina.rect(x, y, ancho, alto)
                lineas = str(libro.get("cota", "")).splitlines()
                pagina.setFont("Courier", 8)
                for linea, valor in enumerate(lineas):
                    pagina.drawCentredString(x + ancho / 2, y + alto - 0.65 * cm - linea * 0.42 * cm, valor[:12])
            pagina.showPage()
        pagina.save()
        return ruta

    def generar_fichas(self, libros: list[dict], destino: str | Path) -> Path:
        if not libros:
            raise ValueError("Seleccione al menos un libro para generar las fichas.")

        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        pagina = canvas.Canvas(str(ruta), pagesize=letter)
        ancho_pagina, alto_pagina = letter
        ancho_ficha, alto_ficha = ancho_pagina / 2, alto_pagina / 2

        for inicio in range(0, len(libros), 4):
            lote = libros[inicio:inicio + 4]
            for posicion in range(4):
                if posicion >= len(lote):
                    continue
                columna = posicion % 2
                fila = posicion // 2
                x = columna * ancho_ficha
                y = alto_pagina - (fila + 1) * alto_ficha
                self._dibujar_ficha_individual(pagina, lote[posicion], x, y, ancho_ficha, alto_ficha)

            pagina.saveState()
            pagina.setStrokeColor(colors.HexColor("#64748B"))
            pagina.setLineWidth(0.6)
            pagina.setDash(2, 3)
            pagina.line(ancho_ficha, 0.35 * cm, ancho_ficha, alto_pagina - 0.35 * cm)
            pagina.line(0.35 * cm, alto_ficha, ancho_pagina - 0.35 * cm, alto_ficha)
            pagina.restoreState()
            pagina.showPage()
        pagina.save()
        return ruta

    @staticmethod
    def _dibujar_ficha_individual(
        pagina: canvas.Canvas,
        libro: dict,
        x: float,
        y: float,
        ancho: float,
        alto: float,
    ) -> None:
        margen = 0.55 * cm
        izquierda = x + margen
        derecha = x + ancho - margen
        arriba = y + alto - margen
        ancho_contenido = derecha - izquierda
        estilos = getSampleStyleSheet()
        texto = ParagraphStyle(
            "FichaIndividualTexto", parent=estilos["BodyText"],
            fontName="Helvetica", fontSize=8, leading=10,
            spaceAfter=0, splitLongWords=True,
        )
        encabezado = ParagraphStyle(
            "FichaIndividualEncabezado", parent=texto,
            fontName="Helvetica-Bold", fontSize=7, leading=8,
        )
        valor_o_linea = lambda valor: escape(str(valor).strip()) if valor not in (None, "") else "................................................"

        pagina.saveState()
        pagina.setStrokeColor(colors.HexColor("#94A3B8"))
        pagina.setLineWidth(0.5)
        pagina.rect(x + 0.12 * cm, y + 0.12 * cm, ancho - 0.24 * cm, alto - 0.24 * cm)
        pagina.restoreState()

        cota = str(libro.get("cota") or "").replace("\n", " / ")
        cota_texto = Paragraph(f"<b>COTA:</b> {escape(cota or '................')}", encabezado)
        cota_ancho, cota_alto = cota_texto.wrap(ancho_contenido * 0.55, alto * 0.2)
        cota_texto.drawOn(pagina, derecha - cota_ancho, arriba - cota_alto)

        membrete = Paragraph(
            "<b>SECRETARÍA DE CULTURA</b><br/>"
            "COORDINACIÓN DE RED ESTATAL DE BIBLIOTECAS PÚBLICAS",
            encabezado,
        )
        membrete_ancho, membrete_alto = membrete.wrap(ancho_contenido * 0.68, alto * 0.2)
        membrete.drawOn(pagina, izquierda, arriba - membrete_alto)
        pagina.saveState()
        pagina.setStrokeColor(colors.HexColor("#CBD5E1"))
        pagina.setLineWidth(0.5)
        pagina.line(izquierda, arriba - 0.9 * cm, derecha, arriba - 0.9 * cm)
        pagina.restoreState()

        cursor_y = arriba - 1.12 * cm

        def dibujar_campo(etiqueta: str, valor: str, altura_minima: float = 0.53 * cm) -> None:
            nonlocal cursor_y
            parrafo = Paragraph(f"<b>{etiqueta}</b> {valor_o_linea(valor)}", texto)
            _ancho, altura = parrafo.wrap(ancho_contenido, max(cursor_y - (y + 0.9 * cm), 0.5 * cm))
            parrafo.drawOn(pagina, izquierda, cursor_y - altura)
            cursor_y -= max(altura, altura_minima)

        dibujar_campo("Autor:", libro.get("autor", ""))
        dibujar_campo("Título:", libro.get("titulo", ""))
        edicion_editorial_ciudad_fecha = (
            f"<b>Edición:</b> {valor_o_linea(libro.get('edicion'))}"
            f"&nbsp;&nbsp; <b>Editorial:</b> {valor_o_linea(libro.get('editorial'))}"
            f"<br/><b>Ciudad:</b> {valor_o_linea(libro.get('ciudad'))}"
            f"&nbsp;&nbsp; <b>Fecha:</b> {valor_o_linea(libro.get('anio'))}"
        )
        parrafo_publicacion = Paragraph(edicion_editorial_ciudad_fecha, texto)
        _ancho, altura_publicacion = parrafo_publicacion.wrap(ancho_contenido, max(cursor_y - (y + 0.9 * cm), 0.5 * cm))
        parrafo_publicacion.drawOn(pagina, izquierda, cursor_y - altura_publicacion)
        cursor_y -= max(altura_publicacion, 0.95 * cm)
        paginas_volumen = libro.get("paginas") or libro.get("numero_volumenes")
        sufijo = "vol." if libro.get("numero_volumenes") and not libro.get("paginas") else "pág."
        dibujar_campo("Pág. ó Vol.:", f"{paginas_volumen} {sufijo}" if paginas_volumen else "")
        dibujar_campo("Observaciones:", libro.get("observaciones", ""), altura_minima=0.8 * cm)
        if libro.get("numero_registro"):
            dibujar_campo("Registro:", libro.get("numero_registro"), altura_minima=0.45 * cm)

        pagina.saveState()
        pagina.setFont("Helvetica", 6)
        pagina.setFillColor(colors.HexColor("#475569"))
        pagina.drawString(izquierda, y + 0.32 * cm, "GOB-074-FM-031/11 | Vigencia: 07/10/2011")
        pagina.restoreState()

    def generar_documento_envio(self, bulto: dict, libros: list[dict], destino: str | Path) -> Path:
        filas = [[libro.get("titulo", ""), libro.get("autor", ""), libro.get("cota", ""), libro.get("numero_registro", "")] for libro in libros]
        tabla = Table([["Título", "Autor", "Cota", "Registro"], *filas], repeatRows=1, style=TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F5C518")), ("GRID", (0, 0), (-1, -1), 0.4, colors.black), ("FONTSIZE", (0, 0), (-1, -1), 8)]))
        contenido = []
        for copia in ("Archivo central", "Biblioteca receptora"):
            contenido.extend([
                Paragraph(f"Documento de envío bibliotecario | Copia para {copia}", self.styles["Title"]),
                Spacer(1, 0.4 * cm),
                Paragraph(f"Código: {bulto.get('codigo_envio', '')} | Destino: {bulto.get('destino', '')} | Fecha: {bulto.get('fecha', '')}", self.styles["BodyText"]),
                Spacer(1, 0.4 * cm), tabla,
                Spacer(1, 1.2 * cm),
                Paragraph("Firma de despacho: ____________________    Firma de recepción: ____________________", self.styles["BodyText"]),
            ])
            if copia == "Archivo central":
                contenido.append(PageBreak())
        return self._document(destino, contenido)

    @staticmethod
    def _formatear_fecha_envio(fecha) -> str:
        if isinstance(fecha, (date, datetime)):
            return fecha.strftime("%d/%m/%Y")
        valor = str(fecha or "").strip()
        try:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        except ValueError:
            return valor.split(" ", 1)[0]

    @staticmethod
    def _formatear_monto(monto: Decimal) -> str:
        entero, decimales = f"{monto:,.2f}".split(".")
        return f"Bs. {entero.replace(',', '.')},{decimales}"

    def generar_control_envio_snbp(self, bulto: dict, libros: list[dict], destino: str | Path) -> Path:
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle(
            "ControlEnvioTitulo", parent=estilos["Title"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, alignment=TA_CENTER, spaceAfter=8,
        )
        celda = ParagraphStyle(
            "ControlEnvioCelda", parent=estilos["BodyText"], fontName="Helvetica",
            fontSize=6.5, leading=8, alignment=TA_LEFT, wordWrap="CJK",
        )
        encabezado = ParagraphStyle(
            "ControlEnvioEncabezado", parent=celda, fontName="Helvetica-Bold",
            fontSize=6.5, leading=8, alignment=TA_CENTER, textColor=colors.white,
        )
        contenido = [
            Table(
                [[
                    Paragraph("<b>GOBERNACIÓN DEL ESTADO BOLÍVAR</b>", celda),
                    Paragraph("<b>INSTITUTO AUTÓNOMO<br/>BIBLIOTECA NACIONAL</b>", celda),
                ]],
                colWidths=[8.6 * cm, 8.6 * cm],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]),
            ),
            Spacer(1, 0.25 * cm),
            Paragraph("CONTROL DE ENVÍO AL SISTEMA NACIONAL DE BIBLIOTECAS PÚBLICAS", titulo),
            Table(
                [[
                    Paragraph("<b>ENTIDAD FEDERAL:</b> BOLÍVAR", celda),
                    Paragraph(f"<b>MEMO Nº:</b> {escape(str(bulto.get('codigo_envio') or ''))}", celda),
                    Paragraph(f"<b>FECHA:</b> {escape(self._formatear_fecha_envio(bulto.get('fecha')))}", celda),
                ]],
                colWidths=[6.3 * cm, 5.5 * cm, 5.4 * cm],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#475569")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]),
            ),
            Spacer(1, 0.25 * cm),
        ]
        encabezados = [
            "Registro<br/>del Koha", "Organismo / Autor", "Títulos", "Cota",
            "N° de<br/>Volúmenes", "Precio Unitario<br/>(Bs.)", "Total<br/>(Bs.)",
            "Vía de ingreso",
        ]
        filas = [[Paragraph(texto, encabezado) for texto in encabezados]]
        total_general = Decimal("0.00")
        registros_incompletos = 0
        for libro in libros:
            volumenes = libro.get("numero_volumenes")
            precio = libro.get("precio_unitario")
            if volumenes not in (None, ""):
                volumenes = int(volumenes)
            else:
                volumenes = None
            if precio not in (None, ""):
                precio = Decimal(str(precio))
            else:
                precio = None
            total = precio * volumenes if precio is not None and volumenes is not None else None
            if total is None:
                registros_incompletos += 1
            else:
                total_general += total
            organismo_autor = " / ".join(
                str(valor).strip() for valor in (libro.get("organismo"), libro.get("autor")) if valor
            ) or "No registrado"
            via = "COMPRA" if libro.get("procedencia") == "compra" else "INGRESOS ORDINARIOS"
            celdas = (
                libro.get("numero_registro") or "No registrado",
                organismo_autor,
                libro.get("titulo") or "No registrado",
                libro.get("cota") or "No registrada",
                str(volumenes) if volumenes is not None else "No registrado",
                self._formatear_monto(precio) if precio is not None else "No registrado",
                self._formatear_monto(total) if total is not None else "No calculable",
                f"X  {via}",
            )
            filas.append([Paragraph(escape(str(valor)).replace("\n", "<br/>"), celda) for valor in celdas])
        anchos = [1.6 * cm, 2.8 * cm, 3.4 * cm, 2.0 * cm, 1.5 * cm, 2.5 * cm, 2.3 * cm, 3.5 * cm]
        tabla = Table(filas, colWidths=anchos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263746")),
            ("GRID", (0, 0), (-1, -1), 0.55, colors.HexColor("#64748B")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (4, 0), (6, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        contenido.extend([tabla, Spacer(1, 0.25 * cm)])
        subtotal_texto = self._formatear_monto(total_general)
        if registros_incompletos:
            total_texto = f"Subtotal calculable: {subtotal_texto}. Total general incompleto: faltan datos en {registros_incompletos} registro(s)."
        else:
            total_texto = f"TOTAL GENERAL: {subtotal_texto}"
        contenido.extend([
            Paragraph(f"<b>{escape(total_texto)}</b>", estilos["BodyText"]),
            Paragraph(f"Cantidad de títulos: {len(libros)}", estilos["BodyText"]),
            Spacer(1, 0.6 * cm),
            Paragraph(
                "Responsable del envío: ____________________________"
                "&nbsp;&nbsp;&nbsp; Firma y sello: ____________________________",
                estilos["BodyText"],
            ),
            Spacer(1, 0.4 * cm),
            Paragraph(
                "Recibido por: _____________________________________"
                "&nbsp;&nbsp;&nbsp; Fecha y firma: ____________________________",
                estilos["BodyText"],
            ),
        ])
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        documento = SimpleDocTemplate(
            str(ruta), pagesize=letter, rightMargin=0.75 * cm, leftMargin=0.75 * cm,
            topMargin=0.8 * cm, bottomMargin=1.2 * cm,
        )
        documento.build(
            contenido,
            onFirstPage=self._pie_control_envio,
            onLaterPages=self._pie_control_envio,
        )
        return ruta

    @staticmethod
    def _pie_control_envio(pagina, documento) -> None:
        pagina.saveState()
        pagina.setFont("Helvetica", 8)
        pagina.setFillColor(colors.HexColor("#64748B"))
        pagina.drawRightString(letter[0] - 0.75 * cm, 0.55 * cm, f"Página {documento.page}")
        pagina.restoreState()

    def generar_matriz_control_sucursales(self, ficha: dict, destino: str | Path) -> Path:
        estilos = getSampleStyleSheet()
        encabezado = ParagraphStyle(
            "MatrizInstitucional", parent=estilos["BodyText"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, alignment=TA_CENTER,
        )
        titulo = ParagraphStyle(
            "MatrizTitulo", parent=estilos["Title"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, alignment=TA_CENTER, spaceBefore=8, spaceAfter=8,
        )
        detalle = ParagraphStyle(
            "MatrizDetalle", parent=estilos["BodyText"], fontName="Helvetica",
            fontSize=8, leading=10,
        )
        nombre_biblioteca = ParagraphStyle(
            "MatrizBiblioteca", parent=detalle, fontSize=7.5, leading=9,
        )
        subtitulo_tabla = ParagraphStyle(
            "MatrizBloque", parent=detalle, fontName="Helvetica-Bold",
            fontSize=8, leading=10, textColor=colors.HexColor("#1F2937"),
        )
        contenido = [
            Table(
                [[
                    Paragraph("<b>SECRETARÍA DE CULTURA</b>", encabezado),
                    Paragraph("<b>COORDINACIÓN DE RED ESTATAL<br/>DE BIBLIOTECAS PÚBLICAS</b>", encabezado),
                ]],
                colWidths=[9.7 * cm, 9.7 * cm],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#475569")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]),
            ),
            Paragraph("FICHA CATALOGRÁFICA INSTITUCIONAL", titulo),
            Paragraph(f"<b>Año:</b> {date.today().year}", detalle),
            Spacer(1, 0.2 * cm),
            Paragraph(
                f"<b>Título:</b> {escape(str(ficha.get('titulo') or ''))}"
                f"&nbsp;&nbsp; <b>Autor:</b> {escape(str(ficha.get('autor') or ''))}<br/>"
                f"<b>Registro:</b> {escape(str(ficha.get('numero_registro') or ''))}"
                f"&nbsp;&nbsp; <b>Cota:</b> {escape(str(ficha.get('cota') or ''))}"
                f"&nbsp;&nbsp; <b>Estado:</b> {escape(str(ficha.get('estado') or ''))}",
                detalle,
            ),
            Spacer(1, 0.25 * cm),
            Paragraph(
                "Marque con X el estado del ejemplar en cada biblioteca: "
                "<b>I</b> Ingreso, <b>D</b> Disponibilidad, <b>P</b> Préstamo.",
                detalle,
            ),
            Spacer(1, 0.15 * cm),
        ]

        filas = ficha.get("filas", [])
        bloques = [filas[:13], filas[13:26]]
        if len(filas) > 26:
            bloques.append(filas[26:])
        if not bloques or not any(bloques):
            bloques = [[]]
        for indice, bloque in enumerate(bloques, start=1):
            contenido.append(Paragraph(f"Bloque {indice}", subtitulo_tabla))
            datos_tabla = [[
                Paragraph("<b>Biblioteca de la red</b>", nombre_biblioteca),
                Paragraph("<b>I</b>", encabezado),
                Paragraph("<b>D</b>", encabezado),
                Paragraph("<b>P</b>", encabezado),
            ]]
            for fila in bloque:
                datos_tabla.append([
                    Paragraph(escape(str(fila.get("biblioteca") or "")), nombre_biblioteca),
                    "X" if fila.get("ingreso") else "",
                    "X" if fila.get("disponibilidad") else "",
                    "X" if fila.get("prestamo") else "",
                ])
            tabla = Table(
                datos_tabla,
                colWidths=[14.0 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm],
                repeatRows=1,
            )
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263746")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#64748B")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            contenido.extend([tabla, Spacer(1, 0.15 * cm)])

        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        documento = SimpleDocTemplate(
            str(ruta), pagesize=letter, rightMargin=1.0 * cm, leftMargin=1.0 * cm,
            topMargin=0.9 * cm, bottomMargin=1.2 * cm,
        )
        documento.build(contenido, onFirstPage=self._pie_matriz_sucursales, onLaterPages=self._pie_matriz_sucursales)
        return ruta

    @staticmethod
    def _pie_matriz_sucursales(pagina, documento) -> None:
        pagina.saveState()
        pagina.setFont("Helvetica", 7)
        pagina.setFillColor(colors.HexColor("#475569"))
        pagina.drawRightString(
            letter[0] - 1.0 * cm,
            0.55 * cm,
            "GOB-074-FM-031/11 | Vigencia: 07/10/2011",
        )
        pagina.restoreState()

    @staticmethod
    def _numero_en_letras(numero: int) -> str:
        unidades = (
            "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
            "ocho", "nueve", "diez", "once", "doce", "trece", "catorce",
            "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
            "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
            "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve",
        )
        decenas = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa"}
        centenas = {
            100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
            500: "quinientos", 600: "seiscientos", 700: "setecientos",
            800: "ochocientos", 900: "novecientos",
        }

        def menor_mil(valor: int) -> str:
            if valor < len(unidades):
                return unidades[valor]
            if valor < 100:
                decena = valor // 10 * 10
                return f"{decenas[decena]} y {unidades[valor % 10]}" if valor % 10 else decenas[decena]
            if valor == 100:
                return "cien"
            centena = valor // 100 * 100
            resto = valor % 100
            return f"{centenas[centena]} {menor_mil(resto)}".strip() if resto else centenas[centena]

        if numero < 0 or numero > 999_999:
            raise ValueError("La cantidad de volúmenes debe estar entre 0 y 999999.")
        if numero < 1000:
            return menor_mil(numero)
        miles, resto = divmod(numero, 1000)
        texto_miles = "mil" if miles == 1 else f"{menor_mil(miles)} mil"
        return f"{texto_miles} {menor_mil(resto)}".strip() if resto else texto_miles

    @staticmethod
    def _fecha_nota_entrega(fecha) -> date:
        if isinstance(fecha, datetime):
            return fecha.date()
        if isinstance(fecha, date):
            return fecha
        valor = str(fecha or "").strip()
        try:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
        except ValueError as error:
            raise ValueError("La fecha del envío no tiene un formato válido.") from error

    def generar_nota_entrega(self, bulto: dict, datos_receptor: dict, destino: str | Path) -> Path:
        fecha = self._fecha_nota_entrega(bulto.get("fecha"))
        cantidad = int(bulto.get("cantidad_volumenes", 0))
        if cantidad < 0:
            raise ValueError("La cantidad de volúmenes no puede ser negativa.")
        nombre_receptor = str(datos_receptor.get("nombre", "")).strip()
        cedula_receptor = str(datos_receptor.get("cedula", "")).strip()
        if not nombre_receptor or not cedula_receptor:
            raise ValueError("El nombre y la cédula de quien recibe son obligatorios.")

        estilos = getSampleStyleSheet()
        cuerpo = ParagraphStyle(
            "NotaEntregaCuerpo", parent=estilos["BodyText"], fontName="Helvetica",
            fontSize=11, leading=17, alignment=TA_LEFT, spaceAfter=12,
        )
        subtitulo = ParagraphStyle(
            "NotaEntregaSubtitulo", parent=estilos["BodyText"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, alignment=TA_CENTER,
        )
        encabezado = ParagraphStyle(
            "NotaEntregaTitulo", parent=estilos["Title"], fontName="Helvetica-Bold",
            fontSize=16, leading=20, alignment=TA_CENTER, spaceBefore=15, spaceAfter=20,
        )
        celda = ParagraphStyle(
            "NotaEntregaCelda", parent=estilos["BodyText"], fontName="Helvetica",
            fontSize=10, leading=14, alignment=TA_LEFT,
        )
        escapado = lambda valor: escape(str(valor or "").strip())
        biblioteca = escapado(bulto.get("destino"))
        direccion = escapado(bulto.get("direccion")) or "No registrada"
        municipio = escapado(bulto.get("municipio")) or "No registrado"
        nombre_receptor = escapado(nombre_receptor)
        cedula_receptor = escapado(cedula_receptor)
        responsable = escapado(datos_receptor.get("responsable_entrega")) or "________________________"
        cedula_responsable = escapado(datos_receptor.get("cedula_entrega")) or "________________"
        cargo_responsable = escapado(datos_receptor.get("cargo_entrega")) or "________________________"
        cargo_receptor = escapado(datos_receptor.get("cargo_receptor")) or "Encargada de biblioteca"
        meses = (
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        )
        fecha_texto = f"Ciudad Bolívar, {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}."
        cantidad_letras = self._numero_en_letras(cantidad)
        titulo_biblioteca = biblioteca if biblioteca.lower().startswith("biblioteca") else f"Biblioteca Pública {biblioteca}"
        texto = (
            "La Coordinación de Red de Bibliotecas Públicas hace constar por medio de la "
            f"presente la entrega a la ciudadana: <b>{nombre_receptor}</b>, encargada de la "
            f"<b>{titulo_biblioteca}</b>, ubicada en <b>{direccion}</b>, Municipio: "
            f"<b>{municipio}</b>, la cantidad de: <b>{cantidad} ({cantidad_letras}) volúmenes</b>."
        )
        contenido = [
            Table(
                [[
                    Paragraph("<b>GOBERNACIÓN DEL ESTADO BOLÍVAR</b>", subtitulo),
                    Paragraph("<b>SECRETARÍA CULTURAL<br/>COORDINACIÓN DE RED DE BIBLIOTECAS PÚBLICAS</b>", subtitulo),
                    Paragraph("<b>INSTITUTO AUTÓNOMO<br/>BIBLIOTECA NACIONAL</b>", subtitulo),
                ]],
                colWidths=[5.9 * cm, 7.8 * cm, 5.9 * cm],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#64748B")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]),
            ),
            Paragraph("NOTA DE ENTREGA", encabezado),
            Paragraph(texto, cuerpo),
            Table(
                [
                    [
                        Paragraph("<b>RESUMEN DEL ENVÍO</b>", celda),
                        Paragraph("<b>CANTIDAD EN LETRAS</b>", celda),
                        Paragraph("<b>CANTIDAD EN NÚMEROS</b>", celda),
                    ],
                    [
                        Paragraph(f"Código: {escapado(bulto.get('codigo_envio'))}<br/>Sucursal: {biblioteca}<br/>Títulos: {int(bulto.get('cantidad_libros', 0))}", celda),
                        Paragraph(f"{cantidad_letras.capitalize()} volúmenes", celda),
                        Paragraph(f"{cantidad:,}".replace(",", ".") + " volúmenes", celda),
                    ],
                ],
                colWidths=[7.2 * cm, 6.2 * cm, 6.2 * cm],
                rowHeights=[0.9 * cm, 2.4 * cm],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#475569")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#64748B")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ]),
            ),
            Spacer(1, 1.0 * cm),
            Paragraph(fecha_texto, ParagraphStyle("NotaEntregaFecha", parent=cuerpo, alignment=TA_RIGHT)),
            Spacer(1, 1.8 * cm),
            Table(
                [[
                    Paragraph(
                        f"<b>Entrega conforme</b><br/><br/><br/>"
                        f"Nombre: {responsable}<br/><br/>"
                        f"Cédula de Identidad (C.I.): {cedula_responsable}<br/><br/>"
                        f"Cargo: {cargo_responsable}",
                        celda,
                    ),
                    Paragraph(
                        f"<b>Recibe conforme</b><br/><br/><br/>"
                        f"Nombre: {nombre_receptor}<br/><br/>"
                        f"Cédula de Identidad (C.I.): {cedula_receptor}<br/><br/>"
                        f"Cargo: {cargo_receptor}",
                        celda,
                    ),
                ]],
                colWidths=[9.8 * cm, 9.8 * cm],
                style=TableStyle([
                    ("LINEABOVE", (0, 0), (0, 0), 0.8, colors.HexColor("#475569")),
                    ("LINEABOVE", (1, 0), (1, 0), 0.8, colors.HexColor("#475569")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]),
            ),
        ]
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        documento = SimpleDocTemplate(
            str(ruta), pagesize=letter, rightMargin=0.8 * cm, leftMargin=0.8 * cm,
            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        )
        documento.build(contenido)
        return ruta

    def generar_mini_ficha(self, bulto: dict, destino: str | Path) -> Path:
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        pagina = canvas.Canvas(str(ruta), pagesize=(8 * cm, 5 * cm))
        pagina.rect(0.25 * cm, 0.25 * cm, 7.5 * cm, 4.5 * cm)
        pagina.setFont("Helvetica-Bold", 10)
        pagina.drawString(0.5 * cm, 4.1 * cm, "BIBLIOTECA CENTRAL")
        pagina.setFont("Helvetica", 8)
        pagina.drawString(0.5 * cm, 3.4 * cm, f"Envío: {bulto.get('codigo_envio', '')}")
        pagina.drawString(0.5 * cm, 2.8 * cm, f"Destino: {bulto.get('destino', '')[:42]}")
        pagina.drawString(0.5 * cm, 2.2 * cm, f"Libros: {bulto.get('cantidad_libros', 0)}")
        pagina.drawString(0.5 * cm, 1.6 * cm, f"Fecha: {bulto.get('fecha', '')}")
        pagina.save()
        return ruta