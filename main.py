# -*- coding: utf-8 -*-
import sys

from PySide6.QtWidgets import QApplication, QDialog

from config import APP_NAME
from controllers.auth_controller import AuthController
from database.db_manager import get_default_database
from views.login_view import LoginView
from views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    database = get_default_database()
    login = LoginView(AuthController(database))
    if login.exec() != QDialog.DialogCode.Accepted:
        database.close()
        return 0

    window = MainWindow(database, login.current_user)
    window.show()
    resultado = app.exec()
    database.close()
    return resultado


if __name__ == "__main__":
    sys.exit(main())
