# from PIL import Image
import os
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
    ROLE = (
        ('ADM', 'администратор'),
        ('SLR', 'продавец'),
        ('CSR', 'покупатель'),
    )

    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                related_name='profile',
                                verbose_name='пользователь')
    role = models.CharField(max_length=3,
                            choices=ROLE,
                            default='CSR',
                            verbose_name='роль')
    avatar = models.ImageField(upload_to=user_dir_path,
                               # upload_to=profile_directory_path('avatar/'),
                               # avatar = models.ImageField(upload_to='avatar/',
                               default='',
                               verbose_name='аватар')
    telephone = models.CharField(max_length=18,
                                 verbose_name='телефон', unique=True)
    date_joined = models.DateTimeField(auto_now_add=True,
                                       null=True)
    review_items = models.ManyToManyField(Item,
                                          related_name='item_views')

    objects = models.Manager()

    class Meta:
        ordering = ['user']
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def save(self, *args, **kwargs):
        if not self.telephone:
            self.telephone = self.telephone.split('7')[1].replace('(', '').replace(')', '').replace(' ', '')
        super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def get_absolute_url(self):
        return reverse('app_users:profile', kwargs={'pk': self.pk})

    @property
    def is_customer(self):
        """
        Функция проверяет роль пользователя.
        Если роль - "покупатель", то возвращает True,
        в остальных случаях - False.
        """
        if self.role == 'CSR':
            return True
        return False

    @property
    def is_seller(self):
        """
        Функция проверяет роль пользователя.
        Если роль - "продавец", то возвращает True,
        в остальных случаях - False.
        """
        if self.role == 'SLR':
            return True
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
