from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


package_books = Table(
    "bulto_libros",
    Base.metadata,
    Column("bulto_id", ForeignKey("bultos.id", ondelete="CASCADE"), primary_key=True),
    Column("libro_id", ForeignKey("libros.id", ondelete="RESTRICT"), primary_key=True),
)


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(160), default="")
    rol: Mapped[str] = mapped_column(String(24), nullable=False, default="bibliotecario")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    debe_cambiar_clave: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (CheckConstraint("rol IN ('admin', 'bibliotecario')", name="ck_usuario_rol"),)


class Book(Base):
    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    autor: Mapped[str] = mapped_column(String(240), default="", index=True)
    editorial: Mapped[str] = mapped_column(String(180), default="")
    anio: Mapped[int | None] = mapped_column(Integer)
    isbn: Mapped[str] = mapped_column(String(32), default="", index=True)
    edicion: Mapped[str] = mapped_column(String(100), default="")
    idioma: Mapped[str] = mapped_column(String(80), default="Español")
    paginas: Mapped[int | None] = mapped_column(Integer)
    numero_volumenes: Mapped[int | None] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    procedencia: Mapped[str] = mapped_column(String(40), nullable=False)
    procedencia_detalle: Mapped[str] = mapped_column(String(240), default="")
    fecha_ingreso: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    estado: Mapped[str] = mapped_column(String(24), default="recibido", nullable=False, index=True)
    cota: Mapped[str] = mapped_column(String(120), default="")
    codigo_dewey: Mapped[str] = mapped_column(String(40), default="")
    numero_registro: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("procedencia IN ('donacion', 'compra', 'biblioteca_nacional')", name="ck_libro_procedencia"),
        CheckConstraint("estado IN ('recibido', 'en_catalogacion', 'catalogado', 'distribuido', 'prestado')", name="ck_libro_estado"),
    )

    recepcion: Mapped["Reception | None"] = relationship(back_populates="libro", cascade="all, delete-orphan", uselist=False)
    catalogacion: Mapped["Cataloging | None"] = relationship(back_populates="libro", cascade="all, delete-orphan", uselist=False)
    ubicaciones: Mapped[list["Location"]] = relationship(back_populates="libro", cascade="all, delete-orphan")
    bultos: Mapped[list["Package"]] = relationship(secondary=package_books, back_populates="libros")
    movimientos: Mapped[list["Movement"]] = relationship(back_populates="libro")


class Reception(Base):
    __tablename__ = "recepcion"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id", ondelete="CASCADE"), unique=True)
    fecha_recepcion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    tipo_ingreso: Mapped[str] = mapped_column(String(40), nullable=False)
    donante_nombre: Mapped[str] = mapped_column(String(180), default="")
    proveedor_nombre: Mapped[str] = mapped_column(String(180), default="")
    institucion_origen: Mapped[str] = mapped_column(String(180), default="")
    observaciones: Mapped[str] = mapped_column(Text, default="")
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    modificado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    modificado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    fecha_modificacion: Mapped[datetime | None] = mapped_column(DateTime)

    libro: Mapped[Book] = relationship(back_populates="recepcion")


class Cataloging(Base):
    __tablename__ = "catalogacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id", ondelete="CASCADE"), unique=True)
    fecha_catalogacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    clasificacion: Mapped[str] = mapped_column(String(16), default="Dewey")
    codigo_clasificacion: Mapped[str] = mapped_column(String(40), default="")
    cota_completa: Mapped[str] = mapped_column(String(120), nullable=False)
    cutter: Mapped[str] = mapped_column(String(40), default="")
    catalogado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))

    libro: Mapped[Book] = relationship(back_populates="catalogacion")


class Library(Base):
    __tablename__ = "bibliotecas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    direccion: Mapped[str] = mapped_column(String(240), default="")
    municipio: Mapped[str] = mapped_column(String(120), default="")
    encargado: Mapped[str] = mapped_column(String(160), default="")
    telefono: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(160), default="")
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Location(Base):
    __tablename__ = "ubicaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id", ondelete="RESTRICT"), index=True)
    tipo_ubicacion: Mapped[str] = mapped_column(String(32), nullable=False)
    biblioteca_id: Mapped[int | None] = mapped_column(ForeignKey("bibliotecas.id", ondelete="SET NULL"))
    sala: Mapped[str] = mapped_column(String(100), default="")
    estante: Mapped[str] = mapped_column(String(100), default="")
    fecha_ubicacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    libro: Mapped[Book] = relationship(back_populates="ubicaciones")
    biblioteca: Mapped[Library | None] = relationship()

    __table_args__ = (CheckConstraint("tipo_ubicacion IN ('sala', 'deposito', 'biblioteca_distribucion')", name="ck_ubicacion_tipo"),)


class Package(Base):
    __tablename__ = "bultos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_envio: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    biblioteca_destino_id: Mapped[int] = mapped_column(ForeignKey("bibliotecas.id", ondelete="RESTRICT"))
    fecha_envio: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    cantidad_libros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    genero: Mapped[str] = mapped_column(String(120), default="")
    observaciones: Mapped[str] = mapped_column(Text, default="")
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))

    biblioteca_destino: Mapped[Library] = relationship()
    libros: Mapped[list[Book]] = relationship(secondary=package_books, back_populates="bultos")


class Movement(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id", ondelete="RESTRICT"), index=True)
    tipo_movimiento: Mapped[str] = mapped_column(String(32), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    origen: Mapped[str] = mapped_column(String(180), default="")
    destino: Mapped[str] = mapped_column(String(180), default="")
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    detalle: Mapped[str] = mapped_column(Text, default="")

    libro: Mapped[Book] = relationship(back_populates="movimientos")