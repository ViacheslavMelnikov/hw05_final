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
            '/auth/signup/',
            '/auth/login/',
            '/auth/logout/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/done/')
        for url in templates_url_names:
            response = self.guest_client.get(url)
            err_message = f'Ошибка доступа: {url}'
            self.assertEqual(response.status_code, HTTPStatus.OK, err_message)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_page_for_an_authorized_user(self):
        """Страница доступна авторизованному пользователю"""
        pages = (
            '/auth/password_change/',
            '/auth/password_change/done/')
        for page in pages:
            response = self.authorized_client.get(page)
            error_message = f'Нет доступа к странице: {page}'
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                error_message)

    # Проверяем редиректы для неавторизованного пользователя+
    def test_task_list_url_redirect_anonymous(self):
        url1 = '/auth/login/?next=/auth/password_change/'
        url2 = '/auth/login/?next=/auth/password_change/done/'
        pages = {
            '/auth/password_change/': url1,
            '/auth/password_change/done/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'users/logged_out.html': '/auth/logout/',
            'users/login.html': '/auth/login/',
            'users/password_reset_complete.html': '/auth/reset/done/',
            'users/password_reset_done.html': '/auth/password_reset/done/',
            'users/password_reset_form.html': '/auth/password_reset/',
            'users/signup.html': '/auth/signup/'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                error_message = f'Ошибка вызываемого шаблона: {url}'
                self.assertTemplateUsed(response, template, error_message)

    def test_password_reset_from_key(self):
        from django.core import mail
        from django.urls import reverse
        response = self.authorized_client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.template_name,
            ['users/password_change_form.html'])

        # Затем мы отправляем ответ с нашим "адресом электронной почты"
        response = self.guest_client.post(
            reverse('password_reset'),
            {'email': StaticURLTests.user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Сброс пароля на testserver')

        token = response.context[0]['token']
        uid = response.context[0]['uid']

        # Теперь мы можем использовать токен для получения формы смены пароля
        response = self.guest_client.get(
            reverse(
                'password_reset_confirm',
                kwargs={'token': token, 'uidb64': uid}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'users/password_reset_confirm.html',
            response.template_name)

        # Теперь мы отправляем сообщение
        # по тому же URL-адресу с нашим новым паролем:
        response = self.authorized_client.post(
            reverse(
                'password_reset_confirm',
                kwargs={'token': token, 'uidb64': uid}),
            {'new_password1': 'pass', 'new_password2': 'pass'},
            follow=True)
        self.assertEqual(response.status_code, 200)
