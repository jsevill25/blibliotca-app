from datetime import date

from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library, Location, Movement
from controllers.auth_controller import AuthController
from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
from controllers.fichero_controller import FicheroController
from controllers.recepcion_controller import RecepcionController
from controllers.reportes_controller import ReportesController
from controllers.ubicacion_controller import UbicacionController


def test_flujo_recepcion_catalogacion_distribucion_y_historial(tmp_path):
    database = DatabaseManager(tmp_path / "sistema.db")
    database.initialize()
    auth = AuthController(database)
    recibido = auth.autenticar("admin", "admin123")
    assert recibido[0] is True
    usuario = recibido[1]
    assert usuario.debe_cambiar_clave is True
    assert auth.cambiar_clave(usuario.id, "admin123", "ClaveNuevaSegura2026")[0] is True
    assert auth.autenticar("admin", "admin123")[0] is False
    assert auth.autenticar("admin", "ClaveNuevaSegura2026")[0] is True
    creado_usuario, mensaje = auth.crear_usuario("lectora", "Lectora de prueba", "ClaveInicial2026", "bibliotecario", usuario.id)
    assert creado_usuario is True, mensaje
    bibliotecario = auth.autenticar("lectora", "ClaveInicial2026")[1]
    assert auth.crear_usuario("intruso", "Sin permiso", "ClaveInicial2026", "admin", bibliotecario.id)[0] is False
    assert auth.listar_usuarios(bibliotecario.id) == []
    actualizado, mensaje = auth.actualizar_usuario(
        bibliotecario.id, "lectora2", "Nombre corregido", "bibliotecario", "", usuario.id,
    )
    assert actualizado is True, mensaje
    assert auth.autenticar("lectora", "ClaveInicial2026")[0] is False
    assert auth.autenticar("lectora2", "ClaveInicial2026")[0] is True
    assert auth.cambiar_estado_usuario(bibliotecario.id, False, usuario.id)[0] is True
    assert auth.autenticar("lectora2", "ClaveInicial2026")[0] is False
    assert auth.cambiar_estado_usuario(bibliotecario.id, True, usuario.id)[0] is True
    assert auth.autenticar("lectora2", "ClaveInicial2026")[0] is True
    assert auth.cambiar_estado_usuario(usuario.id, False, usuario.id)[0] is False

    recepcion = RecepcionController(database)
    creado, numero = recepcion.registrar({
        "titulo": "Historia de Venezuela", "autor": "Rómulo Gallegos", "editorial": "Central",
        "anio": "2020", "isbn": "978-0000000001", "procedencia": "donacion",
        "procedencia_detalle": "Donación escolar", "donante_nombre": "Biblioteca amiga",
        "numero_volumenes": "2", "precio_unitario": "125,50",
    }, usuario.id)
    assert creado is True
    libro = recepcion.listar(texto="978-0000000001")[0]
    assert libro.numero_registro == numero
    assert libro.estado == "recibido"
    assert libro.numero_volumenes == 2
    assert str(libro.precio_unitario) == "125.50"
    editado, mensaje = recepcion.editar(libro.id, {
        "titulo": libro.titulo, "autor": libro.autor, "editorial": libro.editorial,
        "isbn": libro.isbn, "edicion": libro.edicion, "idioma": libro.idioma,
        "anio": "2021", "paginas": "220", "procedencia": "compra",
        "procedencia_detalle": "Factura 15", "proveedor_nombre": "Librería Central",
        "observaciones": "Corregido", "numero_volumenes": "3", "precio_unitario": "200.00",
    }, usuario.id)
    assert editado is True, mensaje
    libro = recepcion.listar(texto="978-0000000001")[0]
    assert libro.recepcion.modificado is True
    assert libro.recepcion.modificado_por == usuario.id
    assert libro.recepcion.proveedor_nombre == "Librería Central"
    assert libro.numero_volumenes == 3
    assert str(libro.precio_unitario) == "200.00"
    assert recepcion.listar(procedencia="compra", inicio=date.today(), fin=date.today())[0].id == libro.id
    edicion_invalida, _ = recepcion.editar(libro.id, {
        "titulo": libro.titulo, "procedencia": "compra", "anio": str(date.today().year + 5),
        "paginas": "220",
    }, usuario.id)
    assert edicion_invalida is False
    libro = recepcion.listar(texto="978-0000000001")[0]
    assert libro.numero_volumenes == 3
    assert str(libro.precio_unitario) == "200.00"

    catalogacion = CatalogacionController(database)
    assert catalogacion.catalogar(libro.id, "Dewey", "863.6", "G216", "863.6\nG216\n2020", usuario.id)[0] is True
    assert catalogacion.catalogar(libro.id, "Dewey", "863.6", "G216", "otra cota", usuario.id)[0] is False
    with database.session() as session:
        persistido = session.get(Book, libro.id)
        ficha = session.query(Cataloging).filter_by(libro_id=libro.id).one()
        assert persistido.codigo_dewey == "863.6"
        assert ficha.clasificacion == "Dewey"
        assert ficha.codigo_clasificacion == "863.6"

    matriz_areas = ReportesController(database).resumen_distribucion_areas()
    central = next(
        fila for fila in matriz_areas["sucursales"]
        if fila["biblioteca"] == "Biblioteca Central 'Rómulo Gallegos'"
    )
    assert central["municipio"] == ""
    assert central["categorias"]["800"] == {"T": 1, "V": 3}
    assert central["categorias"]["Total"] == {"T": 1, "V": 3}
    assert central["categorias"]["Total General"] == {"T": 1, "V": 3}
    assert matriz_areas["totales_generales"]["800"] == {"T": 1, "V": 3}

    matriz_central = FicheroController(database).obtener_matriz_sucursales(libro.id)
    assert matriz_central is not None
    assert len(matriz_central["filas"]) == 26
    fila_central = next(fila for fila in matriz_central["filas"] if fila["biblioteca"] == "Rómulo Gallegos")
    assert fila_central["ingreso"] is True
    assert fila_central["disponibilidad"] is True

    with database.session() as session:
        sucursal = Library(
            nombre="Sucursal Norte", direccion="Calle 1",
            municipio="Angostura del Orinoco", encargado="Encargada Norte", activa=True,
        )
        session.add(sucursal)
        session.flush()
        sucursal_id = sucursal.id

    distribucion = DistribucionController(database)
    enviado, codigo = distribucion.crear_bulto(sucursal_id, [libro.id], usuario.id)
    assert enviado is True
    assert codigo.startswith("ENV-")
    datos_envio = distribucion.obtener_envio(codigo)
    assert datos_envio is not None
    bulto, libros_envio = datos_envio
    assert libros_envio[0]["numero_volumenes"] == 3
    assert str(libros_envio[0]["precio_unitario"]) == "200.00"
    assert libros_envio[0]["procedencia"] == "compra"
    assert bulto["direccion"] == "Calle 1"
    assert bulto["municipio"] == "Angostura del Orinoco"
    assert bulto["encargada"] == "Encargada Norte"
    assert bulto["cantidad_volumenes"] == 3
    assert distribucion.listar_envios()[0]["codigo_envio"] == codigo
    matriz_areas = ReportesController(database).resumen_distribucion_areas()
    sucursal_areas = next(
        fila for fila in matriz_areas["sucursales"]
        if fila["biblioteca"] == "Sucursal Norte"
    )
    assert sucursal_areas["municipio"] == "Angostura del Orinoco"
    assert sucursal_areas["categorias"]["800"] == {"T": 1, "V": 3}
    assert sucursal_areas["categorias"]["Total General"] == {"T": 1, "V": 3}
    matriz = FicheroController(database).obtener_matriz_sucursales(libro.id)
    assert matriz is not None
    assert len(matriz["filas"]) == 27
    fila_sucursal = next(fila for fila in matriz["filas"] if fila["biblioteca"] == "Sucursal Norte")
    assert fila_sucursal == {
        "biblioteca": "Sucursal Norte",
        "ingreso": True,
        "disponibilidad": True,
        "prestamo": False,
    }

    ubicacion = UbicacionController(database)
    resultado = ubicacion.buscar(texto=numero)
    assert resultado[0]["libro"].estado == "distribuido"
    assert resultado[0]["biblioteca"] == "Sucursal Norte"
    assert resultado[0]["ultimo_movimiento"].tipo_movimiento == "distribucion"
    ubicado, mensaje = ubicacion.actualizar_ubicacion(libro.id, sucursal_id, "sala", "Literatura", "E-12", usuario.id)
    assert ubicado is True, mensaje
    resultado_filtrado = ubicacion.buscar(texto=numero, tipo_ubicacion="sala", sala="Literatura", estante="E-12")
    assert resultado_filtrado[0]["biblioteca"] == "Sucursal Norte"
    assert resultado_filtrado[0]["ultimo_movimiento"].tipo_movimiento == "ubicacion"
    assert {movimiento.tipo_movimiento for movimiento in ubicacion.historial(libro.id)} == {
        "recepcion", "catalogacion", "distribucion", "ubicacion",
    }

    resumen = ReportesController(database).resumen(date.today(), date.today())
    assert resumen["total"] == 1
    assert resumen["estados"] == {"distribuido": 1}
    assert resumen["catalogacion"] == {"catalogados": 1, "pendientes": 0}
    assert resumen["distribucion"] == [("Sucursal Norte", 1)]
    assert any(fila[-1] == 1 and fila[2] == "Literatura" for fila in resumen["ubicaciones"])
    assert ReportesController(database).inventario()[0]["sala"] == "Literatura"
    with database.session() as session:
        session.get(Book, libro.id).estado = "prestado"
    matriz_prestamo = FicheroController(database).obtener_matriz_sucursales(libro.id)
    assert matriz_prestamo is not None
    fila_prestamo = next(fila for fila in matriz_prestamo["filas"] if fila["biblioteca"] == "Sucursal Norte")
    assert fila_prestamo["disponibilidad"] is False
    assert fila_prestamo["prestamo"] is True
    database.close()


