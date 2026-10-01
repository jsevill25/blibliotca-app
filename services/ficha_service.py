from services.pdf_service import PDFService


class FichaService:
    def __init__(self, pdf: PDFService | None = None):
        self.pdf = pdf or PDFService()

    def generar_fichas(self, libros: list[dict], destino: str):
        return self.pdf.generar_fichas(libros, destino)