import ast
from pathlib import Path

from views.navigation import add_navigation_page, show_navigation_page


class FakeStack:
    def __init__(self):
        self.pages = []
        self.current = None

    def addWidget(self, page):
        self.pages.append(page)

    def setCurrentWidget(self, page):
        self.current = page


class FakeButton:
    def __init__(self):
        self.checked = False

    def setChecked(self, checked):
        self.checked = checked


def test_navigation_selects_registered_stack_page_and_updates_button_state():
    stack = FakeStack()
    navigation = {}
    first_button, second_button = FakeButton(), FakeButton()
    first_page, second_page = object(), object()

    add_navigation_page(stack, navigation, "Manual", first_button, first_page)
    add_navigation_page(stack, navigation, "Recepción", second_button, second_page)
    show_navigation_page(stack, navigation, "Recepción")

    assert stack.pages == [first_page, second_page]
    assert stack.current is second_page
    assert first_button.checked is False
    assert second_button.checked is True


def test_application_entrypoint_only_starts_desktop_login_flow():
    source = Path(__file__).resolve().parents[1] / "main.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        f"{node.module}.{alias.name}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    )

    assert "PySide6.QtWidgets.QDialog" in imports
    assert "views.login_view.LoginView" in imports
    assert "views.main_window.MainWindow" in imports
    assert not any("web" in imported.lower() for imported in imports)
    assert "views.interface_choice_view.InterfaceChoiceView" not in imports
