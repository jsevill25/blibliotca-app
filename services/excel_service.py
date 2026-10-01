from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import MetaData


class ExcelService:
    def exportar(self, hojas: dict[str, list[dict]], destino: str | Path) -> Path:
        return self._escribir(hojas, destino)

    def exportar_base_datos(self, engine, destino: str | Path) -> Path:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        hojas = {}
        with engine.connect() as connection:
            for tabla in metadata.sorted_tables:
                filas = [dict(fila._mapping) for fila in connection.execute(tabla.select())]
                hojas[tabla.name] = {"columnas": [columna.name for columna in tabla.columns], "filas": filas}
        return self._escribir(hojas, destino, datos_crudos=True)

    def _escribir(self, hojas: dict[str, list[dict]], destino: str | Path, datos_crudos: bool = False) -> Path:
        libro = Workbook()
        libro.remove(libro.active)
        for nombre, contenido in hojas.items():
            hoja = libro.create_sheet(nombre[:31])
            if datos_crudos:
                columnas = contenido["columnas"]
                filas = contenido["filas"]
            else:
                filas = contenido
                columnas = list(filas[0]) if filas else []
            if columnas:
                hoja.append(columnas)
                for celda in hoja[1]:
                    celda.font = Font(bold=True, color="FFFFFF")
                    celda.fill = PatternFill("solid", fgColor="1A1A1A")
                for fila in filas:
                    hoja.append([fila.get(columna, "") for columna in columnas])
                hoja.freeze_panes = "A2"
                hoja.auto_filter.ref = hoja.dimensions
                for indice, columna in enumerate(hoja.columns, 1):
                    ancho = min(max(max(len(str(celda.value or "")) for celda in columna) + 2, 12), 48)
                    hoja.column_dimensions[get_column_letter(indice)].width = ancho
        ruta = Path(destino)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        libro.save(ruta)
        return ruta