def test_generacion_cota_automatica_aplica_reglas_y_numera_duplicados(tmp_path):
    database = DatabaseManager(tmp_path / "cotas.db")
    database.initialize()
    with database.session() as session:
        primero = Book(
            titulo="El mar azul", autor="Ana Pérez", anio=2024, paginas=32,
            procedencia="donacion", estado="recibido", numero_registro="REG-2026-10001",
        )
        segundo = Book(
            titulo="El mar azul", autor="Ana Pérez", anio=2024, paginas=32,
            procedencia="donacion", estado="recibido", numero_registro="REG-2026-10002",
        )
        session.add_all([primero, segundo])
        session.flush()
        primero_id, segundo_id = primero.id, segundo.id

    catalogacion = CatalogacionController(database)
    datos = {
        "genero": "Novela", "nacionalidad": "Venezolana", "seccion": "Referencia",
        "alto": "35", "ancho": "25",
    }
    cota_primera = catalogacion.generar_cota_automatica(primero_id, "863.123456", datos)
    lineas = cota_primera["cota"].splitlines()
    assert lineas[0] == "Foll."
    assert lineas[1] == "NV"
    assert lineas[2].startswith("P")
    assert lineas[3] == "2024"
    assert catalogacion.catalogar(
        primero_id, "Dewey", "863.123456", cota_primera["cutter"], cota_primera["cota"], None,
    )[0] is True

    cota_segunda = catalogacion.generar_cota_automatica(segundo_id, "863.123456", datos)
    assert cota_segunda["cota"].endswith("\nej.2")


