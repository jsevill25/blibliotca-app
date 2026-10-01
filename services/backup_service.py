from datetime import datetime
from pathlib import Path
import sqlite3


class BackupService:
    def __init__(self, database_path: str | Path, backup_dir: str | Path, max_backups: int = 7):
        self.database_path = Path(database_path)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

    def crear_backup(self) -> tuple[bool, str]:
        origen = destino = None
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            marca = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            ruta = self.backup_dir / f"biblioteca_{marca}.db"
            origen = sqlite3.connect(self.database_path)
            destino = sqlite3.connect(ruta)
            origen.backup(destino)
            destino.close()
            destino = None
            origen.close()
            origen = None
            copias = sorted(self.backup_dir.glob("biblioteca_*.db"), key=lambda item: item.stat().st_mtime, reverse=True)
            for antigua in copias[self.max_backups:]:
                antigua.unlink()
            return True, str(ruta)
        except Exception as error:
            return False, str(error)
        finally:
            if destino is not None:
                destino.close()
            if origen is not None:
                origen.close()