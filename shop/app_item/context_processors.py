from django.db.models import Q

from app_item.models import Category, Tag


def categories(request):
    """Функция для выбора всех категорий, в которых есть товары."""

    return {'categories': Category.objects.exclude(Q(items=None) & Q(sub_categories=True))}


def tags(request):
    """Функция для выбора всех тегов."""

    return {'tags': Tag.objects.order_by('title')}
