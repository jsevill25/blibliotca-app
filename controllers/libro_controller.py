# -*- coding: utf-8 -*-
from models.libro_model import LibroModel

class LibroController:
    def __init__(self):
        self.model = LibroModel()
        self.usuario_activo = "invitado"
        self.rol_activo = "invitado"

    def intentar_login(self, username, password):
        resultado = self.model.validar_usuario(username, password)
        if resultado:
            self.usuario_activo = username
            self.rol_activo = resultado[0]
            self.model.escribir_bitacora(username, "Login", "Acceso concedido.")
            return True, resultado[0]
        return False, "Usuario o contraseña incorrectos."

    def registrar_recepcion(self, isbn, titulo, autor, editorial, anio, origen, id_ejemplar):
        if not isbn or not titulo or not autor or not id_ejemplar or not origen:
            return False, "Por favor complete los campos obligatorios para Recepción."
        exito, msg = self.model.registrar_recepcion_basica(
            isbn, titulo, autor, editorial, int(anio) if anio.isdigit() else 2026, origen, id_ejemplar
        )
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "RECEPCION", f"Recibió libro {titulo} (Copia: {id_ejemplar})")
        return exito, msg

    def procesar_catalogacion(self, isbn, id_ejemplar, dewey_codigo, dewey_nombre, sala, estante, edicion, tema, clasificacion, idioma):
        if not dewey_codigo or not sala or not estante:
            return False, "Seleccione un Código Dewey, una Sala y un Estante obligatoriamente."
        exito, msg = self.model.procesar_catalogacion_completa(
            isbn, id_ejemplar, dewey_codigo, dewey_nombre, sala, estante, edicion, tema, clasificacion, idioma
        )
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "CATALOGACION", f"Catalogó ejemplar {id_ejemplar} bajo código Dewey {dewey_codigo}")
        return exito, msg

    def actualizar_libro_y_ejemplar(self, isbn, titulo, autor, editorial, anio, edicion, tema, dewey_codigo, clasificacion, idioma, origen, id_unico, estado, sala, estante, biblioteca_id):
        exito, msg = self.model.actualizar_libro_y_ejemplar(
            isbn, titulo, autor, editorial, int(anio) if str(anio).isdigit() else 2026,
            edicion, tema, dewey_codigo, clasificacion, idioma, origen, id_unico, estado, sala, estante, int(biblioteca_id)
        )
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "MODIFICACION", f"Modificó ficha de libro/ejemplar {id_unico}")
        return exito, msg

    # --- CONTEOS EN CALIENTE ---
    def obtener_conteo_existencias(self):
        return self.model.obtener_inventario_consolidado()

    # --- SEDES ---
    def registrar_sede(self, nombre, direccion, tipo, encargado, contacto):
        if not nombre or not tipo:
            return False, "Nombre y Tipo son requeridos."
        exito, msg = self.model.registrar_biblioteca(nombre, direccion, tipo, encargado, contacto)
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "REGISTRO_SEDE", f"Creó sede: {nombre} (Encargado: {encargado})")
        return exito, msg

    def actualizar_sede(self, id_sede, nombre, direccion, tipo, encargado, contacto):
        exito, msg = self.model.actualizar_biblioteca(id_sede, nombre, direccion, tipo, encargado, contacto)
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "MODIFICACION_SEDE", f"Actualizó sede ID {id_sede}")
        return exito, msg

    # --- USUARIOS ---
    def listar_usuarios(self):
        return self.model.obtener_usuarios()

    def guardar_usuario(self, id_u, user, passw, rol, perm):
        if not user or not passw or not rol:
            return False, "Complete los campos de usuario."
        if id_u is None:
            exito, msg = self.model.registrar_usuario(user, passw, rol, perm)
            if exito:
                self.model.escribir_bitacora(self.usuario_activo, "REGISTRO_USUARIO", f"Creó usuario {user}")
            return exito, msg
        else:
            exito, msg = self.model.actualizar_usuario(id_u, user, passw, rol, perm)
            if exito:
                self.model.escribir_bitacora(self.usuario_activo, "MODIFICACION_USUARIO", f"Editó usuario {user}")
            return exito, msg

    def borrar_usuario(self, id_u, user):
        exito, msg = self.model.eliminar_usuario(id_u)
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "ELIMINAR_USUARIO", f"Eliminó usuario {user}")
        return exito, msg

    # --- INVENTARIOS ---
    def obtener_inventario_completo(self):
        return self.model.obtener_todos_ejemplares()

    def obtener_inventario_sede(self, biblioteca_id):
        return self.model.obtener_ejemplares_por_biblioteca(biblioteca_id)

    def listar_bibliotecas(self):
        return self.model.obtener_bibliotecas()

    # --- DISTRIBUCIONES ---
    def listar_distribuciones(self):
        return self.model.obtener_todas_distribuciones()

    def obtener_detalles_distribucion(self, dist_id):
        return self.model.obtener_detalle_distribucion(dist_id)

    def enviar_distribucion(self, destino_id, ejemplares_ids, responsable, observaciones):
        exito, msg = self.model.procesar_distribucion(1, destino_id, ejemplares_ids, responsable, observaciones)
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "DISTRIBUCION", f"Despachó {len(ejemplares_ids)} libros a Sede {destino_id}")
        return exito, msg

    def recibir_ejemplar_en_sede(self, ejemplar_id):
        exito, msg = self.model.confirmar_recepcion_lote(ejemplar_id)
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "RECEPCION_SEDE", f"Sede dependiente recibió ejemplar {ejemplar_id}")
        return exito, msg

    def dar_de_baja_ejemplar(self, ejemplar_id, motivo):
        exito, msg = self.model.actualizar_estado_ejemplar(ejemplar_id, "dado de baja")
        if exito:
            self.model.escribir_bitacora(self.usuario_activo, "BAJA", f"Baja física ID: {ejemplar_id}. Motivo: {motivo}")
        return exito, msg

    def realizar_copia_seguridad(self, ruta_destino):
        return self.model.realizar_backup(ruta_destino)

    def exportar_todo_a_csv_excel(self, carpeta_destino):
        return self.model.exportar_todo_a_csv(carpeta_destino)

    def obtener_auditoria(self):
        return self.model.obtener_logs_auditoria()

    def obtener_kpis(self):
        return self.model.obtener_estadisticas_generales()
