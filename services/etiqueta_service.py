from services.pdf_service import PDFService


class EtiquetaService:
    def __init__(self, pdf: PDFService | None = None):
        self.pdf = pdf or PDFService()

    def generar_cotas(self, libros: list[dict], destino: str, ancho_cm: float = 1.4, alto_cm: float = 4.0):
        return self.pdf.generar_cotas(libros, destino, ancho_cm, alto_cm)