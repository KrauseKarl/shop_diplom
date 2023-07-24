"""Сервисы работы с пользователя."""

from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404


def get_user(user) -> User:
    """Функция возвращет пользователя по ID."""
    return get_object_or_404(User, id=user.id)


def user_in_group(user, group_name: list) -> bool:
    """Функция проверяет участие пользователя в группе."""
    group = Group.objects.filter(name__in=group_name)
    if user.groups.first() in group:
        return True
    return False


def is_customer(user) -> bool:
    """
    Функция проверяет роль пользователя.

    Если роль - "покупатель", то возвращает True,
    в остальных случаях - False.
    """
    customer = Group.objects.get(name="customer")
    if user.groups.first() == customer:
        return True
    return False
