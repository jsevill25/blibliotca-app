# -*- coding: utf-8 -*-
import sys

from PySide6.QtWidgets import QApplication, QDialog

from config import APP_NAME
from controllers.auth_controller import AuthController
from database.db_manager import get_default_database
from views.interface_choice_view import InterfaceChoiceView
from views.login_view import LoginView
from views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    choice = InterfaceChoiceView()
    if choice.exec() != QDialog.DialogCode.Accepted:
        return 0

    database = get_default_database()
    if choice.mode == "web":
        from web_preview import run_web_preview

        try:
            run_web_preview(database, host="127.0.0.1", port=0, open_browser=True)
        finally:
            database.close()
        return 0

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
