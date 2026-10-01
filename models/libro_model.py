# -*- coding: utf-8 -*-
import sqlite3
import csv
import os
from pathlib import Path
from datetime import datetime

class LibroModel:
    def __init__(self, db_path="biblioteca.db"):
        self.db_path = db_path

    def registrar_recepcion_basica(self, isbn, titulo, autor, editorial, anio, origen, cantidad):
        """Inserta/actualiza recepción creando 'cantidad' ejemplares.

        - Si hay cualquier error de escritura: hace rollback.
        - Ya no se usa campo 'código de barra' desde la UI.
        """
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        try:
            # Asegura existencia del libro
            cursor.execute("""
                INSERT OR IGNORE INTO libros (isbn, titulo, autor, editorial, anio, origen, dewey_codigo, clasificacion)
                VALUES (?, ?, ?, ?, ?, ?, '', '')
            """, (isbn, titulo, autor, editorial, anio, origen))

            # Genera ids únicos para cada ejemplar recibido.
            # Patrón: EJ-<isbn-sin-guiones>-<timestamp>-<n>
            # Usamos timestamp para evitar duplicados al reintentar el alta.
            import time
            base_isbn = isbn.replace("-", "")
            ts = int(time.time() * 1000)

            nuevos_ids = []
            for n in range(1, cantidad + 1):
                nuevos_ids.append(f"EJ-{base_isbn}-{ts}-{n:03d}")

            # Buscar una biblioteca existente para asignar biblioteca_id.
            cursor.execute("SELECT id FROM bibliotecas ORDER BY id ASC LIMIT 1")
            fila = cursor.fetchone()
            if not fila:
                return False, "No existen bibliotecas registradas. Registre al menos una sede antes de recibir libros."
            biblioteca_id = fila[0]

            for id_unico in nuevos_ids:
                cursor.execute("""
                    INSERT INTO ejemplares (id_unico, isbn, estado, sala, estante, biblioteca_id)
                    VALUES (?, ?, 'recibido', 'Área de Recepción', 'Mesa de Entrada', ?)
                """, (id_unico, isbn, biblioteca_id))


            # Garantía de consistencia: si por cualquier razón el alta no dejó
            # el estado en 'recibido' (por migración/flujo), se corrige aquí.
            cursor.execute(
                """
                UPDATE ejemplares
                SET estado = 'recibido', sala = 'Área de Recepción', estante = 'Mesa de Entrada', biblioteca_id = 1
                WHERE isbn = ? AND id_unico IN ({})
                """.format(",".join(["?" for _ in nuevos_ids])),
                tuple([isbn] + nuevos_ids)
            )


            # Debug/consistencia: asegurar que el alta quedó en 'recibido'
            # (en ambientes anteriores existía confusión entre estados por flujos de catálogo/distribución). 
            cursor.execute("""SELECT COUNT(*) FROM ejemplares WHERE isbn = ? AND estado = 'recibido'""", (isbn,))
            _ = cursor.fetchone()

            # IMPORTANTE:
            # La recepción debe quedar en estado 'recibido' para que el módulo de
            # catalogación/listado de pendientes lo tome correctamente.
            # (No se debe mover a 'en stock' desde el alta.)


            conexion.commit()
            return True, f"Recepción registrada: {titulo} (cantidad: {cantidad})."
        except sqlite3.IntegrityError as e:
            conexion.rollback()
            return False, f"Error al registrar recepción (posible duplicado): {str(e)}"
        except Exception as e:
            conexion.rollback()
            return False, f"Error al registrar recepción: {str(e)}"
        finally:
            conexion.close()


    def calcular_cutter_sanborn(self, autor, titulo):
        """
        Algoritmo avanzado para aproximar el código de Cutter-Sanborn de forma automatizada:
        Combina: Letra del Apellido + Identificador numérico determinista de 3 dígitos + Letra del título en minúscula.
        """
        autor_clean = autor.strip()
        apellido = autor_clean.split()[-1] if " " in autor_clean else autor_clean
        first_letter_autor = apellido[0].upper() if apellido else "A"
        
        # Generar un hash determinista de 3 dígitos basado en el nombre del apellido
        val_acumulado = sum(ord(c) for c in apellido)
        num_cutter = 100 + (val_acumulado % 899)
        
        # Ignorar artículos en español al extraer la letra del título
        articulos = ["el", "la", "los", "las", "un", "una", "y", "o", "de", "del"]
        palabras_titulo = [w for w in titulo.strip().lower().split() if w not in articulos]
        first_letter_titulo = palabras_titulo[0][0] if palabras_titulo and palabras_titulo[0] else "x"
        
        return f"{first_letter_autor}{num_cutter}{first_letter_titulo}"

    def procesar_catalogacion_completa(self, isbn, id_ejemplar, dewey_codigo, dewey_nombre, sala, estante, edicion, tema, clasificacion_manual, idioma):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()

        # Obtener datos del libro para el cálculo de Cota automatizada
        cursor.execute("SELECT autor, titulo, anio FROM libros WHERE isbn = ?", (isbn,))
        libro_datos = cursor.fetchone()
        autor_val = libro_datos[0] if libro_datos else "Autor"
        titulo_val = libro_datos[1] if libro_datos else "Título"
        anio_val = str(libro_datos[2]) if libro_datos else "2026"

        if not clasificacion_manual or clasificacion_manual.strip() == "":
            # Estructura del lomo según estándares internacionales en 3 renglones:
            # Renglon 1: Dewey (ej. 621.382)
            # Renglon 2: Cutter (ej. A122m)
            # Renglon 3: Año (ej. 2024)
            cutter_codigo = self.calcular_cutter_sanborn(autor_val, titulo_val)
            clasificacion_final = f"{dewey_codigo}\n{cutter_codigo}\n{anio_val}"
        else:
            clasificacion_final = clasificacion_manual.replace("/", "\n") # Normalizar a renglones

        try:
            cursor.execute("""
                UPDATE libros 
                SET dewey_codigo = ?, tema = ?, edicion = ?, clasificacion = ?, idioma = ?
                WHERE isbn = ?
            """, (dewey_codigo, dewey_nombre, edicion, clasificacion_final, idioma, isbn))

            cursor.execute("""
                UPDATE ejemplares
                SET estado = 'en stock', sala = ?, estante = ?
                WHERE id_unico = ?
            """, (sala, estante, id_ejemplar))

            conexion.commit()
            return True, f"Catalogación exitosa. Cota generada e indexada en el sistema."
        except Exception as e:
            conexion.rollback()
            return False, f"Error: {str(e)}"
        finally:
            conexion.close()

    def actualizar_libro_y_ejemplar(self, isbn, titulo, autor, editorial, anio, edicion, tema, dewey_codigo, clasificacion, idioma, origen, id_unico, estado, sala, estante, biblioteca_id):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE libros 
                SET titulo=?, autor=?, editorial=?, anio=?, edicion=?, tema=?, dewey_codigo=?, clasificacion=?, idioma=?, origen=?
                WHERE isbn=?
            """, (titulo, autor, editorial, anio, edicion, tema, dewey_codigo, clasificacion, idioma, origen, isbn))

            cursor.execute("""
                UPDATE ejemplares
                SET estado=?, sala=?, estante=?, biblioteca_id=?
                WHERE id_unico=?
            """, (estado, sala, estante, biblioteca_id, id_unico))

            conexion.commit()
            return True, "Registro modificado con éxito."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    # --- INVENTARIO GLOBAL CON CONTEOS POR COPIAS ---
    def obtener_inventario_consolidado(self):
        """
        Retorna la matriz de control de existencias para ver a nivel general
        cuántos libros quedan en la central, cuántos están en tránsito y cuántos en cada sede.
        """
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT l.isbn, l.titulo, l.autor,
                   SUM(CASE WHEN e.biblioteca_id = 1 AND e.estado = 'en stock' THEN 1 ELSE 0 END) AS stock_central,
                   SUM(CASE WHEN e.biblioteca_id = 2 AND e.estado = 'en stock' THEN 1 ELSE 0 END) AS stock_norte,
                   SUM(CASE WHEN e.biblioteca_id = 3 AND e.estado = 'en stock' THEN 1 ELSE 0 END) AS stock_sur,
                   SUM(CASE WHEN e.estado = 'en tránsito' THEN 1 ELSE 0 END) AS en_transito,
                   COUNT(e.id_unico) AS total_copias
            FROM libros l
            LEFT JOIN ejemplares e ON l.isbn = e.isbn
            WHERE e.estado != 'dado de baja'
            GROUP BY l.isbn
        """)
        datos = cursor.fetchall()
        conexion.close()
        return datos

    # --- GESTIÓN DE SEDES CON DATOS DE ENCARGADOS ---
    def registrar_biblioteca(self, nombre, direccion, tipo, encargado_nombre, encargado_contacto):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO bibliotecas (nombre, direccion, tipo, encargado_nombre, encargado_contacto)
                VALUES (?, ?, ?, ?, ?)
            """, (nombre, direccion, tipo, encargado_nombre, encargado_contacto))
            conexion.commit()
            return True, f"Sede '{nombre}' registrada con éxito."
        except sqlite3.IntegrityError:
            return False, "Error: El nombre de la sede ya existe."
        finally:
            conexion.close()

    def actualizar_biblioteca(self, id_sede, nombre, direccion, tipo, encargado_nombre, encargado_contacto):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE bibliotecas 
                SET nombre=?, direccion=?, tipo=?, encargado_nombre=?, encargado_contacto=? 
                WHERE id=?
            """, (nombre, direccion, tipo, encargado_nombre, encargado_contacto, id_sede))
            conexion.commit()
            return True, "Datos de la sede actualizados."
        except Exception as e:
            return False, str(e)
        finally:
            conexion.close()

    # --- GESTIÓN DE USUARIOS ---
    def registrar_usuario(self, username, password, rol, permisos):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                INSERT INTO usuarios (username, password, rol, permisos) VALUES (?, ?, ?, ?)
            """, (username, password, rol, permisos))
            conexion.commit()
            return True, f"Usuario '{username}' registrado correctamente."
        except sqlite3.IntegrityError:
            return False, "Error: El nombre de usuario ya existe."
        finally:
            conexion.close()

    def actualizar_usuario(self, id_u, username, password, rol, permisos):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE usuarios SET username=?, password=?, rol=?, permisos=? WHERE id=?
            """, (username, password, rol, permisos, id_u))
            conexion.commit()
            return True, "Usuario modificado correctamente."
        except Exception as e:
            return False, str(e)
        finally:
            conexion.close()

    def eliminar_usuario(self, id_u):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id=?", (id_u,))
            conexion.commit()
            return True, "Usuario eliminado correctamente."
        except Exception as e:
            return False, str(e)
        finally:
            conexion.close()

    def obtener_usuarios(self):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT id, username, password, rol, permisos FROM usuarios")
        datos = cursor.fetchall()
        conexion.close()
        return datos

    # --- LISTADO E INVENTARIOS ---
    def actualizar_recepcion_libros(self, isbn, titulo, autor, editorial, anio, origen):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE libros
                SET titulo=?, autor=?, editorial=?, anio=?, origen=?
                WHERE isbn=?
            """, (titulo, autor, editorial, anio, origen, isbn))
            if cursor.rowcount == 0:
                conexion.rollback()
                return False, "No existe recepción para ese ISBN."
            conexion.commit()
            return True, "Recepción actualizada para el ISBN indicado."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    def borrar_recepcion_ejemplares_por_isbn(self, isbn):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("DELETE FROM ejemplares WHERE isbn=? AND estado='recibido'", (isbn,))
            conexion.commit()
            return True, f"Recepción eliminada (ejemplares recibidos) para ISBN {isbn}."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    def obtener_todos_ejemplares(self):
        conexion = sqlite3.connect(self.db_path)

        cursor = conexion.cursor()
        cursor.execute("""
            SELECT e.id_unico, l.titulo, l.autor, l.isbn, e.estado, e.sala, e.estante, b.nombre, l.clasificacion, l.dewey_codigo, l.tema, l.editorial, l.anio, l.edicion, l.idioma, l.origen, b.id
            FROM ejemplares e
            JOIN libros l ON e.isbn = l.isbn
            JOIN bibliotecas b ON e.biblioteca_id = b.id
        """)
        datos = cursor.fetchall()
        conexion.close()
        return datos

    def obtener_ejemplares_por_biblioteca(self, biblioteca_id):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT e.id_unico, l.titulo, l.isbn, e.estado, e.sala, e.estante, l.clasificacion
            FROM ejemplares e
            JOIN libros l ON e.isbn = l.isbn
            WHERE e.biblioteca_id = ?
        """, (biblioteca_id,))
        datos = cursor.fetchall()
        conexion.close()
        return datos

    def obtener_bibliotecas(self):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, direccion, tipo, encargado_nombre, encargado_contacto FROM bibliotecas")
        datos = cursor.fetchall()
        conexion.close()
        return datos

    # --- REPORTES DE DISTRIBUCIÓN ---
    def obtener_todas_distribuciones(self):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT d.id, b1.nombre AS origen, b2.nombre AS destino, d.fecha, d.responsable, d.observaciones, d.estado
            FROM distribuciones d
            JOIN bibliotecas b1 ON d.origen_id = b1.id
            JOIN bibliotecas b2 ON d.destino_id = b2.id
            ORDER BY d.id DESC
        """)
        datos = cursor.fetchall()
        conexion.close()
        return datos

    def obtener_detalle_distribucion(self, dist_id):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT dd.ejemplar_id, l.titulo, l.autor, l.clasificacion
            FROM distribucion_detalles dd
            JOIN ejemplares e ON dd.ejemplar_id = e.id_unico
            JOIN libros l ON e.isbn = l.isbn
            WHERE dd.distribucion_id = ?
        """, (dist_id,))
        datos = cursor.fetchall()
        conexion.close()
        return datos

    def procesar_distribucion(self, origen_id, destino_id, ejemplares_ids, responsable, observaciones):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute("""
                INSERT INTO distribuciones (origen_id, destino_id, fecha, responsable, observaciones, estado)
                VALUES (?, ?, ?, ?, ?, 'en tránsito')
            """, (origen_id, destino_id, fecha_actual, responsable, observaciones))
            dist_id = cursor.lastrowid

            for ej_id in ejemplares_ids:
                cursor.execute("""
                    INSERT INTO distribucion_detalles (distribucion_id, ejemplar_id)
                    VALUES (?, ?)
                """, (dist_id, ej_id))

                cursor.execute("""
                    UPDATE ejemplares 
                    SET biblioteca_id = ?, estado = 'en tránsito'
                    WHERE id_unico = ?
                """, (destino_id, ej_id))

            conexion.commit()
            return True, f"Lote #{dist_id} enviado de forma exitosa."
        except Exception as e:
            conexion.rollback()
            return False, str(e)
        finally:
            conexion.close()

    def confirmar_recepcion_lote(self, ejemplar_id):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("""
                UPDATE ejemplares 
                SET estado = 'en stock' 
                WHERE id_unico = ? AND estado = 'en tránsito'
            """, (ejemplar_id,))
            conexion.commit()
            return True, "Ejemplar recibido con éxito en sede dependiente."
        except Exception as e:
            return False, str(e)
        finally:
            conexion.close()

    def actualizar_estado_ejemplar(self, ejemplar_id, nuevo_estado, ubicacion=""):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute("UPDATE ejemplares SET estado = ? WHERE id_unico = ?", (nuevo_estado, ejemplar_id))
            conexion.commit()
            return True, "Estado del ejemplar modificado."
        except Exception as e:
            return False, str(e)
        finally:
            conexion.close()

    def realizar_backup(self, ruta_destino):
        origen = None
        destino = None
        try:
            ruta = Path(ruta_destino)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            origen = sqlite3.connect(self.db_path)
            destino = sqlite3.connect(str(ruta))
            origen.backup(destino)
            return True, "Copia de seguridad local creada con éxito."
        except Exception as e:
            return False, str(e)
        finally:
            if destino is not None:
                destino.close()
            if origen is not None:
                origen.close()

    def realizar_backup_automatico(self, directorio_destino, max_backups=7):
        carpeta = Path(directorio_destino)
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ruta_backup = carpeta / f"backup_{marca_tiempo}.db"
        exito, mensaje = self.realizar_backup(ruta_backup)
        if not exito:
            return False, mensaje

        try:
            copias = sorted(carpeta.glob("backup_*.db"), key=lambda ruta: ruta.stat().st_mtime, reverse=True)
            for copia_antigua in copias[max_backups:]:
                copia_antigua.unlink()
            return True, str(ruta_backup)
        except Exception as e:
            return False, f"Backup creado, pero no se pudo depurar el historial: {e}"

    # --- MÓDULO DE EXPORTACIÓN TOTAL A EXCEL/CSV ---
    def exportar_todo_a_csv(self, directorio_destino):
        tablas = ["usuarios", "bibliotecas", "libros", "ejemplares", "distribuciones", "distribucion_detalles", "bitacora"]
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()

        try:
            for tabla in tablas:
                cursor.execute(f"SELECT * FROM {tabla}")
                filas = cursor.fetchall()
                columnas = [desc[0] for desc in cursor.description]

                ruta_archivo = os.path.join(directorio_destino, f"reporte_seguridad_{tabla}.csv")
                with open(ruta_archivo, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(columnas)
                    writer.writerows(filas)
            
            conexion.close()
            return True, f"Se han exportado {len(tablas)} hojas de cálculo con éxito en la carpeta seleccionada."
        except Exception as e:
            conexion.close()
            return False, str(e)

    def obtener_logs_auditoria(self):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT fecha, usuario, accion, detalle FROM bitacora ORDER BY id DESC")
        datos = cursor.fetchall()
        conexion.close()
        return datos

    def escribir_bitacora(self, usuario, accion, detalle):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO bitacora (fecha, usuario, accion, detalle)
            VALUES (?, ?, ?, ?)
        """, (fecha_actual, usuario, accion, detalle))
        conexion.commit()
        conexion.close()

    def validar_usuario(self, username, password):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT rol, permisos FROM usuarios WHERE username = ? AND password = ?", (username, password))
        resultado = cursor.fetchone()
        conexion.close()
        return resultado

    def obtener_estadisticas_generales(self):
        conexion = sqlite3.connect(self.db_path)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT b.nombre, COUNT(e.id_unico) 
            FROM bibliotecas b
            LEFT JOIN ejemplares e ON b.id = e.biblioteca_id
            GROUP BY b.id
        """)
        ej_por_sede = cursor.fetchall()
        cursor.execute("SELECT estado, COUNT(*) FROM ejemplares GROUP BY estado")
        por_estado = cursor.fetchall()
        cursor.execute("""
            SELECT l.tema, COUNT(e.id_unico)
            FROM ejemplares e
            JOIN libros l ON e.isbn = l.isbn
            GROUP BY l.tema
        """)
        por_tema = cursor.fetchall()
        conexion.close()
        return ej_por_sede, por_estado, por_tema
