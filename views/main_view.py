# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import os

class MainView(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.title("SPGB ROMULO - GALLEGOS")
        self.geometry("1280x820")
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

        # ===================== THEME: NEGRO / BLANCO / AMARILLO =====================
        # Se usa Light para evitar problemas visuales del modo Dark en combinaciones hardcodeadas.
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        # Paleta global (reemplazo progresivo de colores hardcodeados)
        self.T_BG = "#0B0B0B"        # negro
        self.T_PANEL = "#111111"     # panel
        self.T_CARD = "#FFFFFF8B"      # card
        self.T_TEXT = "#0B0B0B"      # texto
        self.T_TEXT_INV = "#FFFFFF"  # texto invertido
        self.T_BORDER = "#333333"    # borde
        self.T_MUTED = "#777777"     # texto tenue
        self.T_ACCENT = "#FFCC33"    # amarillo acento
        self.T_ACCENT_2 = "#F7C948"  # amarillo secundario
        self.T_PRIMARY = "#3C8DBC"   # primario
        self.T_SUCCESS = "#00A65A"   # verde
        self.T_WARNING = "#F39C12"   # naranja/alerta
        self.T_DANGER = "#C23321"    # peligro




        # Catálogo Dewey para automatización rápida
        self.dewey_categorias = {
            "000": "Generalidades y Computación",
            "100": "Filosofía y Psicología",
            "200": "Religión",
            "300": "Ciencias Sociales",
            "400": "Lenguas e Idiomas",
            "500": "Ciencias Naturales y Matemáticas",
            "600": "Tecnología (Ciencias Aplicadas)",
            "621.382": "Telecomunicaciones (Dewey)",
            "700": "Bellas Artes y Recreación",
            "800": "Literatura y Retórica",
            "900": "Geografía e Historia"
        }

        self.mostrar_pantalla_login()

    def limpiar_ventana(self):
        for widget in self.winfo_children():
            widget.destroy()

    def cerrar_aplicacion(self):
        exito, resultado = self.controller.realizar_backup_automatico()
        if not exito and not messagebox.askyesno(
            "No se pudo respaldar",
            f"{resultado}\n\n¿Desea cerrar la aplicación de todos modos?",
        ):
            return
        self.destroy()

    # ========================== LOGIN ==========================
    def mostrar_pantalla_login(self):
        self.limpiar_ventana()
        login_frame = ctk.CTkFrame(self, width=420, height=520, corner_radius=12, fg_color="white", border_width=1, border_color="#E0E0E0")
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        header_login = ctk.CTkFrame(login_frame, height=90, fg_color="#222D32", corner_radius=0)
        header_login.pack(fill="x", side="top")
        ctk.CTkLabel(header_login, text="INICIAR SESIÒN", font=("Helvetica", 18, "bold"), text_color="white").pack(pady=13)
        ctk.CTkLabel(header_login, text="Control e Inventario Central de Sedes", font=("Helvetica", 11), text_color="#A0A0A0").pack()

        ctk.CTkLabel(login_frame, text="Usuario:", font=("Helvetica", 12, "bold"), text_color="#333").pack(pady=(35, 5), anchor="w", padx=45)
        self.entry_user = ctk.CTkEntry(login_frame, width=330, height=35, placeholder_text="Nombre de usuario")
        self.entry_user.pack()

        ctk.CTkLabel(login_frame, text="Contraseña:", font=("Helvetica", 12, "bold"), text_color="#333").pack(pady=(15, 5), anchor="w", padx=45)
        self.entry_pass = ctk.CTkEntry(login_frame, width=330, height=35, show="*", placeholder_text="Contraseña")
        self.entry_pass.pack()

        btn_login = ctk.CTkButton(login_frame, text="Iniciar Sesión", fg_color="#3C8DBC", hover_color="#367FA9", width=330, height=40, command=self.procesar_login)
        btn_login.pack(pady=35)

    def procesar_login(self):
        user = self.entry_user.get()
        passwd = self.entry_pass.get()
        exito, rol_o_msg = self.controller.intentar_login(user, passwd)
        if exito:
            self.mostrar_dashboard_principal()
        else:
            messagebox.showerror("Error de Credenciales", rol_o_msg)

    # ========================== DASHBOARD PRINCIPAL ==========================
    def mostrar_dashboard_principal(self):
        self.limpiar_ventana()

        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#222D32")
        self.sidebar_frame.pack(side="left", fill="y")

        logo_frame = ctk.CTkFrame(self.sidebar_frame, height=60, fg_color="#1A2226", corner_radius=0)
        logo_frame.pack(fill="x", side="top")
        ctk.CTkLabel(logo_frame, text="SPGB-ROMULO GALLEGOS", font=("Helvetica", 16, "bold"), text_color="#FFFFFF").pack(pady=15)

        user_info = f"Activo: {self.controller.usuario_activo}\nRol: {self.controller.rol_activo}"
        ctk.CTkLabel(self.sidebar_frame, text=user_info, font=("Helvetica", 12, "bold"), text_color="#3C8DBC").pack(pady=15)

        rol = self.controller.rol_activo

        btn_dash = ctk.CTkButton(self.sidebar_frame, text="Dashboard Central", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_dashboard)
        btn_dash.pack(fill="x", padx=10, pady=2)

        if rol in ["Administrador", "Bibliotecario Central"]:
            btn_rec = ctk.CTkButton(self.sidebar_frame, text="1. Recepción (Entrada)", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_recepcion)
            btn_rec.pack(fill="x", padx=10, pady=2)

            btn_cat = ctk.CTkButton(self.sidebar_frame, text="2. Catalogación (Dewey)", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_catalogacion)
            btn_cat.pack(fill="x", padx=10, pady=2)

            btn_inv_c = ctk.CTkButton(self.sidebar_frame, text="Existencias y Conteos", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_inventario_central)
            btn_inv_c.pack(fill="x", padx=10, pady=2)

            btn_dist = ctk.CTkButton(self.sidebar_frame, text="Distribución de Lotes", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_distribucion)
            btn_dist.pack(fill="x", padx=10, pady=2)

        btn_sedes = ctk.CTkButton(self.sidebar_frame, text="Gestión de Sedes", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_sedes)
        btn_sedes.pack(fill="x", padx=10, pady=2)

        btn_etiq = ctk.CTkButton(self.sidebar_frame, text="Impresión de Cotas (cm)", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_etiquetas)
        btn_etiq.pack(fill="x", padx=10, pady=2)

        btn_rep = ctk.CTkButton(self.sidebar_frame, text="Reportes y Fichas", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_reportes)
        btn_rep.pack(fill="x", padx=10, pady=2)

        if rol == "Administrador":
            btn_admin = ctk.CTkButton(self.sidebar_frame, text="Consola de Administración", fg_color="transparent", text_color="#B8C7CE", hover_color="#1A2226", anchor="w", command=self.vista_administracion)
            btn_admin.pack(fill="x", padx=10, pady=2)

        btn_logout = ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", fg_color="#DD4B39", hover_color="#C23321", text_color="white", command=self.mostrar_pantalla_login)
        btn_logout.pack(side="bottom", fill="x", padx=15, pady=15)

        self.main_content_canvas = ctk.CTkFrame(self, fg_color="#F4F6F9", corner_radius=0)
        self.main_content_canvas.pack(side="right", fill="both", expand=True)

        self.vista_dashboard()

    def dibujar_cabecera_modulo(self, titulo_modulo, subtitulo):
        header_frame = ctk.CTkFrame(self.main_content_canvas, height=55, fg_color="white", corner_radius=0, border_width=1, border_color="#D2D6DE")
        header_frame.pack(fill="x", side="top")
        
        ctk.CTkLabel(header_frame, text=titulo_modulo.upper(), font=("Helvetica", 14, "bold"), text_color="#333333").pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(header_frame, text=f"|  {subtitulo}", font=("Helvetica", 10), text_color="#777777").pack(side="left", pady=15)

        self.content_frame = ctk.CTkFrame(self.main_content_canvas, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=15)

    def limpiar_contenido_activo(self):
        for widget in self.main_content_canvas.winfo_children():
            widget.destroy()

    # ========================== VISTA: DASHBOARD ==========================
    def vista_dashboard(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Dashboard Principal", "Resumen de estado e inventario central")

        sedes, estados, temas = self.controller.obtener_kpis()

        total_libros = sum([x[1] for x in sedes])
        total_en_stock = sum([x[1] for x in estados if x[0] == "en stock"])
        total_recibidos = sum([x[1] for x in estados if x[0] == "recibido"])

        tarjetas_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tarjetas_frame.pack(fill="x", pady=10)

        # KPIs
        c1 = ctk.CTkFrame(tarjetas_frame, width=220, height=100, fg_color="#00C0EF", corner_radius=5)
        c1.pack(side="left", expand=True, padx=10)
        ctk.CTkLabel(c1, text="Total Ejemplares", font=("Helvetica", 11, "bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(c1, text=str(total_libros), font=("Helvetica", 24, "bold"), text_color="white").pack()

        c2 = ctk.CTkFrame(tarjetas_frame, width=220, height=100, fg_color="#00A65A", corner_radius=5)
        c2.pack(side="left", expand=True, padx=10)
        ctk.CTkLabel(c2, text="En Stock Activo", font=("Helvetica", 11, "bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(c2, text=str(total_en_stock), font=("Helvetica", 24, "bold"), text_color="white").pack()

        c3 = ctk.CTkFrame(tarjetas_frame, width=220, height=100, fg_color="#F39C12", corner_radius=5)
        c3.pack(side="left", expand=True, padx=10)
        ctk.CTkLabel(c3, text="Pendientes Catalogar (Recibidos)", font=("Helvetica", 11, "bold"), text_color="white").pack(pady=5)
        ctk.CTkLabel(c3, text=str(total_recibidos), font=("Helvetica", 24, "bold"), text_color="white").pack()

        panel = ctk.CTkFrame(self.content_frame, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        panel.pack(fill="both", expand=True, pady=15, padx=10)

        ctk.CTkLabel(panel, text="Existencias por Biblioteca Sede:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        for idx, (sede, cant) in enumerate(sedes):
            barra = "█" * (cant * 2 if cant > 0 else 1)
            ctk.CTkLabel(panel, text=f"{sede}: {cant} ejemplares  {barra}", font=("Courier New", 11)).grid(row=idx+1, column=0, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(panel, text="Distribución Temática Dewey / Ficha:", font=("Helvetica", 12, "bold")).grid(row=0, column=1, padx=40, pady=15, sticky="w")
        for idx_t, (tema, cant) in enumerate(temas):
            barra = "█" * (cant * 2 if cant > 0 else 1)
            ctk.CTkLabel(panel, text=f"{tema or 'Sin Procesar'}: {cant}  {barra}", font=("Courier New", 11)).grid(row=idx_t+1, column=1, padx=40, pady=4, sticky="w")

    # ========================== VISTA: RECEPCIÓN ==========================
    def vista_recepcion(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("1. Recepción (Entrada básica)", "Ingreso de libros por documento de origen")

        tabs = ctk.CTkTabview(self.content_frame)
        tabs.pack(fill="both", expand=True)

        tab_registrar = tabs.add("Registrar Recepción")
        tab_modificar = tabs.add("Modificar Recepción")

        # ===================== TAB: REGISTRAR =====================
        cont_reg = ctk.CTkFrame(tab_registrar, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        cont_reg.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(cont_reg, text="DATOS GENERALES DE RECEPCIÓN (Mesa de Entrada)", font=("Helvetica", 12, "bold")).pack(pady=15)

        campos_rec = [
            ("ISBN (Obligatorio):", "Ej. 978-X-XXXX-XXXX-X"),
            ("Título del Libro (Obligatorio):", "Título que aparece en el documento"),
            ("Autor (Obligatorio):", "Nombre del autor principal"),
            ("cantidad (Obligatorio):", "cantidad de ejemplares"),
            ("Editorial de Impresión:", "Nombre de la editorial"),
            ("Año de Publicación:", "Ej. 2024"),
        ]

        self.rec_entries = {}
        for idx, (label, place) in enumerate(campos_rec):
            ctk.CTkLabel(cont_reg, text=label, font=("Helvetica", 11, "bold")).place(x=50, y=110 + (idx * 50))
            entry = ctk.CTkEntry(cont_reg, width=320, placeholder_text=place)
            entry.place(x=350, y=105 + (idx * 50))
            self.rec_entries[label] = entry

        ctk.CTkLabel(cont_reg, text="Origen / Procedencia del Libro:", font=("Helvetica", 11, "bold")).place(x=50, y=110 + (len(campos_rec) * 50))
        self.combo_origen_rec = ctk.CTkComboBox(
            cont_reg,
            values=[
                "Biblioteca Nacional",
                "Donación Particular",
                "Compra Directa",
                "Intercambio Institucional",
                "Ministerio de Educación",
            ],
            width=320,
        )
        # Valor por defecto para que el controller no reciba origen vacío
        self.combo_origen_rec.set("Biblioteca Nacional")
        self.combo_origen_rec.place(x=350, y=105 + (len(campos_rec) * 50))


        btn_guardar = ctk.CTkButton(
            cont_reg,
            text="Registrar Recepción (Estado: 'recibido')",
            fg_color="#3C8DBC",
            hover_color="#367FA9",
            height=40,
            command=self.procesar_recepcion_libro,
        )
        btn_guardar.place(x=350, y=160 + (len(campos_rec) * 50))

        # ===================== TAB: MODIFICAR =====================
        cont_mod = ctk.CTkFrame(tab_modificar, fg_color="transparent")
        cont_mod.pack(fill="both", expand=True, padx=10, pady=10)

        barra_buscar = ctk.CTkFrame(cont_mod, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        barra_buscar.pack(fill="x", padx=10, pady=10)

        # Nota: se eliminó el buscador por ISBN para que el usuario vea siempre
        # la lista y seleccione un registro para cargar el formulario.
        barra_buscar.destroy()


        self.tree_recibidos_gestion = ttk.Treeview(
            cont_mod,
            columns=("ISBN", "Título", "Autor", "Editorial", "Año", "Origen", "Cantidad"),
            show="headings",
            selectmode="browse",
            height=8,
        )
        for col in ("ISBN", "Título", "Autor", "Editorial", "Año", "Origen", "Cantidad"):
            self.tree_recibidos_gestion.heading(col, text=col)
            self.tree_recibidos_gestion.column(col, width=110)
        self.tree_recibidos_gestion.pack(fill="x", padx=10, pady=(0, 10))
        self.tree_recibidos_gestion.bind("<<TreeviewSelect>>", self.cargar_recepcion_para_editar)

        # Cargar lista inicialmente (evita que el tab Modificar salga vacío)
        self.llenar_lista_recepcion()

        # Si no hay recepciones registradas todavía, limpia el formulario
        # para que no se vea “cantidad” con valores residuales.
        if "cantidad (Obligatorio):" in self.rec_entries:
            self.rec_entries["cantidad (Obligatorio):"].configure(state="normal")
            self.rec_entries["cantidad (Obligatorio):"].delete(0, tk.END)
            self.rec_entries["cantidad (Obligatorio):"].configure(state="disabled")



        btns = ctk.CTkFrame(cont_mod, fg_color="transparent")
        btns.pack(fill="x", padx=10, pady=(0, 10))
        self.btn_eliminar_recepcion = ctk.CTkButton(
            btns,
            text="Eliminar Recepción (por ISBN)",
            fg_color="#DD4B39",
            hover_color="#C23321",
            command=self.eliminar_recepcion,
        )
        self.btn_eliminar_recepcion.pack(side="left")

        # formulario de edición (horizontal, usando grid)
        form_frame = ctk.CTkFrame(cont_mod, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(form_frame, text="EDITAR RECEPCIÓN (bibliográfico)", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=4, pady=12, sticky="w", padx=25)

        self.recepcion_modo_edicion = False
        self.recepcion_isbn_edit = None

        self.rec_entries = {}

        # Layout en 2 columnas para evitar scroll vertical
        # Columna 0: Etiqueta | Columna 1: Campo
        # Columna 2: Etiqueta | Columna 3: Campo
        campos_ui = [c for c in campos_rec]  # (label, placeholder)
        # Excluimos cantidad porque va deshabilitado y se verá igual

        max_rows = (len(campos_ui) + 1) // 2
        for i, (label, _place) in enumerate(campos_ui):
            row = 1 + (i % max_rows)
            col_pair = i // max_rows
            if col_pair == 0:
                col_label = 0
                col_entry = 1
            else:
                col_label = 2
                col_entry = 3

            ctk.CTkLabel(form_frame, text=label, font=("Helvetica", 11, "bold")).grid(
                row=row, column=col_label, sticky="w", padx=15, pady=4
            )
            entry = ctk.CTkEntry(form_frame, width=260)
            entry.grid(row=row, column=col_entry, sticky="w", padx=15, pady=4)
            self.rec_entries[label] = entry

        # Bloquear cantidad en edición
        if "cantidad (Obligatorio):" in self.rec_entries:
            self.rec_entries["cantidad (Obligatorio):"].configure(state="disabled")

        # Origen (combo) en una fila debajo, ocupando todo el ancho
        ctk.CTkLabel(form_frame, text="Origen / Procedencia del Libro:", font=("Helvetica", 11, "bold")).grid(
            row=1 + max_rows, column=0, columnspan=2, sticky="w", padx=25, pady=6
        )
        self.combo_origen_rec = ctk.CTkComboBox(
            form_frame,
            values=[
                "Biblioteca Nacional",
                "Donación Particular",
                "Compra Directa",
                "Intercambio Institucional",
                "Ministerio de Educación",
            ],
            width=260,
        )
        # Valor por defecto para que el controller no falle si no se selecciona
        self.combo_origen_rec.set("Biblioteca Nacional")
        self.combo_origen_rec.grid(row=1 + max_rows, column=2, columnspan=2, sticky="w", padx=15, pady=6)


        btn_actualizar = ctk.CTkButton(
            form_frame,
            text="Guardar Cambios (Estado: 'recibido')",
            fg_color="#00A65A",
            hover_color="#008D4C",
            height=40,
            command=self.procesar_recepcion_libro,
        )
        btn_actualizar.grid(row=2 + max_rows, column=0, columnspan=4, padx=25, pady=16, sticky="ew")

        # Inicializa el modo de edición y lista de registros
        self.recepcion_modo_edicion = False
        self.recepcion_isbn_edit = None
        self.llenar_lista_recepcion()

        # Botón buscar/bind ya fueron configurados arriba; aquí se asegura que la
        # selección del Treeview cargue el formulario.
        self.tree_recibidos_gestion.bind("<<TreeviewSelect>>", self.cargar_recepcion_para_editar)

    # ========================== RECEPCIÓN: MODIFICAR (UTILIDADES DEL TAB) ==========================
    def llenar_lista_recepcion(self):
        """Carga en el Treeview las recepciones que aún están en estado 'recibido'."""
        if not hasattr(self, "tree_recibidos_gestion"):
            return

        # Limpia árbol
        for item in self.tree_recibidos_gestion.get_children():
            self.tree_recibidos_gestion.delete(item)

        # Trae inventario completo y filtra las entradas en estado 'recibido'
        # Nota: en este sistema 'recibido' corresponde a la tabla ejemplares.
        datos = self.controller.obtener_inventario_completo()

        # Agrupa por ISBN para evitar repetir la misma fila bibliográfica varias veces
        # tomando la primera ocurrencia.
        vistos = set()
        for ej in datos:
            estado = ej[4]
            isbn = ej[3]
            if estado != "recibido" or not isbn or isbn in vistos:
                continue
            vistos.add(isbn)

            titulo = ej[1]
            autor = ej[2]
            editorial = ej[11]
            anio = ej[12]
            origen = ej[15]

            # cantidad = cantidad física por ISBN en 'recibido'
            cant_recibidos = 0
            for ej2 in datos:
                if ej2[3] == isbn and ej2[4] == "recibido":
                    cant_recibidos += 1

            self.tree_recibidos_gestion.insert(
                "",
                "end",
                values=(isbn, titulo, autor, editorial, anio, origen, cant_recibidos),
            )

    def buscar_recepcion(self):
        """(Deprecado) Antes filtraba por ISBN. Ahora el módulo muestra la lista completa siempre."""
        self.llenar_lista_recepcion()


    def cargar_recepcion_para_editar(self, evento):
        """Al seleccionar una fila del Treeview, rellena el formulario de edición."""
        seleccion = self.tree_recibidos_gestion.selection()
        if not seleccion:
            return

        item = self.tree_recibidos_gestion.item(seleccion[0])
        valores = item["values"]
        if not valores:
            return

        isbn, titulo, autor, editorial, anio, origen, _cantidad = valores

        # Setear modo de edición
        self.recepcion_modo_edicion = True
        self.recepcion_isbn_edit = isbn

        # Cargar campos
        self.rec_entries["ISBN (Obligatorio):"].delete(0, tk.END)
        self.rec_entries["ISBN (Obligatorio):"].insert(0, isbn)

        self.rec_entries["Título del Libro (Obligatorio):"].delete(0, tk.END)
        self.rec_entries["Título del Libro (Obligatorio):"].insert(0, titulo or "")

        self.rec_entries["Autor (Obligatorio):"].delete(0, tk.END)
        self.rec_entries["Autor (Obligatorio):"].insert(0, autor or "")

        self.rec_entries["Editorial de Impresión:"].delete(0, tk.END)
        self.rec_entries["Editorial de Impresión:"].insert(0, editorial or "")

        self.rec_entries["Año de Publicación:"].delete(0, tk.END)
        self.rec_entries["Año de Publicación:"].insert(0, str(anio) if anio is not None else "")

        # combo origen
        try:
            vals = self.combo_origen_rec.cget('values')
            if origen and str(origen).strip() and (not vals or origen in vals):
                self.combo_origen_rec.set(origen)
            else:
                if vals:
                    self.combo_origen_rec.set(vals[0])
        except Exception:
            pass

    def eliminar_recepcion(self):
        """Elimina recepción por ISBN (solo si está en estado 'recibido')."""
        seleccion = self.tree_recibidos_gestion.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un registro de recepción para eliminar.")
            return

        item = self.tree_recibidos_gestion.item(seleccion[0])
        valores = item["values"]
        if not valores:
            return
        isbn = valores[0]

        if not messagebox.askyesno("Confirmar", f"¿Eliminar recepción (estado 'recibido') para ISBN: {isbn}?"):
            return

        exito, msg = self.controller.borrar_recepcion_ejemplares(isbn)
        if exito:
            messagebox.showinfo("Eliminado", msg)
            self.recepcion_modo_edicion = False
            self.recepcion_isbn_edit = None
            self.llenar_lista_recepcion()
        else:
            messagebox.showerror("Error", msg)

    def procesar_recepcion_libro(self):

        isbn = self.rec_entries["ISBN (Obligatorio):"].get().strip()
        titulo = self.rec_entries["Título del Libro (Obligatorio):"].get().strip()
        autor = self.rec_entries["Autor (Obligatorio):"].get().strip()
        editorial = self.rec_entries["Editorial de Impresión:"].get().strip()
        anio = self.rec_entries["Año de Publicación:"].get().strip()
        origen = self.combo_origen_rec.get().strip()
        cantidad = self.rec_entries["cantidad (Obligatorio):"].get().strip()

        if self.recepcion_modo_edicion and self.recepcion_isbn_edit:
            # Update bibliográfico (por ISBN). Mantiene cantidad física.
            isbn_update = self.recepcion_isbn_edit
            exito, msg = self.controller.actualizar_recepcion(
                isbn_update, titulo, autor, editorial, anio, origen
            )
        else:
            exito, msg = self.controller.registrar_recepcion(isbn, titulo, autor, editorial, anio, origen, cantidad)

        if exito:
            messagebox.showinfo("Recepción Guardada", msg)
            self.recepcion_modo_edicion = False
            self.recepcion_isbn_edit = None
            # habilitar ISBN y recargar lista
            self.rec_entries["ISBN (Obligatorio):"].configure(state="normal")
            self.llenar_lista_recepcion()
        else:
            messagebox.showerror("Error", msg)


    # ========================== VISTA: CATALOGACIÓN (DEWEY SELECTS AUTOMATED) ==========================
    def vista_catalogacion(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("2. Catalogación y Clasificación Dewey", "Procesamiento bibliográfico para inventario")

        paneles = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        paneles.pack(fill="both", expand=True)

        col_izq = ctk.CTkFrame(paneles, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_izq.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(col_izq, text="Libros Recibidos Pendientes por Catalogar", font=("Helvetica", 11, "bold")).pack(pady=10)

        columnas = ("ID Ejemplar", "Título", "Autor", "ISBN", "Origen")
        self.tree_recibidos = ttk.Treeview(col_izq, columns=columnas, show="headings", selectmode="browse")
        for col in columnas:
            self.tree_recibidos.heading(col, text=col)
            self.tree_recibidos.column(col, width=100)

        self.tree_recibidos.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_recibidos.bind("<<TreeviewSelect>>", self.cargar_libro_para_catalogar)

        datos = self.controller.obtener_inventario_completo()
        for ej in datos:
            if ej[4] == "recibido":
                self.tree_recibidos.insert("", "end", values=(ej[0], ej[1], ej[2], ej[3], ej[15]))

        self.col_der_cat = ctk.CTkScrollableFrame(paneles, width=420, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        self.col_der_cat.pack(side="right", fill="both", padx=5, pady=5)

        ctk.CTkLabel(self.col_der_cat, text="FICHA TÉCNICA DE CATALOGACIÓN", font=("Helvetica", 11, "bold")).pack(pady=10)

        self.cat_id_ejemplar = tk.StringVar(value="Seleccione un libro de la lista")
        self.cat_isbn = tk.StringVar()

        ctk.CTkLabel(self.col_der_cat, textvariable=self.cat_id_ejemplar, font=("Helvetica", 11, "bold"), text_color="#3C8DBC").pack(pady=5)

        # SELECTORES DEWEY COMPLETO AUTOMATIZADO
        ctk.CTkLabel(self.col_der_cat, text="Clasificación Dewey Standard (Select):").pack(anchor="w", padx=20, pady=2)
        dewey_opciones = [f"{k} - {v}" for k, v in self.dewey_categorias.items()]
        self.combo_dewey = ctk.CTkComboBox(self.col_der_cat, values=dewey_opciones, width=320)
        self.combo_dewey.pack(pady=5)

        # UBICACIÓN SALAS EN MESA DESPLEGABLE (SELECT)
        ctk.CTkLabel(self.col_der_cat, text="Sala Destino Central (Select):").pack(anchor="w", padx=20, pady=2)
        self.combo_sala = ctk.CTkComboBox(self.col_der_cat, values=["Sala General", "Sala de Tecnología", "Sala de Referencia", "Sala Infantil", "Hemeroteca", "Depósito Principal", "Sala de Ciencias"], width=320)
        self.combo_sala.pack(pady=5)

        # UBICACIÓN ESTANTES EN SELECT AUTOMATIZADO
        ctk.CTkLabel(self.col_der_cat, text="Estante Destino Central (Select):").pack(anchor="w", padx=20, pady=2)
        self.combo_estante = ctk.CTkComboBox(self.col_der_cat, values=["Estante A-1", "Estante A-2", "Estante B-1", "Estante B-2", "Estante C-1", "Estante C-2", "Estante T-1", "Estante T-2", "Vitrina Especial"], width=320)
        self.combo_estante.pack(pady=5)

        ctk.CTkLabel(self.col_der_cat, text="Edición del Libro (Select):").pack(anchor="w", padx=20, pady=2)
        self.combo_edicion = ctk.CTkComboBox(self.col_der_cat, values=["1ra Edición", "2da Edición", "3ra Edición", "4ta Edición", "Edición Especial", "Reimpresión"], width=320)
        self.combo_edicion.pack(pady=5)

        ctk.CTkLabel(self.col_der_cat, text="Género / Tema del Libro (Select):").pack(anchor="w", padx=20, pady=2)
        self.combo_tema = ctk.CTkComboBox(self.col_der_cat, values=["Ficción", "Fantasía", "Novela Histórica", "Tecnología y Código", "Ciencia Matemática", "Geografía e Historia", "Poesía", "Arte"], width=320)
        self.combo_tema.pack(pady=5)

        ctk.CTkLabel(self.col_der_cat, text="Idioma del Libro (Select):").pack(anchor="w", padx=20, pady=2)
        self.combo_idioma = ctk.CTkComboBox(self.col_der_cat, values=["Español", "Inglés", "Portugués", "Francés", "Italiano"], width=320)
        self.combo_idioma.pack(pady=5)

        ctk.CTkLabel(self.col_der_cat, text="Cota de Biblioteca (Personalizada):").pack(anchor="w", padx=20, pady=2)
        self.entry_cota_manual = ctk.CTkEntry(self.col_der_cat, width=320, placeholder_text="Vacío para Cutter-Sanborn Auto")
        self.entry_cota_manual.pack(pady=5)

        self.btn_catalogar = ctk.CTkButton(self.col_der_cat, text="Completar Catalogación y Guardar Ficha", fg_color="#00A65A", hover_color="#008D4C", command=self.guardar_catalogacion_libro)
        self.btn_catalogar.pack(pady=25, padx=20, fill="x")

    def cargar_libro_para_catalogar(self, evento):
        seleccion = self.tree_recibidos.selection()
        if not seleccion:
            return
        item = self.tree_recibidos.item(seleccion[0])
        valores = item['values']
        self.cat_id_ejemplar.set(f"Procesando Ejemplar: {valores[0]}")
        self.cat_isbn.set(valores[3])

    def guardar_catalogacion_libro(self):
        id_ej = self.cat_id_ejemplar.get()
        if "Procesando" not in id_ej:
            messagebox.showwarning("Aviso", "Seleccione un libro recibido de la lista izquierda primero.")
            return
        id_ejemplar = id_ej.split(": ")[1]
        isbn = self.cat_isbn.get()

        dewey_completo = self.combo_dewey.get()
        dewey_codigo = dewey_completo.split(" - ")[0] if dewey_completo else "000"
        dewey_nombre = dewey_completo.split(" - ")[1] if dewey_completo else "Generalidades"

        exito, msg = self.controller.procesar_catalogacion(
            isbn, id_ejemplar, dewey_codigo, dewey_nombre,
            self.combo_sala.get(), self.combo_estante.get(),
            self.combo_edicion.get(), self.combo_tema.get(),
            self.entry_cota_manual.get(), self.combo_idioma.get()
        )

        if exito:
            messagebox.showinfo("Felicidades", msg)
            self.vista_inventario_central()
        else:
            messagebox.showerror("Error", msg)

    # ========================== VISTA: EXISTENCIAS Y CONTEOS (REAL STOCK TRACKING) ==========================
    def vista_inventario_central(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Existencias y Conteos de Stock", "Monitoreo real de copias distribuidas y saldos locales")

        tabs_inv = ctk.CTkTabview(self.content_frame)
        tabs_inv.pack(fill="both", expand=True, padx=5, pady=5)

        tab_matriz = tabs_inv.add("Matriz de Stock (Conteo de Ejemplares)")
        tab_detallado = tabs_inv.add("Ejemplares Físicos Detallados")

        # --- SUB-TAB: MATRIZ DE STOCK ---
        card_box_m = ctk.CTkFrame(tab_matriz, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        card_box_m.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(card_box_m, text="MATRIZ DE DISPONIBILIDAD Y CONTEO AUTOMÁTICO DE STOCK", font=("Helvetica", 12, "bold"), text_color="#1F6AA5").pack(pady=10)

        style_m = ttk.Style()
        style_m.configure("Matriz.Treeview", font=("Helvetica", 10), rowheight=25)

        self.tree_matriz = ttk.Treeview(card_box_m, columns=("ISBN", "Título", "Autor", "Stock Central", "Sede Norte", "Sede Sur", "En Tránsito", "Total General"), show="headings", style="Matriz.Treeview")
        for col in ("ISBN", "Título", "Autor", "Stock Central", "Sede Norte", "Sede Sur", "En Tránsito", "Total General"):
            self.tree_matriz.heading(col, text=col)
            self.tree_matriz.column(col, width=120)
        self.tree_matriz.pack(fill="both", expand=True, padx=15, pady=15)

        self.recargar_matriz_stock()

        # --- SUB-TAB: DETALLADO ---
        card_box = ctk.CTkFrame(tab_detallado, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        card_box.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

        tree_frame = ctk.CTkFrame(card_box, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=15)

        columnas = ("ID Ejemplar", "Título", "Autor", "Cota", "ISBN", "Estado", "Sala", "Estante", "Biblioteca Sede")
        self.tree_central = ttk.Treeview(tree_frame, columns=columnas, show="headings", selectmode="browse")
        for col in columnas:
            self.tree_central.heading(col, text=col)
            self.tree_central.column(col, width=110)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_central.yview)
        self.tree_central.configure(yscrollcommand=scroll.set)
        self.tree_central.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.ejemplares_cache = self.controller.obtener_inventario_completo()
        for ej in self.ejemplares_cache:
            self.tree_central.insert("", "end", values=(ej[0], ej[1], ej[2], ej[8].replace("\n", " / "), ej[3], ej[4], ej[5], ej[6], ej[7]))

        acc_bar = ctk.CTkFrame(card_box, fg_color="transparent")
        acc_bar.pack(fill="x", padx=15, pady=10)

        btn_edit = ctk.CTkButton(acc_bar, text="Modificar / Editar Registro", fg_color="#F39C12", hover_color="#E08E0B", command=self.abrir_editor_ejemplar)
        btn_edit.pack(side="left", padx=5)

        btn_baja = ctk.CTkButton(acc_bar, text="Dar de Baja Ejemplar", fg_color="#DD4B39", hover_color="#D73925", command=self.baja_ejemplar_central)
        btn_baja.pack(side="left", padx=5)

    def recargar_matriz_stock(self):
        for item in self.tree_matriz.get_children():
            self.tree_matriz.delete(item)
        datos = self.controller.obtener_conteo_existencias()
        for d in datos:
            self.tree_matriz.insert("", "end", values=d)

    def abrir_editor_ejemplar(self):
        seleccion = self.tree_central.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor seleccione un ejemplar de la lista.")
            return

        item = self.tree_central.item(seleccion[0])
        ej_id = item['values'][0]

        ej_datos = None
        for ej in self.ejemplares_cache:
            if ej[0] == ej_id:
                ej_datos = ej
                break

        if not ej_datos:
            return

        self.modal_edit = ctk.CTkToplevel(self)
        self.modal_edit.title(f"Modificar Registro: {ej_id}")
        self.modal_edit.geometry("450x680")
        self.modal_edit.grab_set()

        scroll_frame = ctk.CTkScrollableFrame(self.modal_edit)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(scroll_frame, text="EDITAR REGISTRO GENERAL Y UBICACIÓN", font=("Helvetica", 12, "bold")).pack(pady=10)

        campos_modificar = [
            ("ISBN (Fijo)", ej_datos[3], False),
            ("Título", ej_datos[1], True),
            ("Autor", ej_datos[2], True),
            ("Editorial", ej_datos[11], True),
            ("Año", str(ej_datos[12]), True),
            ("Edición", ej_datos[13], True),
            ("Dewey Código", ej_datos[9], True),
            ("Tema / Género", ej_datos[10], True),
            ("Cota / Clasificación", ej_datos[8], True),
            ("Idioma", ej_datos[14], True),
            ("Origen / Entrada", ej_datos[15], True),
            ("Sala de Estancia", ej_datos[5], True),
            ("Estante", ej_datos[6], True)
        ]

        self.edit_entries = {}
        for label, val, editable in campos_modificar:
            ctk.CTkLabel(scroll_frame, text=label, font=("Helvetica", 10, "bold")).pack(anchor="w", padx=10, pady=2)
            entry = ctk.CTkEntry(scroll_frame, width=320)
            entry.insert(0, val if val else "")
            if not editable:
                entry.configure(state="disabled")
            entry.pack(padx=10, pady=4)
            self.edit_entries[label] = entry

        ctk.CTkLabel(scroll_frame, text="Estado").pack(anchor="w", padx=10, pady=2)
        combo_estado = ctk.CTkComboBox(scroll_frame, values=["recibido", "catalogado", "en stock", "en tránsito", "distribuido", "dado de baja"], width=320)
        combo_estado.set(ej_datos[4])
        combo_estado.pack(padx=10, pady=4)

        ctk.CTkLabel(scroll_frame, text="Sede Actual").pack(anchor="w", padx=10, pady=2)
        sedes = self.controller.listar_bibliotecas()
        sedes_nombres = [f"{s[0]} - {s[1]}" for s in sedes]
        combo_sede = ctk.CTkComboBox(scroll_frame, values=sedes_nombres, width=320)
        combo_sede.set(f"{ej_datos[16]} - {ej_datos[7]}")
        combo_sede.pack(padx=10, pady=4)

        btn_guardar = ctk.CTkButton(scroll_frame, text="Guardar Cambios", fg_color="#00A65A", command=lambda: self.guardar_modificacion_ejemplar(ej_datos, combo_estado, combo_sede))
        btn_guardar.pack(pady=20)

    def guardar_modificacion_ejemplar(self, ej_datos, combo_estado, combo_sede):
        isbn = ej_datos[3]
        id_unico = ej_datos[0]
        
        titulo = self.edit_entries["Título"].get()
        autor = self.edit_entries["Autor"].get()
        editorial = self.edit_entries["Editorial"].get()
        anio = self.edit_entries["Año"].get()
        edicion = self.edit_entries["Edición"].get()
        dewey = self.edit_entries["Dewey Código"].get()
        tema = self.edit_entries["Tema / Género"].get()
        clasificacion = self.edit_entries["Cota / Clasificación"].get()
        idioma = self.edit_entries["Idioma"].get()
        origen = self.edit_entries["Origen / Entrada"].get()
        sala = self.edit_entries["Sala de Estancia"].get()
        estante = self.edit_entries["Estante"].get()
        
        estado = combo_estado.get()
        sede_sel = combo_sede.get()
        sede_id = int(sede_sel.split(" - ")[0])

        exito, msg = self.controller.actualizar_libro_y_ejemplar(
            isbn, titulo, autor, editorial, anio, edicion, tema, dewey, clasificacion, idioma, origen,
            id_unico, estado, sala, estante, sede_id
        )
        if exito:
            messagebox.showinfo("Modificado", msg)
            self.modal_edit.destroy()
            self.vista_inventario_central()
        else:
            messagebox.showerror("Error", msg)

    def baja_ejemplar_central(self):
        seleccion = self.tree_central.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Seleccione un ejemplar primero.")
            return
        item = self.tree_central.item(seleccion[0])
        ej_id = item['values'][0]

        dialogo = ctk.CTkInputDialog(text="Ingrese el motivo de la baja:", title="Dar de baja")
        motivo = dialogo.get_input()

        if motivo:
            exito, msg = self.controller.dar_de_baja_ejemplar(ej_id, motivo)
            if exito:
                messagebox.showinfo("Correcto", msg)
                self.vista_inventario_central()
            else:
                messagebox.showerror("Error", msg)

    # ========================== VISTA: DISTRIBUCIÓN ==========================
    def vista_distribucion(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Distribución por Lote", "Envío de ejemplares a sedes dependientes")

        paneles = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        paneles.pack(fill="both", expand=True)

        col_izq = ctk.CTkFrame(paneles, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_izq.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(col_izq, text="1. Seleccione los Ejemplares Libres (Soporta Selección Múltiple)", font=("Helvetica", 11, "bold")).pack(pady=10)

        columnas = ("ID Ejemplar", "Título", "Cota", "Sala / Estante")
        self.tree_dist_libros = ttk.Treeview(col_izq, columns=columnas, show="headings", selectmode="extended")
        for col in columnas:
            self.tree_dist_libros.heading(col, text=col)
            self.tree_dist_libros.column(col, width=110)

        self.tree_dist_libros.pack(fill="both", expand=True, padx=10, pady=10)

        datos = self.controller.obtener_inventario_completo()
        for ej in datos:
            if ej[16] == 1 and ej[4] == "en stock":
                self.tree_dist_libros.insert("", "end", values=(ej[0], ej[1], ej[8].replace("\n", " / "), f"{ej[5]} / {ej[6]}"))

        col_der = ctk.CTkFrame(paneles, width=320, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_der.pack(side="right", fill="y", padx=5, pady=5)

        ctk.CTkLabel(col_der, text="2. Configuración de Destino", font=("Helvetica", 11, "bold")).pack(pady=15)

        ctk.CTkLabel(col_der, text="Sede de Destino:").pack(anchor="w", padx=25)
        sedes = self.controller.listar_bibliotecas()
        sedes_nombres = [f"{s[0]} - {s[1]}" for s in sedes if s[3] == "Dependiente"]
        self.combo_sedes = ctk.CTkComboBox(col_der, values=sedes_nombres, width=260)
        self.combo_sedes.pack(pady=5)

        ctk.CTkLabel(col_der, text="Responsable de Envío:").pack(anchor="w", padx=25)
        self.entry_resp_dist = ctk.CTkEntry(col_der, width=260, placeholder_text="Nombre completo")
        self.entry_resp_dist.pack(pady=5)

        ctk.CTkLabel(col_der, text="Observaciones:").pack(anchor="w", padx=25)
        self.text_obs_dist = ctk.CTkEntry(col_der, width=260, placeholder_text="Notas de despacho")
        self.text_obs_dist.pack(pady=5)

        btn_enviar = ctk.CTkButton(col_der, text="Enviar Lote en Tránsito", fg_color="#00A65A", hover_color="#008D4C", command=self.procesar_envio_distribucion)
        btn_enviar.pack(pady=35, padx=25, fill="x")

    def procesar_envio_distribucion(self):
        selecciones = self.tree_dist_libros.selection()
        if not selecciones:
            messagebox.showwarning("Aviso", "Seleccione al menos un ejemplar de la lista izquierda.")
            return
        ejemplares_ids = [self.tree_dist_libros.item(sel)['values'][0] for sel in selecciones]

        sede_sel = self.combo_sedes.get()
        if not Sede_sel:
            messagebox.showwarning("Aviso", "Seleccione una Sede dependiente destino.")
            return
        destino_id = int(sede_sel.split(" - ")[0])

        responsable = self.entry_resp_dist.get()
        observaciones = self.text_obs_dist.get()

        if not responsable:
            messagebox.showwarning("Aviso", "Escriba el nombre del responsable.")
            return

        exito, msg = self.controller.enviar_distribucion(destino_id, ejemplares_ids, responsable, observaciones)
        if exito:
            messagebox.showinfo("Éxito", msg)
            self.vista_distribucion()
        else:
            messagebox.showerror("Error", msg)

    # ========================== VISTA: GESTIÓN DE SEDES ==========================
    def vista_sedes(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Gestión de Sedes", "Registro y control de bibliotecas de la red")

        paneles = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        paneles.pack(fill="both", expand=True)

        col_izq = ctk.CTkFrame(paneles, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_izq.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        columnas = ("ID", "Nombre de Biblioteca Sede", "Dirección", "Tipo de Sede", "Encargado(a)", "Contacto")
        self.tree_sedes_gest = ttk.Treeview(col_izq, columns=columnas, show="headings", selectmode="browse")
        for col in columnas:
            self.tree_sedes_gest.heading(col, text=col)
            self.tree_sedes_gest.column(col, width=120)

        self.tree_sedes_gest.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_sedes_gest.bind("<<TreeviewSelect>>", self.cargar_sede_para_editar)

        self.recargar_tabla_sedes()

        col_der = ctk.CTkScrollableFrame(paneles, width=320, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_der.pack(side="right", fill="both", padx=5, pady=5)

        ctk.CTkLabel(col_der, text="Formulario de Biblioteca Sede", font=("Helvetica", 11, "bold")).pack(pady=15)

        self.lbl_id_sede = ctk.CTkLabel(col_der, text="ID de Sede: Nuevo Registro", text_color="#777777")
        self.lbl_id_sede.pack(pady=5)

        ctk.CTkLabel(col_der, text="Nombre Sede:").pack(anchor="w", padx=25)
        self.entry_nom_sede = ctk.CTkEntry(col_der, width=240)
        self.entry_nom_sede.pack(pady=5)

        ctk.CTkLabel(col_der, text="Dirección Física:").pack(anchor="w", padx=25)
        self.entry_dir_sede = ctk.CTkEntry(col_der, width=240)
        self.entry_dir_sede.pack(pady=5)

        ctk.CTkLabel(col_der, text="Tipo Sede:").pack(anchor="w", padx=25)
        self.combo_tipo_sede = ctk.CTkComboBox(col_der, values=["Central", "Dependiente"], width=240)
        self.combo_tipo_sede.pack(pady=5)

        # Campos de Encargado
        ctk.CTkLabel(col_der, text="Nombre del Encargado(a):").pack(anchor="w", padx=25)
        self.entry_encargado_sede = ctk.CTkEntry(col_der, width=240, placeholder_text="Responsable")
        self.entry_encargado_sede.pack(pady=5)

        ctk.CTkLabel(col_der, text="Contacto del Encargado(a):").pack(anchor="w", padx=25)
        self.entry_contacto_sede = ctk.CTkEntry(col_der, width=240, placeholder_text="Teléfono / Email")
        self.entry_contacto_sede.pack(pady=5)

        self.btn_guardar_sede = ctk.CTkButton(col_der, text="Registrar Nueva Sede", fg_color="#3C8DBC", hover_color="#367FA9", command=self.guardar_sede_modulo)
        self.btn_guardar_sede.pack(pady=15, padx=25, fill="x")

        self.btn_limpiar_sede_form = ctk.CTkButton(col_der, text="Limpiar Formulario", fg_color="#F39C12", hover_color="#E08E0B", command=self.limpiar_formulario_sede)
        self.btn_limpiar_sede_form.pack(pady=5, padx=25, fill="x")

    def recargar_tabla_sedes(self):
        for item in self.tree_sedes_gest.get_children():
            self.tree_sedes_gest.delete(item)
        sedes = self.controller.listar_bibliotecas()
        for s in sedes:
            self.tree_sedes_gest.insert("", "end", values=s)

    def cargar_sede_para_editar(self, evento):
        seleccion = self.tree_sedes_gest.selection()
        if not seleccion:
            return
        item = self.tree_sedes_gest.item(seleccion[0])
        valores = item['values']

        self.lbl_id_sede.configure(text=f"ID de Sede: {valores[0]}")
        self.entry_nom_sede.delete(0, tk.END)
        self.entry_nom_sede.insert(0, valores[1])
        self.entry_dir_sede.delete(0, tk.END)
        self.entry_dir_sede.insert(0, valores[2] if valores[2] else "")
        self.combo_tipo_sede.set(valores[3])
        self.entry_encargado_sede.delete(0, tk.END)
        self.entry_encargado_sede.insert(0, valores[4] if valores[4] else "")
        self.entry_contacto_sede.delete(0, tk.END)
        self.entry_contacto_sede.insert(0, valores[5] if valores[5] else "")

        self.btn_guardar_sede.configure(text="Guardar Cambios de Sede", fg_color="#00A65A", hover_color="#008D4C")

    def limpiar_formulario_sede(self):
        self.lbl_id_sede.configure(text="ID de Sede: Nuevo Registro")
        self.entry_nom_sede.delete(0, tk.END)
        self.entry_dir_sede.delete(0, tk.END)
        self.combo_tipo_sede.set("Dependiente")
        self.entry_encargado_sede.delete(0, tk.END)
        self.entry_contacto_sede.delete(0, tk.END)
        self.btn_guardar_sede.configure(text="Registrar Nueva Sede", fg_color="#3C8DBC", hover_color="#367FA9")
        self.tree_sedes_gest.selection_remove(self.tree_sedes_gest.selection())

    def guardar_sede_modulo(self):
        nom = self.entry_nom_sede.get()
        dire = self.entry_dir_sede.get()
        tipo = self.combo_tipo_sede.get()
        enc = self.entry_encargado_sede.get()
        cont = self.entry_contacto_sede.get()
        id_texto = self.lbl_id_sede.cget("text")

        if "Nuevo Registro" in id_texto:
            exito, msg = self.controller.registrar_sede(nom, dire, tipo, enc, cont)
        else:
            id_sede = int(id_texto.split(": ")[1])
            exito, msg = self.controller.actualizar_sede(id_sede, nom, dire, tipo, enc, cont)

        if exito:
            messagebox.showinfo("Éxito", msg)
            self.recargar_tabla_sedes()
            self.limpiar_formulario_sede()
        else:
            messagebox.showerror("Error", msg)

    # ========================== VISTA: IMPRESIÓN COTAS (MEDIDAS PERSONALIZABLES Y PDF NATIVO) ==========================
    def vista_etiquetas(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Diseñador de Etiquetas", "Ajuste milimétrico de tamaño en cm y exportación a PDF directo")

        paneles = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        paneles.pack(fill="both", expand=True)

        col_izq = ctk.CTkFrame(paneles, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_izq.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(col_izq, text="Seleccione los Ejemplares para Hoja de Cotas (Multi-Selección)", font=("Helvetica", 11, "bold")).pack(pady=10)

        columnas = ("ID Ejemplar", "Título del Libro", "Cota de Biblioteca")
        self.tree_etiq_libros = ttk.Treeview(col_izq, columns=columnas, show="headings", selectmode="extended")
        for col in columnas:
            self.tree_etiq_libros.heading(col, text=col)
            self.tree_etiq_libros.column(col, width=130)

        self.tree_etiq_libros.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_etiq_libros.bind("<<TreeviewSelect>>", lambda e: self.actualizar_plantilla_cotas_completa())

        datos = self.controller.obtener_inventario_completo()
        for ej in datos:
            if ej[8] and ej[8] != "":
                self.tree_etiq_libros.insert("", "end", values=(ej[0], ej[1], ej[8].replace("\n", " / ")))

        # Columna Derecha con Controles de Centímetros y Alineación
        col_der = ctk.CTkScrollableFrame(paneles, width=420, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_der.pack(side="right", fill="both", padx=5, pady=5)

        ctk.CTkLabel(col_der, text="PARÁMETROS FÍSICOS DE ROTULACIÓN", font=("Helvetica", 11, "bold"), text_color="#1F6AA5").pack(pady=10)

        # Inputs de Medidas en cm
        ctk.CTkLabel(col_der, text="Ancho de la Cota (cm):").pack(anchor="w", padx=20)
        self.entry_width_cm = ctk.CTkEntry(col_der, width=280)
        self.entry_width_cm.insert(0, "3.5")
        self.entry_width_cm.pack(pady=5)
        self.entry_width_cm.bind("<KeyRelease>", lambda e: self.actualizar_plantilla_cotas_completa())

        ctk.CTkLabel(col_der, text="Alto de la Cota (cm):").pack(anchor="w", padx=20)
        self.entry_height_cm = ctk.CTkEntry(col_der, width=280)
        self.entry_height_cm.insert(0, "5.0")
        self.entry_height_cm.pack(pady=5)
        self.entry_height_cm.bind("<KeyRelease>", lambda e: self.actualizar_plantilla_cotas_completa())

        # Control de Alineación
        ctk.CTkLabel(col_der, text="Alineación del Texto estándar (Select):").pack(anchor="w", padx=20)
        self.combo_align = ctk.CTkComboBox(col_der, values=["Centro", "Izquierda", "Derecha"], width=280, command=lambda e: self.actualizar_plantilla_cotas_completa())
        self.combo_align.set("Centro")
        self.combo_align.pack(pady=5)

        ctk.CTkLabel(col_der, text="VISTA PREVIA REJILLA IMPRESIÓN (Hoja A4)", font=("Helvetica", 11, "bold")).pack(pady=15)

        canvas_container = ctk.CTkFrame(col_der, fg_color="white", height=300)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas_etiq_sheet = tk.Canvas(canvas_container, bg="white", highlightthickness=1, highlightbackground="#D2D6DE", height=280)
        scroll_c = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas_etiq_sheet.yview)
        
        self.canvas_etiq_sheet.configure(yscrollcommand=scroll_c.set)
        self.canvas_etiq_sheet.pack(side="left", fill="both", expand=True)
        scroll_c.pack(side="right", fill="y")

        self.canvas_etiq_sheet.bind("<Configure>", lambda e: self.canvas_etiq_sheet.configure(scrollregion=self.canvas_etiq_sheet.bbox("all")))

        btn_imprimir = ctk.CTkButton(col_der, text="Generar y Exportar PDF Físico Milimétrico", fg_color="#00A65A", hover_color="#008D4C", command=self.imprimir_cotas_pdf_real)
        btn_imprimir.pack(pady=15, padx=20, fill="x")

        self.actualizar_plantilla_cotas_completa()

    def obtener_medidas_seguras(self):
        try:
            w = float(self.entry_width_cm.get())
            h = float(self.entry_height_cm.get())
            return w, h
        except ValueError:
            return 3.5, 5.0

    def actualizar_plantilla_cotas_completa(self):
        self.canvas_etiq_sheet.delete("all")

        selecciones = self.tree_etiq_libros.selection()
        if not selecciones:
            self.canvas_etiq_sheet.create_text(180, 140, text="Seleccione libros de la lista\npara simular el aprovechamiento\nde la hoja blanca A4.", justify="center", font=("Helvetica", 10, "italic"), fill="gray")
            return

        w_cm, h_cm = self.obtener_medidas_seguras()
        lbl_w_px = int(w_cm * 32) # Escala para previsualizar cómodo en el contenedor
        lbl_h_px = int(h_cm * 32)
        
        margin_x = 15
        margin_y = 15
        cols = 3
        align_opt = self.combo_align.get()

        for idx, sel in enumerate(selecciones):
            item = self.tree_etiq_libros.item(sel)
            ej_id = item['values'][0]
            titulo = item['values'][1]
            # Obtener del inventario completo con salto de línea real
            cota_multiline = ""
            for ej in self.ejemplares_cache:
                if ej[0] == ej_id:
                    cota_multiline = ej[8]
                    break

            if not cota_multiline:
                cota_multiline = "000\nAUT\n2026"

            row_idx = idx // cols
            col_idx = idx % cols

            x1 = margin_x + (col_idx * (lbl_w_px + 8))
            y1 = margin_y + (row_idx * (lbl_h_px + 8))
            x2 = x1 + lbl_w_px
            y2 = y1 + lbl_h_px

            self.canvas_etiq_sheet.create_rectangle(x1, y1, x2, y2, outline="#333", width=1, dash=(3, 2))

            # Dibujar textos respetando la alineación elegida
            anchor_tk = tk.CENTER
            text_x = x1 + (lbl_w_px / 2)
            if align_opt == "Izquierda":
                anchor_tk = tk.W
                text_x = x1 + 10
            elif align_opt == "Derecha":
                anchor_tk = tk.E
                text_x = x2 - 10

            lines = cota_multiline.split("\n")
            line_height_step = 14 if lbl_h_px > 100 else 10
            
            # Dibujar cada línea de la cota
            y_offset = y1 + 15
            for line in lines:
                self.canvas_etiq_sheet.create_text(text_x, y_offset, text=line, font=("Courier New", 10, "bold"), fill="black", anchor=anchor_tk)
                y_offset += line_height_step

            # ID de barra e información resumida al fondo
            if lbl_h_px > 90:
                self.canvas_etiq_sheet.create_text(x1 + (lbl_w_px / 2), y2 - 25, text=ej_id, font=("Courier New", 7, "bold"), fill="blue")
                titulo_recortado = titulo[:12] + ".." if len(titulo) > 12 else titulo
                self.canvas_etiq_sheet.create_text(x1 + (lbl_w_px / 2), y2 - 10, text=titulo_recortado.upper(), font=("Helvetica", 6), fill="gray")

        self.canvas_etiq_sheet.configure(scrollregion=(0, 0, 360, margin_y + ((len(selecciones)//cols + 1) * (lbl_h_px + 12))))

    def imprimir_cotas_pdf_real(self):
        """Genera un PDF exacto para impresión en A4 con ReportLab usando las medidas físicas ingresadas."""
        selecciones = self.tree_etiq_libros.selection()
        if not selecciones:
            messagebox.showwarning("Aviso", "Seleccione al menos una cota para exportar en PDF.")
            return

        # Intentar importar reportlab dinámicamente para proteger contra ausencia de la librería
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm as r_cm
        except ImportError:
            messagebox.showerror("Librería faltante", "Por favor ejecute en su terminal Canaima:\npip install reportlab")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            title="Exportar Cotas de Lomo en PDF Profesional"
        )
        if not archivo:
            return

        w_cm, h_cm = self.obtener_medidas_seguras()
        align_opt = self.combo_align.get()

        # Medidas de la hoja A4 en cm
        a4_w, a4_h = A4
        c = pdf_canvas.Canvas(archivo, pagesize=A4)

        # Márgenes en puntos ReportLab
        margin_x = 1.5 * r_cm
        margin_y = 1.5 * r_cm
        spacing = 0.3 * r_cm

        # Dimensiones de cada etiqueta en puntos
        lbl_w = w_cm * r_cm
        lbl_h = h_cm * r_cm

        # Número de columnas disponibles en A4
        cols = int((a4_w - (2 * margin_x)) // (lbl_w + spacing))
        if cols < 1: cols = 1

        x = margin_x
        y = a4_h - margin_y - lbl_h

        for idx, sel in enumerate(selecciones):
            item = self.tree_etiq_libros.item(sel)
            ej_id = item['values'][0]
            titulo = item['values'][1]

            cota_multiline = ""
            for ej in self.ejemplares_cache:
                if ej[0] == ej_id:
                    cota_multiline = ej[8]
                    break

            if not cota_multiline:
                cota_multiline = "000\nAUT\n2026"

            # Dibujar recuadro punteado
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.setLineWidth(0.5)
            c.setStrokeDashArray([2, 1])
            c.rect(x, y, lbl_w, lbl_h)

            # Dibujar líneas de texto
            lines = cota_multiline.split("\n")
            c.setFont("Courier-Bold", 10)
            
            y_text = y + lbl_h - (0.6 * r_cm)
            for line in lines:
                if align_opt == "Centro":
                    c.drawCentredString(x + (lbl_w / 2), y_text, line)
                elif align_opt == "Izquierda":
                    c.drawString(x + (0.2 * r_cm), y_text, line)
                else:
                    c.drawRightString(x + lbl_w - (0.2 * r_cm), y_text, line)
                y_text -= 12

            # Barra/ID de Ejemplar abajo
            c.setFont("Courier", 7)
            c.drawCentredString(x + (lbl_w / 2), y + 15, ej_id)
            c.setFont("Helvetica", 6)
            c.drawCentredString(x + (lbl_w / 2), y + 6, titulo[:16].upper())

            # Avanzar coordenadas
            col_idx = (idx + 1) % cols
            if col_idx == 0:
                x = margin_x
                y -= (lbl_h + spacing)
                # Nueva página si desborda
                if y < margin_y:
                    c.showPage()
                    y = a4_h - margin_y - lbl_h
            else:
                x += (lbl_w + spacing)

        c.save()
        messagebox.showinfo("Exportación Exitosa", f"Archivo PDF creado milimétricamente:\n{archivo}")

    # ========================== VISTA: REPORTES Y FICHAS ==========================
    def vista_reportes(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Reportes, Fichas y Distribuciones", "Consultar fichas y actas de despacho")

        tabs = ctk.CTkTabview(self.content_frame)
        tabs.pack(fill="both", expand=True, padx=5, pady=5)

        tab_fichas = tabs.add("Fichas Bibliográficas")
        tab_distribuciones = tabs.add("Historial de Distribuciones")

        # --- SUB-TAB FICHAS ---
        paneles_f = ctk.CTkFrame(tab_fichas, fg_color="transparent")
        paneles_f.pack(fill="both", expand=True)

        col_izq_f = ctk.CTkFrame(paneles_f, fg_color="white", border_width=1, border_color="#D2D6DE")
        col_izq_f.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(col_izq_f, text="Libros Catalogados en el Inventario Central", font=("Helvetica", 11, "bold")).pack(pady=10)

        columnas_f = ("ID Ejemplar", "Título", "Cota", "Estado")
        self.tree_fichas = ttk.Treeview(col_izq_f, columns=columnas_f, show="headings", selectmode="browse")
        for col in columnas_f:
            self.tree_fichas.heading(col, text=col)
            self.tree_fichas.column(col, width=120)
        self.tree_fichas.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_fichas.bind("<<TreeviewSelect>>", self.visualizar_ficha_bibliografica_completa)

        self.fichas_cache = self.controller.obtener_inventario_completo()
        for ej in self.fichas_cache:
            if ej[4] in ["en stock", "catalogado"]:
                self.tree_fichas.insert("", "end", values=(ej[0], ej[1], ej[8].replace("\n", " / "), ej[4]))

        self.col_der_ficha = ctk.CTkFrame(paneles_f, width=420, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        self.col_der_ficha.pack(side="right", fill="both", padx=5, pady=5)

        ctk.CTkLabel(self.col_der_ficha, text="FICHA BIBLIOGRÁFICA OFICIAL", font=("Helvetica", 12, "bold"), text_color="#222D32").pack(pady=15)

        self.canvas_ficha = tk.Canvas(self.col_der_ficha, bg="#FAF8F5", highlightthickness=1, highlightbackground="#D2D6DE", width=340, height=340)
        self.canvas_ficha.pack(pady=10, padx=20)
        self.canvas_ficha.create_text(170, 170, text="Seleccione un libro catalogado", justify="center", font=("Helvetica", 10, "italic"))

        btn_imp_ficha = ctk.CTkButton(self.col_der_ficha, text="Imprimir / Exportar Ficha Bibliográfica", fg_color="#3C8DBC", hover_color="#367FA9", command=self.imprimir_ficha_bibliografica_html)
        btn_imp_ficha.pack(pady=10, padx=20, fill="x")

        # --- SUB-TAB DISTRIBUCIONES ---
        paneles_d = ctk.CTkFrame(tab_distribuciones, fg_color="transparent")
        paneles_d.pack(fill="both", expand=True)

        col_izq_d = ctk.CTkFrame(paneles_d, fg_color="white", border_width=1, border_color="#D2D6DE")
        col_izq_d.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(col_izq_d, text="Lotes de Distribución Enviados", font=("Helvetica", 11, "bold")).pack(pady=10)

        columnas_d = ("ID Lote", "Origen", "Destino", "Fecha de Envío", "Responsable", "Estado")
        self.tree_distribuciones_hist = ttk.Treeview(col_izq_d, columns=columnas_d, show="headings", selectmode="browse")
        for col in columnas_d:
            self.tree_distribuciones_hist.heading(col, text=col)
            self.tree_distribuciones_hist.column(col, width=110)
        self.tree_distribuciones_hist.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_distribuciones_hist.bind("<<TreeviewSelect>>", self.cargar_detalles_distribucion_seleccionada)

        self.recargar_tabla_distribuciones_hist()

        self.col_der_dist = ctk.CTkFrame(paneles_d, width=420, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        self.col_der_dist.pack(side="right", fill="both", padx=5, pady=5)

        ctk.CTkLabel(self.col_der_dist, text="ACTA DETALLADA DE DISTRIBUCIÓN", font=("Helvetica", 12, "bold"), text_color="#222D32").pack(pady=15)

        self.txt_acta_detalles = tk.Text(self.col_der_dist, bg="#FAF8F5", font=("Courier New", 10), borderwidth=1, relief="solid")
        self.txt_acta_detalles.pack(fill="both", expand=True, padx=20, pady=5)

        btn_imp_acta = ctk.CTkButton(self.col_der_dist, text="Imprimir / Exportar Acta de Entrega", fg_color="#00A65A", hover_color="#008D4C", command=self.imprimir_acta_distribucion_txt)
        btn_imp_acta.pack(pady=15, padx=20, fill="x")

    def recargar_tabla_distribuciones_hist(self):
        for item in self.tree_distribuciones_hist.get_children():
            self.tree_distribuciones_hist.delete(item)
        datos = self.controller.listar_distribuciones()
        for d in datos:
            self.tree_distribuciones_hist.insert("", "end", values=d)

    def visualizar_ficha_bibliografica_completa(self, evento):
        seleccion = self.tree_fichas.selection()
        if not seleccion:
            return
        item = self.tree_fichas.item(seleccion[0])
        ej_id = item['values'][0]

        ej_datos = None
        for ej in self.fichas_cache:
            if ej[0] == ej_id:
                ej_datos = ej
                break

        if not ej_datos:
            return

        self.canvas_ficha.delete("all")
        self.canvas_ficha.create_rectangle(10, 10, 330, 330, outline="#333", width=1)
        self.canvas_ficha.create_oval(162, 305, 178, 321, fill="white", outline="#333")

        cota_raw = ej_datos[8] or "000\nAUT\n2026"
        cota_lineas = cota_raw.split("\n")
        
        autor = ej_datos[2] or "Autor"
        titulo = ej_datos[1] or "Título"
        editorial = ej_datos[11] or "N/A"
        anio = str(ej_datos[12]) if ej_datos[12] else "2026"
        edicion = ej_datos[13] or "1ra Ed."
        idioma = ej_datos[14] or "Español"
        origen = ej_datos[15] or "Desconocido"
        sala = ej_datos[5] or "N/A"
        estante = ej_datos[6] or "N/A"
        isbn = ej_datos[3] or "N/A"

        # Escritura de renglones Cutter/Cota
        y_text = 40
        for lin in cota_lineas:
            self.canvas_ficha.create_text(30, y_text, text=lin, font=("Courier New", 11, "bold"), anchor="w", fill="red")
            y_text += 15

        self.canvas_ficha.create_text(110, 45, text=autor.upper(), font=("Helvetica", 11, "bold"), anchor="w", fill="black")
        
        texto_titulo_completo = f"{titulo}. -- {edicion}. -- {editorial}, {anio}."
        self.canvas_ficha.create_text(110, 85, text=texto_titulo_completo, font=("Helvetica", 10), anchor="w", width=200, justify="left")

        self.canvas_ficha.create_text(110, 145, text=f"ISBN: {isbn}", font=("Helvetica", 9), anchor="w")
        self.canvas_ficha.create_text(110, 165, text=f"Idioma: {idioma}", font=("Helvetica", 9), anchor="w")
        self.canvas_ficha.create_text(110, 185, text=f"Procedencia: {origen}", font=("Helvetica", 9), anchor="w")

        self.canvas_ficha.create_line(30, 215, 310, 215, fill="lightgray")
        self.canvas_ficha.create_text(30, 235, text="ALMACENADO EN CENTRAL:", font=("Helvetica", 8, "bold"), anchor="w", fill="gray")
        self.canvas_ficha.create_text(30, 255, text=f"Sala: {sala} | Estante: {estante}", font=("Helvetica", 9, "bold"), anchor="w")

    def imprimir_ficha_bibliografica_html(self):
        seleccion = self.tree_fichas.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione una ficha de la lista.")
            return
        
        item = self.tree_fichas.item(seleccion[0])
        ej_id = item['values'][0]

        ej_datos = None
        for ej in self.fichas_cache:
            if ej[0] == ej_id:
                ej_datos = ej
                break

        if not ej_datos:
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("Archivo Web", "*.html")],
            title="Exportar Ficha Bibliográfica"
        )
        if not archivo:
            return

        cota_html = ej_datos[8].replace("\n", "<br>")

        html_ficha = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ficha Bibliográfica - {ej_datos[1]}</title>
    <style>
        body {{ background: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Times New Roman', Times, serif; }}
        .ficha {{ 
            width: 12.5cm; 
            height: 7.5cm; 
            background: #fff; 
            border: 1px solid #999; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.15); 
            padding: 1.0cm;
            box-sizing: border-box;
            position: relative;
        }}
        .cota {{ font-family: monospace; font-size: 14px; font-weight: bold; color: red; position: absolute; left: 1cm; top: 1cm; line-height: 1.2; }}
        .cuerpo {{ margin-left: 3.2cm; font-size: 13px; line-height: 1.4; }}
        .autor {{ font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 5px; }}
        .titulo {{ margin-bottom: 10px; }}
        .detalles {{ font-size: 12px; color: #333; }}
        .agujero {{ 
            width: 0.5cm; 
            height: 0.5cm; 
            border: 1px solid #444; 
            border-radius: 50%; 
            position: absolute; 
            bottom: 0.3cm; 
            left: 50%; 
            transform: translateX(-50%);
            background: #fff;
        }}
    </style>
</head>
<body>
    <div class="ficha">
        <div class="cota">{cota_html}</div>
        <div class="cuerpo">
            <div class="autor">{ej_datos[2]}</div>
            <div class="titulo">{ej_datos[1]}. -- {ej_datos[13] or "1ra Ed."}. -- {ej_datos[11] or "N/A"}, {ej_datos[12]}.</div>
            <div class="detalles">
                ISBN: {ej_datos[3]}<br>
                Idioma: {ej_datos[14]} | Origen: {ej_datos[15]}<br>
                Ubicación Central: Sala {ej_datos[5]} - Estante {ej_datos[6]}
            </div>
        </div>
        <div class="agujero"></div>
    </div>
</body>
</html>"""

        with open(archivo, "w", encoding="utf-8") as f:
            f.write(html_ficha)
        messagebox.showinfo("Exportada", f"Ficha guardada en: {archivo}")

    def cargar_detalles_distribucion_seleccionada(self, evento):
        seleccion = self.tree_distribuciones_hist.selection()
        if not seleccion:
            return
        item = self.tree_distribuciones_hist.item(seleccion[0])
        dist_id = item['values'][0]
        
        detalles_lote = self.controller.obtener_detalles_distribucion(dist_id)

        acta_txt = f"========================================\n"
        acta_txt += f"      ACTA DE DESPACHO / DISTRIBUCIÓN\n"
        acta_txt += f"========================================\n"
        acta_txt += f"Lote ID: #{item['values'][0]}\n"
        acta_txt += f"Origen:  {item['values'][1]}\n"
        acta_txt += f"Destino: {item['values'][2]}\n"
        acta_txt += f"Fecha:   {item['values'][3]}\n"
        acta_txt += f"Resp.:   {item['values'][4]}\n"
        acta_txt += f"Estado:  {item['values'][5]}\n"
        acta_txt += f"----------------------------------------\n"
        acta_txt += f"EJEMPLARES INCLUIDOS EN EL ENVÍO:\n"
        acta_txt += f"----------------------------------------\n"
        for d in detalles_lote:
            acta_txt += f"* ID: {d[0]}\n  Libro: {d[1][:25]}\n  Cota: {d[3].replace('\\n', ' / ')}\n\n"
        
        self.txt_acta_detalles.delete("1.0", tk.END)
        self.txt_acta_detalles.insert(tk.END, acta_txt)

    def imprimir_acta_distribucion_txt(self):
        contenido = self.txt_acta_detalles.get("1.0", tk.END).strip()
        if not contenido or "EJEMPLARES INCLUIDOS" not in contenido:
            messagebox.showwarning("Aviso", "Seleccione un lote de distribución con detalles válidos.")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Documentos de Texto", "*.txt")],
            title="Exportar Acta de Distribución"
        )
        if not archivo:
            return

        with open(archivo, "w", encoding="utf-8") as f:
            f.write(contenido)
        messagebox.showinfo("Exportada", f"Acta oficial de entrega exportada en:\n{archivo}")

    # ========================== VISTA: ADMINISTRACIÓN (CON GESTIÓN DE USUARIOS) ==========================
    def vista_administracion(self):
        self.limpiar_contenido_activo()
        self.dibujar_cabecera_modulo("Consola de Administración", "Control global de seguridad, usuarios y backups")

        tabs = ctk.CTkTabview(self.content_frame)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        tab_usuarios = tabs.add("Gestión de Usuarios")
        tab_seg = tabs.add("Copias de Seguridad (Backup & Exportar)")
        tab_audit = tabs.add("Auditoría (Bitácora)")

        # --- TAB GESTIÓN DE USUARIOS ---
        paneles_u = ctk.CTkFrame(tab_usuarios, fg_color="transparent")
        paneles_u.pack(fill="both", expand=True)

        col_izq_u = ctk.CTkFrame(paneles_u, fg_color="white", border_width=1, border_color="#D2D6DE")
        col_izq_u.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        columnas_u = ("ID", "Nombre de Usuario", "Contraseña", "Rol", "Permisos")
        self.tree_usuarios_gest = ttk.Treeview(col_izq_u, columns=columnas_u, show="headings", selectmode="browse")
        for col in columnas_u:
            self.tree_usuarios_gest.heading(col, text=col)
            self.tree_usuarios_gest.column(col, width=100)
        self.tree_usuarios_gest.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_usuarios_gest.bind("<<TreeviewSelect>>", self.cargar_usuario_para_editar)

        self.recargar_tabla_usuarios()

        col_der_u = ctk.CTkFrame(paneles_u, width=320, fg_color="white", border_width=1, border_color="#D2D6DE", corner_radius=5)
        col_der_u.pack(side="right", fill="y", padx=5, pady=5)

        ctk.CTkLabel(col_der_u, text="Formulario de Usuario", font=("Helvetica", 11, "bold")).pack(pady=15)

        self.lbl_id_usuario = ctk.CTkLabel(col_der_u, text="ID de Usuario: Nuevo Registro", text_color="#777777")
        self.lbl_id_usuario.pack(pady=5)

        ctk.CTkLabel(col_der_u, text="Nombre de Usuario:").pack(anchor="w", padx=25)
        self.entry_nom_user = ctk.CTkEntry(col_der_u, width=240)
        self.entry_nom_user.pack(pady=5)

        ctk.CTkLabel(col_der_u, text="Contraseña de Acceso:").pack(anchor="w", padx=25)
        self.entry_pass_user = ctk.CTkEntry(col_der_u, width=240)
        self.entry_pass_user.pack(pady=5)

        ctk.CTkLabel(col_der_u, text="Rol del Usuario:").pack(anchor="w", padx=25)
        self.combo_rol_user = ctk.CTkComboBox(col_der_u, values=["Administrador", "Bibliotecario Central", "Bibliotecario Sede"], width=240)
        self.combo_rol_user.pack(pady=5)

        self.btn_guardar_user = ctk.CTkButton(col_der_u, text="Registrar Usuario", fg_color="#3C8DBC", hover_color="#367FA9", command=self.guardar_usuario_modulo)
        self.btn_guardar_user.pack(pady=15, padx=25, fill="x")

        self.btn_borrar_user = ctk.CTkButton(col_der_u, text="Eliminar Usuario Seleccionado", fg_color="#DD4B39", hover_color="#C23321", command=self.eliminar_usuario_modulo)
        self.btn_borrar_user.pack(pady=5, padx=25, fill="x")

        self.btn_limpiar_user_form = ctk.CTkButton(col_der_u, text="Limpiar Formulario", fg_color="#F39C12", hover_color="#E08E0B", command=self.limpiar_formulario_usuario)
        self.btn_limpiar_user_form.pack(pady=5, padx=25, fill="x")

        # --- TAB COPAS DE SEGURIDAD ---
        ctk.CTkLabel(tab_seg, text="GENERACIÓN MANUAL DE COPIAS DE SEGURIDAD", font=("Helvetica", 14, "bold"), text_color="#222D32").pack(pady=15)
        
        btn_respaldo = ctk.CTkButton(tab_seg, text="Generar Respaldo Local de Base de Datos (.db)", fg_color="#00C0EF", command=self.ejecutar_backup)
        btn_respaldo.pack(pady=10)

        ctk.CTkLabel(tab_seg, text="EXPORTACIÓN TOTAL DEL SISTEMA A HOJAS DE CÁLCULO (CSV)", font=("Helvetica", 14, "bold"), text_color="#222D32").pack(pady=35)
        btn_export_csv = ctk.CTkButton(tab_seg, text="Exportar todo el sistema a Hojas de Cálculo (CSV)", fg_color="#00A65A", hover_color="#008D4C", height=40, command=self.ejecutar_exportacion_csv_total)
        btn_export_csv.pack()

        # --- TAB AUDITORÍA ---
        tree_frame = ctk.CTkFrame(tab_audit, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columnas_bit = ("Fecha", "Usuario", "Acción", "Detalles")
        tree_aud = ttk.Treeview(tree_frame, columns=columnas_bit, show="headings")
        for col in columnas_bit:
            tree_aud.heading(col, text=col)
            tree_aud.column(col, width=120)
        tree_aud.pack(fill="both", expand=True)

        datos_logs = self.controller.obtener_auditoria()
        for log in datos_logs:
            tree_aud.insert("", "end", values=log)

    def recargar_tabla_usuarios(self):
        for item in self.tree_usuarios_gest.get_children():
            self.tree_usuarios_gest.delete(item)
        usuarios = self.controller.listar_usuarios()
        for u in usuarios:
            self.tree_usuarios_gest.insert("", "end", values=u)

    def cargar_usuario_para_editar(self, evento):
        seleccion = self.tree_usuarios_gest.selection()
        if not seleccion:
            return
        item = self.tree_usuarios_gest.item(seleccion[0])
        valores = item['values']

        self.lbl_id_usuario.configure(text=f"ID de Usuario: {valores[0]}")
        self.entry_nom_user.delete(0, tk.END)
        self.entry_nom_user.insert(0, valores[1])
        self.entry_pass_user.delete(0, tk.END)
        self.entry_pass_user.insert(0, valores[2])
        self.combo_rol_user.set(valores[3])

        self.btn_guardar_user.configure(text="Guardar Cambios de Usuario", fg_color="#00A65A", hover_color="#008D4C")

    def limpiar_formulario_usuario(self):
        self.lbl_id_usuario.configure(text="ID de Usuario: Nuevo Registro")
        self.entry_nom_user.delete(0, tk.END)
        self.entry_pass_user.delete(0, tk.END)
        self.combo_rol_user.set("Bibliotecario Sede")
        self.btn_guardar_user.configure(text="Registrar Usuario", fg_color="#3C8DBC", hover_color="#367FA9")
        self.tree_usuarios_gest.selection_remove(self.tree_usuarios_gest.selection())

    def guardar_usuario_modulo(self):
        user = self.entry_nom_user.get()
        passw = self.entry_pass_user.get()
        rol = self.combo_rol_user.get()
        perm = "todos" if rol == "Administrador" else "inventario"
        id_texto = self.lbl_id_usuario.cget("text")

        if "Nuevo Registro" in id_texto:
            exito, msg = self.controller.guardar_usuario(None, user, passw, rol, perm)
        else:
            id_u = int(id_texto.split(": ")[1])
            exito, msg = self.controller.guardar_usuario(id_u, user, passw, rol, perm)

        if exito:
            messagebox.showinfo("Éxito", msg)
            self.recargar_tabla_usuarios()
            self.limpiar_formulario_usuario()
        else:
            messagebox.showerror("Error", msg)

    def eliminar_usuario_modulo(self):
        seleccion = self.tree_usuarios_gest.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un usuario de la lista.")
            return
        item = self.tree_usuarios_gest.item(seleccion[0])
        id_u = item['values'][0]
        user = item['values'][1]

        if user == "admin":
            messagebox.showerror("Seguridad", "No se puede eliminar el usuario 'admin' maestro por motivos de seguridad.")
            return

        if messagebox.askyesno("Confirmar", f"¿Está seguro que desea eliminar al usuario '{user}' del sistema?"):
            exito, msg = self.controller.borrar_usuario(id_u, user)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.recargar_tabla_usuarios()
                self.limpiar_formulario_usuario()
            else:
                messagebox.showerror("Error", msg)

    def ejecutar_backup(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Base de Datos SQLite", "*.db")], title="Guardar Respaldo")
        if ruta:
            exito, msg = self.controller.realizar_copia_seguridad(ruta)
            if exito:
                messagebox.showinfo("Correcto", "Copia de seguridad local creada con éxito.")
            else:
                messagebox.showerror("Error", msg)

    def ejecutar_exportacion_csv_total(self):
        directorio = filedialog.askdirectory(title="Seleccionar Carpeta para Respaldar Tablas")
        if directorio:
            exito, msg = self.controller.exportar_todo_a_csv_excel(directorio)
            if exito:
                messagebox.showinfo("Exportado de Seguridad Exitoso", msg)
            else:
                messagebox.showerror("Error", msg)
