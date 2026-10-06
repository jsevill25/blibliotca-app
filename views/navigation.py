def add_navigation_page(stack, navigation: dict, title: str, button, page) -> None:
    stack.addWidget(page)
    navigation[title] = (button, page)


def show_navigation_page(stack, navigation: dict, title: str) -> None:
    selected_button, page = navigation[title]
    stack.setCurrentWidget(page)
    for button, _page in navigation.values():
        button.setChecked(button is selected_button)
