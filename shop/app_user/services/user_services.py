from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


def get_user(user):
    try:
        return User.objects.get(id=user.id)
    except ObjectDoesNotExist:
        return None


def is_customer(user):
    """
    Функция проверяет роль пользователя.
    Если роль - "покупатель", то возвращает True,
    в остальных случаях - False.
    """
    if user.profile.role == 'CSR':
        return True
    return False
