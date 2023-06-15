from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from app_user.models import Profile
from app_user.services.register_services import ProfileHandler


class AuthForm(AuthenticationForm):
    """
    Форма для аутентификации пользователя
    (model User)
    """
    default_errors = {
        'required': 'Поле обязательно для заполнения',
        'invalid': 'Введите допустимое значение',
        'inactive': 'Такой пользователь не зарегистрирован',
    }
    username = forms.CharField(error_messages=default_errors)
    password = forms.CharField(widget=forms.PasswordInput, error_messages=default_errors)


class RegisterUserForm(UserCreationForm):
    default_errors = {
        'required': 'Поле обязательно для заполнения',
        'invalid': 'Введите допустимое значение',
        'inactive': 'Такой пользователь не зарегистрирован',
    }
    username = forms.CharField(max_length=30,
                               label='имя пользователя',
                               widget=forms.Textarea(attrs={'rows': 1, 'cols': 20})
                               )
    first_name = forms.CharField(max_length=100,
                                 label='имя',
                                 help_text='имя',
                                 required=False,
                                 )
    last_name = forms.CharField(max_length=100,
                                label='фамилия',
                                help_text='фамилия',
                                required=False,
                                )
    password1 = forms.CharField(label="пароль",
                                strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
                                )
    password2 = forms.CharField(label="пароль подтвердить",
                                strip=False,
                                help_text='',
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    telephone = forms.CharField(label='телефон', help_text='укажите ваш контактный номер телефона',)
    email = forms.EmailField(label='E-mail', help_text='укажите адрес вашей электронной почты',)
    group = forms.CharField(label='группа', error_messages=default_errors)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'telephone', 'email', 'group')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Такой пользователь уже зарегистрирован")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Ваши пароли не совпадают")
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Это электронная почта уже используется")
        return email

    def clean_telephone(self):
        telephone = ProfileHandler.telephone_formatter(self.cleaned_data.get('telephone'))
        if Profile.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Этот телефон уже используется")
        return telephone


class RegisterUserFormFromOrder(UserCreationForm):
    username = forms.CharField(max_length=30,
                               label='имя пользователя',
                               widget=forms.Textarea(attrs={'rows': 1, 'cols': 20})
                               )
    first_name = forms.CharField(max_length=100,
                                 label='имя',
                                 help_text='имя',
                                 )
    last_name = forms.CharField(max_length=100,
                                label='фамилия',
                                help_text='фамилия',
                                )
    password1 = forms.CharField(label="пароль",
                                strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
                                )
    password2 = forms.CharField(label="пароль подтвердить",
                                strip=False,
                                help_text='',
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    telephone = forms.CharField(label='телефон',
                                help_text='телефон'
                                )
    email = forms.EmailField(label='E-mail',
                             help_text='электронная почта'
                             )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'telephone', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Такой пользователь уже зарегистрирован")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Ваши пароли не совпадают")
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Это электронная почта уже используется")
        return email

    def clean_telephone(self):
        telephone = ProfileHandler.telephone_formatter(self.cleaned_data.get('telephone'))
        if Profile.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Этот номер телефона уже используется")
        return telephone


class UpdateUserForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email):
            raise forms.ValidationError("Это электронная почта уже используется")
        return email


class UpdateProfileForm(forms.ModelForm):
    telephone = forms.CharField(max_length=18)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ('avatar', 'telephone')

    def clean_telephone(self):
        telephone = ProfileHandler.telephone_formatter(self.cleaned_data.get('telephone'))
        if Profile.objects.exclude(pk=self.instance.pk).filter(telephone__iexact=telephone):
            raise forms.ValidationError("Этот номер телефона уже используется")
        return telephone
