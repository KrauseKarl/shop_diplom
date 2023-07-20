from django.db.models import QuerySet, Q
from django.http import Http404

from app_item.forms import CommentForm
from app_item import models as item_models
from app_item.services import item_services
from app_store import models as store_models


class CommentHandler:
    """Класс для работы с комментариями."""

    @staticmethod
    def non_moderate_comments_amount() -> int:
        """Функция возвращает общее кол-во новых  комментариев для панели администратора."""
        return item_models.Comment.objects.filter(is_published=False).count()

    @staticmethod
    def total_comments() -> QuerySet[item_models.Comment]:
        """Функция возвращает все комментраии на сайте для панели администратора."""
        return item_models.Comment.objects.order_by("-created")

    @staticmethod
    def seller_stores_comments(user) -> QuerySet[item_models.Comment]:
        """Функция возвращает все комментраии магазина."""
        store = store_models.Store.objects.filter(owner=user)
        return item_models.Comment.objects.filter(item__store__in=store)

    @staticmethod
    def comment_counter(item_id: int) -> int:
        """
        Функция-счетчик для комментариев одного товрара.
        :param item_id: id товара
        :return: кол-во комментариев
        """
        item = item_services.ItemHandler.get_item(item_id=item_id)
        return item.comments.count()

    @staticmethod
    def get_comment(comment_id: id):
        """Функция для получения одного комментария."""
        comment = (
            item_models.Comment.objects.select_related("item", "user")
            .filter(id=comment_id)
            .first()
        )
        if not comment:
            raise Http404("Комментарий не найден")
        return comment

    @staticmethod
    def set_comment_approved(comment_id):
        """Функция для подтверждения комментария."""
        comment = CommentHandler.get_comment(comment_id)
        comment.is_published = True
        comment.save(
            update_fields=[
                "is_published",
            ]
        )
        return comment

    @staticmethod
    def set_comment_reject(comment_id):
        """Функция для отклонения  комментария."""
        comment = CommentHandler.get_comment(comment_id)
        comment.is_published = False
        comment.save(
            update_fields=[
                "is_published",
            ]
        )
        return comment

    @staticmethod
    def get_comment_list_by_user(user) -> QuerySet[item_models.Comment]:
        """Функция возвращает список всех комментариев пользователя."""
        comments = item_models.Comment.objects.select_related("item").filter(user=user)
        return comments

    @staticmethod
    def get_comment_cont(item_id):
        """Функция возвращает общее количество комментариев товара."""
        return item_models.Comment.objects.filter(
            Q(item_id=item_id) & Q(is_published=True)
        ).count()

    @staticmethod
    def add_comment(user, item_id, data):
        """
        Функция для добавления комментария.

        :param user: экземпляр пользователя.
        :param item_id: id-товара.
        :param data: словарь с данными из формы комментария.
        :return: новый комментарий.
        """
        item = item_services.ItemHandler.get_item(item_id)
        form = CommentForm(data)
        new_comment = form.save(commit=False)
        new_comment.item = item
        new_comment.user = user
        new_comment.is_published = False
        new_comment.save()
        return new_comment

    @staticmethod
    def get_permission(user_id: int, comment_user_id: int) -> bool:
        """
        Функция для установления права пользователя на комментарий.
        :param user_id: ID пользователя.
        :param comment_user_id: ID автора комментария.
        :return: True - если комментарий принадлежит пользователю, False - если нет.
        """
        if comment_user_id == user_id:
            return True
        return False

    @staticmethod
    def delete_comment(user, comment_id) -> dict:
        """
        Функция для удаления комментария.

        Проверят право на удаления комментария.
        :param user: экземпляр пользователя.
        :param comment_id: id-комментария.
        :return: удаляет комментарий.
        """
        comment = CommentHandler.get_comment(comment_id)
        permission = CommentHandler.get_permission(user.id, comment.user.id)
        if permission:
            return comment.delete()
        return comment
