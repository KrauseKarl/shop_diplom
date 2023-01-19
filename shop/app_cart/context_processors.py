from app_cart.services.cart_services import get_current_cart


def get_cart(request) -> dict:
    """
    Функция возвращает словарь состоящий
    из корзины,
    словаря(товары отсортированные по магазинам, общая стоимость и стоимость доставки)
    и общей стоимости доставки
    """
    cart_dict = get_current_cart(request)
    return {'cart_dict': cart_dict}
