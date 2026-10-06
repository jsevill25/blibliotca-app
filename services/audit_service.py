from datetime import datetime

from database.db_manager import DatabaseManager
from database.models import AuditoriaLog


class AuditService:
    ACCIONES = {
        "LOGIN_EXITOSO",
        "LOGIN_FALLIDO",
        "CAMBIO_CLAVE",
        "EXPORTACION_DATOS",
        "RESPALDO_DB",
        "ACCION_ADMIN",
    }

    def __init__(self, database: DatabaseManager):
        self.database = database

    @classmethod
    def agregar(cls, session, accion: str, usuario_id: int | None, origen: str, detalle: str) -> None:
        if accion not in cls.ACCIONES:
            raise ValueError(f"Acción de auditoría no permitida: {accion}")
        session.add(AuditoriaLog(
            fecha_hora=datetime.now(),
            usuario_id=usuario_id,
            accion=accion,
            origen=origen[:120],
            detalle=detalle[:2000],
        ))

    def registrar(self, accion: str, usuario_id: int | None, origen: str, detalle: str) -> None:
        with self.database.session() as session:
            self.agregar(session, accion, usuario_id, origen, detalle)
