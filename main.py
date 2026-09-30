# -*- coding: utf-8 -*-
from models.database import inicializar_base_datos
from controllers.libro_controller import LibroController
from views.main_view import MainView

def main():
    # 1. Asegurar persistencia y tablas con soporte a migración
    inicializar_base_datos()

    # 2. Instanciar Controlador MVC
    controlador = LibroController()

    # 3. Lanzar Vista de escritorio CustomTkinter
    app = MainView(controlador)
    app.mainloop()

if __name__ == "__main__":
    main()
