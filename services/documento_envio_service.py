from services.pdf_service import PDFService


class DocumentoEnvioService:
    def __init__(self, pdf: PDFService | None = None):
        self.pdf = pdf or PDFService()

    def generar(self, bulto: dict, libros: list[dict], destino: str):
        return self.pdf.generar_documento_envio(bulto, libros, destino)