def test_generacion_cota_no_ficcion_trunca_dewey_y_omite_articulos_en_titulo(tmp_path):
    database = DatabaseManager(tmp_path / "cota-titulo.db")
    database.initialize()
    with database.session() as session:
        libro = Book(
            titulo="Las rutas de la historia", autor="", anio=2025, paginas=100,
            procedencia="donacion", estado="recibido", numero_registro="REG-2026-10003",
        )
        libro_autores = Book(
            titulo="El mapa compartido", autor="Ana, A.; Bruno, B.; Carla, C.; Diego, D.",
            anio=2025, paginas=100, procedencia="donacion", estado="recibido",
            numero_registro="REG-2026-10004",
        )
        session.add(libro)
        session.add(libro_autores)
        session.flush()
        libro_id = libro.id
        libro_autores_id = libro_autores.id

    catalogacion = CatalogacionController(database)
    cota = catalogacion.generar_cota_automatica(libro_id, "987.0632199", {"genero": "No ficción"})
    assert cota["cota"].splitlines() == ["987.06321", cota["cutter"], "2025"]
    assert cota["cutter"].startswith("R")
    cota_autores = catalogacion.generar_cota_automatica(
        libro_autores_id, "900", {"genero": "No ficción", "numero_autores": "4"},
    )
    assert cota_autores["cutter"].startswith("M")


