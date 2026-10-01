from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFService:
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
        contenido = [Paragraph(titulo, self.styles["Title"]), Spacer(1, 0.5 * cm), Table([columnas, *filas], repeatRows=1, style=TableStyle([
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
                contenido.append(Table([columnas, *filas], repeatRows=1, style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#F5C518")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])))
            else:
                contenido.append(Paragraph("Sin registros para el período seleccionado.", self.styles["BodyText"]))
            contenido.append(Spacer(1, 0.3 * cm))
        return self._document(destino, contenido)

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
        from xml.sax.saxutils import escape

        filas = []
        for libro in libros:
            texto = "<br/>".join([
                f"<b>{escape(str(libro.get('autor', '')))}</b>", escape(str(libro.get("titulo", ""))),
                escape(f"{libro.get('edicion', '')}. {libro.get('editorial', '')}, {libro.get('anio', '')}"),
                escape(f"{libro.get('paginas', '')} p. ISBN {libro.get('isbn', '')}"),
                escape(f"Cota: {libro.get('cota', '')} | Registro: {libro.get('numero_registro', '')}"),
            ])
            filas.append(Paragraph(texto, self.small))
        while len(filas) % 4:
            filas.append(Paragraph("", self.small))
        tabla = Table([filas[i:i + 2] for i in range(0, len(filas), 2)], colWidths=[7.5 * cm, 7.5 * cm], rowHeights=[12.5 * cm] * (len(filas) // 2), hAlign="CENTER")
        tabla.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0.5 * cm), ("TOPPADDING", (0, 0), (-1, -1), 0.5 * cm)]))
        return self._document(destino, [tabla])

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