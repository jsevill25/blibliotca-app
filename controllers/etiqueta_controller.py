from pathlib import Path

from database.db_manager import DatabaseManager
from services.audit_service import AuditService
from services.documento_envio_service import DocumentoEnvioService
from services.etiqueta_service import EtiquetaService
from services.ficha_service import FichaService
from services.mini_ficha_service import MiniFichaService


class EtiquetaController:
    def __init__(self, database: DatabaseManager | None = None, usuario_id: int | None = None):
        self.audit = AuditService(database) if database is not None else None
        self.usuario_id = usuario_id
        self.etiquetas = EtiquetaService()
        self.fichas = FichaService()
        self.documentos = DocumentoEnvioService()
        self.mini_fichas = MiniFichaService()

    def exportar_cotas(self, libros: list[dict], destino: str, ancho_cm: float = 1.4, alto_cm: float = 4.0) -> None:
        self.etiquetas.generar_cotas(libros, destino, ancho_cm, alto_cm)
        self._auditar(destino, "PDF de cotas")

    def exportar_fichas(self, libros: list[dict], destino: str) -> None:
        self.fichas.generar_fichas(libros, destino)
        self._auditar(destino, "PDF de fichas catalográficas")

    def exportar_envio(self, bulto: dict, libros: list[dict], destino: str) -> None:
        self.documentos.generar(bulto, libros, destino)
        self._auditar(destino, "PDF de envío")

    def exportar_control_envio(self, bulto: dict, libros: list[dict], destino: str) -> None:
        self.documentos.generar_control_snbp(bulto, libros, destino)
        self._auditar(destino, "PDF de control de envío")

    def exportar_nota_entrega(self, bulto: dict, datos_receptor: dict, destino: str) -> None:
        self.documentos.generar_nota_entrega(bulto, datos_receptor, destino)
        self._auditar(destino, "PDF de nota de entrega")

    def exportar_matriz_sucursales(self, ficha: dict, destino: str) -> None:
        self.documentos.generar_matriz_sucursales(ficha, destino)
        self._auditar(destino, "PDF de matriz por sucursales")

    def exportar_mini_ficha(self, bulto: dict, destino: str) -> None:
        self.mini_fichas.generar(bulto, destino)
        self._auditar(destino, "PDF de mini-ficha")

    def _auditar(self, destino: str, tipo: str) -> None:
        if self.audit is not None:
            self.audit.registrar(
                "EXPORTACION_DATOS", self.usuario_id, "escritorio",
                f"Generó {tipo}: '{Path(destino).name}'.",
            )