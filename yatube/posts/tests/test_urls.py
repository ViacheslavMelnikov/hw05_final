from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адресов
        cls.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    # Проверяем общедоступные страницы
    def test_public_pages(self):
        """Доступ неавторизованного пользователя"""
        templates_url_names = (
            '/',
            f'/group/{self.post.group.slug}/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.id}/')
        for url in templates_url_names:
            response = self.guest_client.get(url)
            err_message = f'Ошибка доступа: {url}'
            self.assertEqual(response.status_code, HTTPStatus.OK, err_message)

    # Проверяем несуществующую страницу
    def test_non_existent_pages(self):
        """Проверяем несуществующую страницу"""
        non_existent_pages = '/unexisting_page/'
        response = self.guest_client.get(non_existent_pages)
        err_message = f'Ошибка несуществующей страницы: {non_existent_pages}'
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND,
            err_message)
        self.assertTemplateUsed(
            response,
            'core/404.html',
            'Ошибка проверки кастомного шаблона ошибки!')

    # Проверяем доступность страниц для авторизованного пользователя
    def test_page_for_an_authorized_user(self):
        """Страница доступна авторизованному пользователю + редактирование"""
        pages = (
            '/create/',
            f'/posts/{self.post.id}/edit/')
        for page in pages:
            response = self.authorized_client.get(page)
            error_message = f'Нет доступа к странице: {page}'
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                error_message)

    # Проверяем редиректы для неавторизованного пользователя
    def test_task_list_url_redirect_anonymous(self):
        """Проверяем редиректы для неавторизованного пользователя"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html'}
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                error_message = f'Ошибка вызываемого шаблона: {url}'
                self.assertTemplateUsed(response, template, error_message)
