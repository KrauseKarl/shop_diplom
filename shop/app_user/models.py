import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse
from app_item.models import Item


def profile_directory_path(path):
    """Функция для переименования файла с изображением аватара пользователя."""
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        filename = 'user_id_{}.{}'.format(instance.user.id, ext)
        return os.path.join(path, filename)

    return wrapper


def user_dir_path(instance, filename):
    """Функция для переименования файла с изображением аватара пользователя."""
    ext = filename.split('.')[-1]
    filename = 'user_id_{}.{}'.format(instance.user.id, ext)
    return f'avatar/{filename}'


class Profile(models.Model):
    """Модель пользователя."""
    DEFAULT_IMAGE = '/media/default_images/default_avatar.png'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='пользователь'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='активный профиль'
    )
    avatar = models.ImageField(
        upload_to=user_dir_path,
        # upload_to=profile_directory_path('avatar/'),
        # avatar = models.ImageField(upload_to='avatar/',
        default='',
        verbose_name='аватар'
    )
    telephone = models.CharField(
        max_length=18,
        verbose_name='телефон',
        unique=True
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        null=True
    )
    review_items = models.ManyToManyField(
        Item,
        related_name='item_views'
    )

    objects = models.Manager()

    class Meta:
        ordering = ['user']
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def get_absolute_url(self):
        return reverse('app_users:profile', kwargs={'pk': self.pk})

    def get_avatar(self):
        if self.avatar:
            return f'/media/{self.avatar}'
        else:
            return '/media/default_images/default_avatar.png'

    @property
    def is_customer(self):
        """
        Функция проверяет роль пользователя.
        Если роль - "покупатель", то возвращает True,
        в остальных случаях - False.
        """
        if self.user.groups.filter(name='customer').exists():
            return True
        return False

    @property
    def is_seller(self):
        """
        Функция проверяет роль пользователя.
        Если роль - "продавец", то возвращает True,
        в остальных случаях - False.
        """
        if self.user.groups.filter(name='seller').exists():
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
            if self.user.groups.filter(name='admin').exists():
                return True
        except AttributeError:
            return False


# @receiver(models.signals.pre_save, sender=Profile)
# def delete_file_on_change_extension(sender, instance, **kwargs):
#     Profile.objects.get(pk=instance.pk)
#     try:
#         old_avatar = str(Profile.objects.get(pk=instance.pk).avatar.path)
#         new_avatar = instance.avatar
#         if old_avatar != new_avatar:
#             os.remove(old_avatar)
#     except (ValueError, FileNotFoundError):
#         pass
