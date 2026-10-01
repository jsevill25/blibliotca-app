from datetime import date

from database.db_manager import DatabaseManager
from database.models import Book, Cataloging, Library
from controllers.auth_controller import AuthController
from controllers.catalogacion_controller import CatalogacionController
from controllers.distribucion_controller import DistribucionController
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
    }, usuario.id)
    assert creado is True
    libro = recepcion.listar(texto="978-0000000001")[0]
    assert libro.numero_registro == numero
    assert libro.estado == "recibido"
    editado, mensaje = recepcion.editar(libro.id, {
        "titulo": libro.titulo, "autor": libro.autor, "editorial": libro.editorial,
        "isbn": libro.isbn, "edicion": libro.edicion, "idioma": libro.idioma,
        "anio": "2021", "paginas": "220", "procedencia": "compra",
        "procedencia_detalle": "Factura 15", "proveedor_nombre": "Librería Central",
        "observaciones": "Corregido",
    }, usuario.id)
    assert editado is True, mensaje
    libro = recepcion.listar(texto="978-0000000001")[0]
    assert libro.recepcion.modificado is True
    assert libro.recepcion.modificado_por == usuario.id
    assert libro.recepcion.proveedor_nombre == "Librería Central"
    assert recepcion.listar(procedencia="compra", inicio=date.today(), fin=date.today())[0].id == libro.id
    edicion_invalida, _ = recepcion.editar(libro.id, {
        "titulo": libro.titulo, "procedencia": "compra", "anio": str(date.today().year + 5),
        "paginas": "220",
    }, usuario.id)
    assert edicion_invalida is False

    catalogacion = CatalogacionController(database)
    assert catalogacion.catalogar(libro.id, "Dewey", "863.6", "G216", "863.6\nG216\n2020", usuario.id)[0] is True
    assert catalogacion.catalogar(libro.id, "Dewey", "863.6", "G216", "otra cota", usuario.id)[0] is False
    with database.session() as session:
        persistido = session.get(Book, libro.id)
        ficha = session.query(Cataloging).filter_by(libro_id=libro.id).one()
        assert persistido.codigo_dewey == "863.6"
        assert ficha.clasificacion == "Dewey"
        assert ficha.codigo_clasificacion == "863.6"

    with database.session() as session:
        sucursal = Library(nombre="Sucursal Norte", direccion="Calle 1", activa=True)
        session.add(sucursal)
        session.flush()
        sucursal_id = sucursal.id

    distribucion = DistribucionController(database)
    enviado, codigo = distribucion.crear_bulto(sucursal_id, [libro.id], usuario.id)
    assert enviado is True
    assert codigo.startswith("ENV-")

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
    database.close()