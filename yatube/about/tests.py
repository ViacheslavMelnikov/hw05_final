from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        cls.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    # Проверяем общедоступные страницы+
    def test_public_pages(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            '/about/author/',
            '/about/tech/')
        for url in templates_url_names:
            response = self.guest_client.get(url)
            err_message = f'Ошибка доступа: {url}'
            self.assertEqual(response.status_code, HTTPStatus.OK, err_message)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'}
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                error_message = f'Ошибка вызываемого шаблона: {url}'
                self.assertTemplateUsed(response, template, error_message)
