from pathlib import Path

from config import BACKUP_DIR
from database.db_manager import DatabaseManager
from services.backup_service import BackupService


class BackupController:
    def __init__(self, database: DatabaseManager, backup_dir: str | Path = BACKUP_DIR):
        self.service = BackupService(database.database_path, backup_dir)

    def crear_backup(self) -> tuple[bool, str]:
        return self.service.crear_backup()