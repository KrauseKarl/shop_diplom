from django.db.models import Q

from app_item.models import Category, Tag


def categories(request):
    """Функция для выбора всех категорий, в которых есть товары."""
    return {'categories': Category.objects.all()}


def tags(request):
    """Функция для выбора всех тегов."""
    return {'tags': Tag.objects.order_by('title')}
