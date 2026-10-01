from services.pdf_service import PDFService


class MiniFichaService:
    def __init__(self, pdf: PDFService | None = None):
        self.pdf = pdf or PDFService()

    def generar(self, bulto: dict, destino: str):
        return self.pdf.generar_mini_ficha(bulto, destino)