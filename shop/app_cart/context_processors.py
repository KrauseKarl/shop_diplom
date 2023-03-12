from app_cart.services.cart_services import get_current_cart, get_items_in_cart


def get_cart(request) -> dict:
    """
    Функция возвращает словарь состоящий
    из корзины,
    словаря(товары отсортированные по магазинам, общая стоимость и стоимость доставки)
    и общей стоимости доставки
    """
    cart_dict = get_current_cart(request)
    return {'cart_dict': cart_dict}


def in_cart(request):
    """Функция определяем какие товары в корзине (для надписи "В КОРЗИНЕ")."""
    return {'in_cart': get_items_in_cart(request)}
