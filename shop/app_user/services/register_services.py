"""
Сервисы работы с группами, созданием и редактированием пользователя.

1. GroupHandler - класс для работы с группами пользователей.
2. ProfileHandler - класс для работы с профилем пользователя.

"""
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.urls import reverse

# services
from app_cart.services import cart_services
# models
from app_user.models import Profile


class GroupHandler:
    """Класс для работы с группами пользователей."""

    @staticmethod
    def get_group(group):
        """Функция возвращет экземпляр группы по имени групп."""
        return Group.objects.get(name=group)

    @staticmethod
    def set_group(user, group):
        """Функция добавляет пользователя в группу."""
        group = GroupHandler().get_group(group)
        user.groups.add(group)
        user.save()
        return user


class ProfileHandler:
    """Класс для работы с профилем пользователя."""

    @staticmethod
    def create_user(request, form):
        """Функция создает пользователя."""

        # создание пользователя
        user = form.save()
        user.first_name = form.cleaned_data.get("first_name")
        user.last_name = form.cleaned_data.get("last_name")
        user.save(update_fields=["first_name", "last_name"])

        # присвоение группы для пользователя
        GroupHandler().set_group(
            user=user, group=form.cleaned_data.get("group")
        )

        # создание расширенного профиля пользователя
        ProfileHandler().create_profile(
            user=user, telephone=form.cleaned_data.get("telephone"),
        )
        #  находим анонимную корзину и
        #  присваиваем ее вновь созданному пользователю.
        cart_services.identify_cart(
            user=request.user, session=request.session
        )

        user = authenticate(
            request,
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password1"),
        )

        login(request, user)

        next_page = request.GET.get("next")
        path = (
            next_page
            if next_page
            else reverse("app_user:account", kwargs={"pk": user.pk})
        )

        # удаление данных об анонимной корзине из COOKIES
        # при создании нового пользователя
        response = cart_services.delete_cart_cookies(request, path)
        return response

    @staticmethod
    def create_profile(user, telephone):
        """Функция создает расширенный профиль пользователя."""

        profile = Profile.objects.create(
            user=user,
            telephone=ProfileHandler.telephone_formatter(telephone),
            is_active=True,
        )
        return profile

    @staticmethod
    def telephone_formatter(telephone):
        """Функция форматирует номер телефона (оставляет только цифры)."""

        if str(telephone).startswith("+7"):
            telephone = (
                str(telephone)
                .split("+7")[1]
                .replace("(", "")
                .replace(")", "")
                .replace(" ", "")
            )
        return telephone

    @staticmethod
    def update_profile(request):
        """Функция обновляет базовый и расширенный профиль пользователя."""

        from app_user.forms import UpdateProfileForm, UpdateUserForm

        user_form = UpdateUserForm(data=request.POST, instance=request.user)
        profile_form = UpdateProfileForm(
            data=request.POST,
            files=request.FILES,
            instance=request.user.profile,
        )
        user_form.save()
        profile_form.save()
