from django.contrib.auth import get_user_model

from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

User = get_user_model()


class PostFormTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_create_post(self):
        '''Проверка создания нового пользователя'''
        user_count = User.objects.count()
        form_data = {
            'first_name': 'NameUser',
            'last_name': 'FamiliaUser',
            'username': 'usertests11',
            'email': "aaa@aa.ru",
            'password1': 'p1assword0',
            'password2': 'p1assword0'}
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name = 'Ошибка добавления пользователя!'
        self.assertEqual(User.objects.count(), user_count + 1, error_name)
