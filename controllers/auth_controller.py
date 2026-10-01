import hmac
import secrets

from sqlalchemy import select

from database.db_manager import DatabaseManager
from database.models import User
from database.seed_data import hash_password


class AuthController:
    def __init__(self, database: DatabaseManager):
        self.database = database

    def autenticar(self, username: str, password: str) -> tuple[bool, User | str]:
        with self.database.session() as session:
            user = session.scalar(select(User).where(User.username == username.strip()))
            if user is None or not user.activo:
                return False, "Usuario o contraseña incorrectos."
            password_valido = hmac.compare_digest(user.password_hash, hash_password(password, user.salt))
            if not password_valido:
                return False, "Usuario o contraseña incorrectos."
            return True, user

    def cambiar_clave(self, user_id: int, clave_actual: str, clave_nueva: str) -> tuple[bool, str]:
        if len(clave_nueva) < 10:
            return False, "La nueva contraseña debe tener al menos 10 caracteres."
        with self.database.session() as session:
            user = session.get(User, user_id)
            if user is None or not hmac.compare_digest(user.password_hash, hash_password(clave_actual, user.salt)):
                return False, "La contraseña actual no es correcta."
            user.salt = secrets.token_hex(16)
            user.password_hash = hash_password(clave_nueva, user.salt)
            user.debe_cambiar_clave = False
            return True, "Contraseña actualizada."

    @staticmethod
    def _solicitante_es_admin(session, solicitante_id: int | None) -> bool:
        solicitante = session.get(User, solicitante_id) if solicitante_id is not None else None
        return bool(solicitante and solicitante.activo and solicitante.rol == "admin")

    def crear_usuario(self, username: str, nombre: str, password: str, rol: str, solicitante_id: int) -> tuple[bool, str]:
        if not username.strip() or len(password) < 10 or rol not in {"admin", "bibliotecario"}:
            return False, "Indique usuario, rol válido y contraseña de al menos 10 caracteres."
        salt = secrets.token_hex(16)
        with self.database.session() as session:
            if not self._solicitante_es_admin(session, solicitante_id):
                return False, "Sólo un administrador activo puede gestionar usuarios."
            if session.scalar(select(User.id).where(User.username == username.strip())):
                return False, "El nombre de usuario ya existe."
            session.add(User(
                username=username.strip(), nombre_completo=nombre.strip(), rol=rol,
                salt=salt, password_hash=hash_password(password, salt),
            ))
        return True, "Usuario creado."

    def actualizar_usuario(self, user_id: int, username: str, nombre: str, rol: str, password: str, solicitante_id: int) -> tuple[bool, str]:
        username = username.strip()
        if not username or rol not in {"admin", "bibliotecario"} or (password and len(password) < 10):
            return False, "Indique usuario, rol válido y, si cambia la contraseña, al menos 10 caracteres."
        with self.database.session() as session:
            if not self._solicitante_es_admin(session, solicitante_id):
                return False, "Sólo un administrador activo puede gestionar usuarios."
            user = session.get(User, user_id)
            if user is None:
                return False, "No se encontró el usuario."
            if user.username == "admin" and (username != "admin" or rol != "admin"):
                return False, "No se puede cambiar el usuario ni el rol de la cuenta inicial admin."
            duplicado = session.scalar(select(User.id).where(User.username == username, User.id != user_id))
            if duplicado:
                return False, "El nombre de usuario ya existe."
            if user.activo and user.rol == "admin" and rol != "admin":
                otro_admin = session.scalar(select(User.id).where(
                    User.id != user_id, User.rol == "admin", User.activo.is_(True)
                ).limit(1))
                if otro_admin is None:
                    return False, "Debe mantenerse al menos un administrador activo."
            user.username = username
            user.nombre_completo = nombre.strip()
            user.rol = rol
            if password:
                user.salt = secrets.token_hex(16)
                user.password_hash = hash_password(password, user.salt)
        return True, "Usuario actualizado."

    def cambiar_estado_usuario(self, user_id: int, activo: bool, solicitante_id: int) -> tuple[bool, str]:
        with self.database.session() as session:
            if not self._solicitante_es_admin(session, solicitante_id):
                return False, "Sólo un administrador activo puede gestionar usuarios."
            user = session.get(User, user_id)
            if user is None:
                return False, "No se encontró el usuario."
            if user.username == "admin" and not activo:
                return False, "No se puede desactivar la cuenta inicial admin."
            if not activo and user.activo and user.rol == "admin":
                otro_admin = session.scalar(select(User.id).where(
                    User.id != user_id, User.rol == "admin", User.activo.is_(True)
                ).limit(1))
                if otro_admin is None:
                    return False, "Debe mantenerse al menos un administrador activo."
            user.activo = activo
        return True, "Usuario activado." if activo else "Usuario desactivado."

    def desactivar_usuario(self, user_id: int, solicitante_id: int) -> tuple[bool, str]:
        return self.cambiar_estado_usuario(user_id, False, solicitante_id)

    def listar_usuarios(self, solicitante_id: int) -> list[User]:
        with self.database.session() as session:
            if not self._solicitante_es_admin(session, solicitante_id):
                return []
            return list(session.scalars(select(User).order_by(User.username)))