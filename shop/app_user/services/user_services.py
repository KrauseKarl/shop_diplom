from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist


def get_user(user):
    try:
        return User.objects.get(id=user.id)
    except ObjectDoesNotExist:
        return None


def user_in_group(user, group_name: str) -> bool:
    group = Group.objects.get(name=group_name)
    if group in user.groups.all():
        return True
    return False


def is_customer(user):
    """
    Функция проверяет роль пользователя.
    Если роль - "покупатель", то возвращает True,
    в остальных случаях - False.
    """
    customer = Group.objects.get(name='customer')
    if user.groups.first() == customer:
        return True
    return False
