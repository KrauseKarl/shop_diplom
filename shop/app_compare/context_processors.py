"""Модуль содержит контекст-процессоры списка для сравнения."""
from app_compare.compare import Comparison


def compare_list(request) -> dict:
    """ Функция возвращает словарь с данными для сравнения."""
    compares = Comparison(request)
    return {"compare_count": compares.__len__(), "compare_item": compares}
