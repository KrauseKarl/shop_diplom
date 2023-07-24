"""Модуль содержит модели Пользоваетля."""
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from app_item.models import Item


def user_dir_path(instance, filename):
    """
    Функция для переименования файла.

    Возвращает новое название файла
    с изображением аватара пользователя.
    """
    ext = filename.split(".")[-1]
    filename = "user_id_{}.{}".format(instance.user.id, ext)
    return f"avatar/{filename}"


class Profile(models.Model):
    """Модель пользователя."""

    DEFAULT_AVATAR = "default_images/default_avatar.png"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )
    is_active = models.BooleanField(
        default=False, verbose_name="активный профиль"
    )
    avatar = models.ImageField(
        upload_to=user_dir_path,
        default=os.path.join(settings.MEDIA_URL, DEFAULT_AVATAR),
        verbose_name="аватар",
    )
    telephone = models.CharField(
        max_length=18, verbose_name="телефон", unique=True
    )
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    review_items = models.ManyToManyField(Item, related_name="item_views")

    objects = models.Manager()

    class Meta:
        ordering = ["user"]
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        """Метод для отображения информации об объекте класса Profile."""
        return f"{self.user.first_name} {self.user.last_name}"

    def get_absolute_url(self):
        """Метод возвращает абсолютный путь пользовактеля."""
        return reverse("app_users:profile", kwargs={"pk": self.pk})

    def get_avatar(self):
        """
        Функция возвращает URL изображения.

        Возвращется URL изображения
        или дефолтное изображение.
        """
        if self.avatar:
            return os.path.join(settings.MEDIA_URL, self.avatar.url)
        else:
            return os.path.join(settings.MEDIA_URL, self.DEFAULT_AVATAR)

    @property
    def is_customer(self):
        """
        Функция проверяет роль пользователя.

        Если роль - "покупатель", то возвращает True,
        в остальных случаях - False.
        """
        if self.user.groups.filter(name="customer").exists():
            return True
        return False

    @property
    def is_seller(self):
        """
        Функция проверяет роль пользователя.

        Если роль - "продавец", то возвращает True,
        в остальных случаях - False.
        """
        if self.user.groups.filter(name="seller").exists():
            return True
        return False

    @property
    def is_admin(self):
        """
        Функция проверяет роль пользователя.

        Если роль - "админ", то возвращает True,
        в остальных случаях - False.
        """
        try:
            if self.user.groups.filter(name="admin").exists():
                return True
        except AttributeError:
            return False
