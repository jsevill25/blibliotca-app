import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from database.models import Library, User


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 310_000).hex()


def seed_initial_data(session: Session) -> None:
    if session.scalar(select(User.id).where(User.username == DEFAULT_ADMIN_USERNAME)) is None:
        salt = secrets.token_hex(16)
        session.add(User(
            username=DEFAULT_ADMIN_USERNAME,
            nombre_completo="Administrador del sistema",
            rol="admin",
            salt=salt,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD, salt),
            debe_cambiar_clave=True,
        ))

    if session.scalar(select(Library.id).where(Library.nombre == "Biblioteca Central Rómulo Gallegos")) is None:
        session.add(Library(nombre="Biblioteca Central Rómulo Gallegos", activa=True))

    session.commit()