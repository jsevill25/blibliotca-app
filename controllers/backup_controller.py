from pathlib import Path

from config import BACKUP_DIR
from database.db_manager import DatabaseManager
from services.audit_service import AuditService
from services.backup_service import BackupService


class BackupController:
    def __init__(self, database: DatabaseManager, backup_dir: str | Path = BACKUP_DIR):
        self.database = database
        self.service = BackupService(database.database_path, backup_dir)

    def crear_backup(self, usuario_id: int | None = None, origen: str = "aplicacion") -> tuple[bool, str]:
        exito, resultado = self.service.crear_backup()
        if exito:
            AuditService(self.database).registrar(
                "RESPALDO_DB", usuario_id, origen, f"Creó el respaldo SQLite '{Path(resultado).name}'.",
            )
        return exito, resultado