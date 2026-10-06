from services.pdf_service import PDFService


class DocumentoEnvioService:
    def __init__(self, pdf: PDFService | None = None):
        self.pdf = pdf or PDFService()

    def generar(self, bulto: dict, libros: list[dict], destino: str):
        return self.pdf.generar_documento_envio(bulto, libros, destino)

    def generar_control_snbp(self, bulto: dict, libros: list[dict], destino: str):
        return self.pdf.generar_control_envio_snbp(bulto, libros, destino)

    def generar_nota_entrega(self, bulto: dict, datos_receptor: dict, destino: str):
        return self.pdf.generar_nota_entrega(bulto, datos_receptor, destino)

    def generar_matriz_sucursales(self, ficha: dict, destino: str):
        return self.pdf.generar_matriz_control_sucursales(ficha, destino)