from django.db.models import QuerySet, Q

from app_item.forms import CommentForm
from app_item.models import Item, Comment
from app_item.services.item_services import ItemHandler


class CommentHandler:
    @staticmethod
    def comment_counter(item_id) -> int:
        """
        Функция-счетчик для комментариев одного товрара.
        :param item_id: id товара
        :return: кол-во комментариев
        """
        item = ItemHandler.get_item(item_id=item_id)
        return item.comments.count()

    @staticmethod
    def get_permission(user, comment) -> bool:
        """
        Функция для установления права пользователя на комментарий.
        :param user: экземпляр пользователя.
        :param comment: экземпляр комментария.
        :return: True - если комментарий принадлежит пользователю, False - если нет.
        """
        if comment.user.id == user.id:
            return True
        return False

    @staticmethod
    def get_comment(comment_id):
        """Функция для получения одного комментария."""
        return Comment.objects.select_related('item', 'user').filter(id=comment_id)[0]

    @staticmethod
    def set_comment_approved(comment_id):
        """Функция для подтверждения комментария."""
        comment = CommentHandler.get_comment(comment_id)
        comment.is_published = True
        comment.save()
        return comment

    @staticmethod
    def set_comment_reject(comment_id):
        """Функция для отклонения  комментария."""
        comment = CommentHandler.get_comment(comment_id)
        comment.is_published = False
        comment.save()
        return comment

    @staticmethod
    def get_comment_list_by_user(request) -> QuerySet[Comment]:
        """Функция возвращает список всех комментариев пользователя. """
        comments = Comment.objects.select_related('item').filter(user=request.user)
        return comments

    @staticmethod
    def get_comment_cont(item_id):
        """Функция возвращает общее количество комментариев товара. """
        return Comment.objects.filter(Q(item_id=item_id) & Q(is_published=True)).count()

    @staticmethod
    def add_comment(user, item_id, data):
        """
        Функция для добавления комментария.
        :param user: экземпляр пользователя.
        :param item_id: id-товара.
        :param data: словарь с данными из формы комментария.
        :return: новый комментарий.
        """
        item = ItemHandler.get_item(item_id)
        form = CommentForm(data)
        new_comment = form.save(commit=False)
        new_comment.item = item
        new_comment.user = user
        new_comment.is_published = False
        new_comment.save()
        return new_comment

    @staticmethod
    def delete_comment(user, comment_id, item_id):
        """
        Функция для удаления комментария.
        Проверят право на удаления комментария.
        :param user: экземпляр пользователя.
        :param item_id: id-товара.
        :param comment_id: id-комментария.
        :return: удаляет комментарий.
        """
        comment = CommentHandler.get_comment(comment_id)
        permission = CommentHandler.get_permission(user, comment)
        item = ItemHandler.get_item(item_id)
        if permission:
            comment.delete()
            return True
        return comment
