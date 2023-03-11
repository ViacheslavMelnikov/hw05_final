from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class ViewsTest(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны+++++++++++++++++++++
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            'users/logged_out.html': reverse('users:logout'),
            'users/login.html': reverse('users:login'),
            'users/signup.html': reverse('users:signup'),
            'users/password_reset_form.html': reverse('users:password_reset'),
        }
        # Не получается у меня провести проверку этих двух шаблонов.
        # Можете подсказать? Спасибо
        # 'users/password_change_form.html':
        # reverse('users:password_change'),
        # 'users/password_change_done.html':
        # reverse('users:password_change_done'),
        # Не получается у меня провести проверку этих двух шаблонов.
        # Можете подсказать? Спасибо. Разбил строку из-за flake8

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                error_name = f'Ошибка: {reverse_name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)
