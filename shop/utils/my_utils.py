from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.template.defaultfilters import slugify as django_slugify
from django.db import connection

alphabet = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g',
    'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ы': 'i',
    'э': 'e', 'ю': 'yu', 'я': 'ya'
}


def slugify_for_cyrillic_text(string) -> str:
    """
    Функция преобразует строку из кириллицы в латиницу.
    :param: строка на кириллице
    :return string: строка на латинице
    """
    return django_slugify(''.join(alphabet.get(letter, letter) for letter in string.lower()))


class MixinPaginator(Paginator):
    def my_paginator(self, queryset, request, paginate_by):
        try:
            page = int(request.GET.get('page', '1'))
        except:
            page = 1
        paginator = Paginator(queryset, paginate_by)

        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset


def query_counter(func):
    """Декоратор для подсчета запросов к БД."""

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        func_name = func.__name__
        class_name = func.__qualname__.split(".")[0]
        file_name = func.__module__.split(".")[-1]
        try:
            folder_name = func.__module__.split(".")[-2]
            app_name = func.__module__.split(".")[-3]
        except:
            folder_name = '__'
            app_name = func.__module__.split(".")[-2]

        print('\n===========================================================================================')
        print('ЗАПРОСОВ = ', len(connection.queries), '|',
              f'FUNC - {func_name} | {class_name} | {file_name} | {folder_name} | {app_name}')
        print('=============================================================================================\n')
        return result

    return wrapper