def test_fichero_busca_cedulas_y_resume_existencias_por_area_y_sistema(tmp_path):
    database = DatabaseManager(tmp_path / "fichero.db")
    database.initialize()
    with database.session() as session:
        for indice in range(1, 5):
            libro = Book(
                titulo=f"Relato de prueba {indice}", autor="Autora de prueba",
                procedencia="donacion", estado="catalogado", codigo_dewey="863.6",
                cota="863.6\nA123\n2024", numero_registro=f"REG-2026-{indice:05d}",
            )
            session.add(libro)
            session.flush()
            session.add(Cataloging(
                libro_id=libro.id, clasificacion="Dewey", codigo_clasificacion="863.6",
                cota_completa=libro.cota, cutter="A123",
            ))
        libro_lc = Book(
            titulo="Lenguas en la comunidad", autor="Autora LC", procedencia="compra",
            estado="catalogado", cota="P123.L45", numero_registro="REG-2026-00005",
        )
        session.add(libro_lc)
        session.flush()
        session.add(Cataloging(
            libro_id=libro_lc.id, clasificacion="LC", codigo_clasificacion="P123.L45",
            cota_completa=libro_lc.cota,
        ))
        session.add(Book(
            titulo="Libro pendiente", autor="Autor pendiente", procedencia="donacion",
            estado="recibido", numero_registro="REG-2026-00006",
        ))

    fichero = FicheroController(database)
    assert len(fichero.buscar("Relato de prueba")) == 4
    assert len(fichero.buscar()) == 5
    resumen = {(fila["area"], fila["sistema"]): fila for fila in fichero.resumen_inventario()}
    assert resumen[("Literatura", "Dewey")] == {
        "area": "Literatura", "sistema": "Dewey", "catalogados": 4, "pendientes": 0, "total": 4,
    }
    assert resumen[("Lengua y literatura", "LC")]["total"] == 1
    assert resumen[("Sin clasificar", "Sin clasificar")]["pendientes"] == 1
    database.close()


def test_bibliotecas_reales_y_cotas_quedan_trasladas_sin_perder_historial(tmp_path):
    database = DatabaseManager(tmp_path / "multisucursal.db")
    database.initialize()
    libro_id = None

    with database.session() as session:
        central = session.query(Library).filter_by(nombre="Biblioteca Central Rómulo Gallegos").one()
        norte = Library(nombre="Sucursal Norte", direccion="Av. Norte 10", municipio="Municipio Norte", encargado="Ana", activa=True)
        sur = Library(nombre="Sede Sur Regional", direccion="Av. Sur 12", municipio="Municipio Sur", encargado="Luis", activa=True)
        session.add_all([norte, sur])
        session.flush()

        libro = Book(
            titulo="Libro de sucursales", autor="Autor de prueba",
            procedencia="compra", estado="catalogado", codigo_dewey="300",
            cota="300\nA123\n2024", numero_registro="REG-2026-90001",
            numero_volumenes=2,
        )
        session.add(libro)
        session.flush()
        libro_id = libro.id

        session.add(Cataloging(
            libro_id=libro.id, clasificacion="Dewey", codigo_clasificacion="300",
            cota_completa=libro.cota, cutter="A123",
        ))
        session.add_all([
            Location(libro_id=libro.id, biblioteca_id=central.id, tipo_ubicacion="sala", sala="Catalogación"),
            Location(libro_id=libro.id, biblioteca_id=norte.id, tipo_ubicacion="biblioteca_distribucion"),
            Movement(libro_id=libro.id, tipo_movimiento="distribucion", origen=central.nombre, destino=norte.nombre, detalle="Envío Norte"),
        ])
        session.flush()

    fichero = FicheroController(database)
    matriz = fichero.obtener_matriz_sucursales(libro_id=libro_id)
    nombres = {fila["biblioteca"] for fila in matriz["filas"]}
    assert {"Rómulo Gallegos", "Sucursal Norte", "Sede Sur Regional"}.issubset(nombres)

    ubicacion = UbicacionController(database)
    resultados = ubicacion.buscar(texto="REG-2026-90001")
    assert resultados
    assert resultados[0]["biblioteca"] == "Sucursal Norte"
    assert resultados[0]["libro"].cota == "300\nA123\n2024"
    assert any(mov.tipo_movimiento == "distribucion" for mov in ubicacion.historial(resultados[0]["libro"].id))

    database.close()