from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings
from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание группы')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост плюс дополнительный текст',
            group=cls.group)

    def test_models_have_correct_object_names(self):
        '''Проверка длины __str__ post'''
        error_name = f"Вывод не имеет {settings.LEN_OF_POSTS} символов"
        self.assertEqual(self.post.__str__(),
                         self.post.text[:settings.LEN_OF_POSTS],
                         error_name)

    def test_title_label(self):
        '''Проверка заполнения verbose_name'''
        field_verboses = {'text': 'Текст поста',
                          'pub_date': 'Дата публикации',
                          'group': 'Группа',
                          'author': 'Автор поста'}
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                error_name = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value, error_name)

    def test_title_help_text(self):
        '''Проверка заполнения help_text'''
        field_help_texts = {
            'text': 'Поле для Вашего текста в нашей социальной сети!',
            'group': 'Укажите группу (необязательно)'}
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                error_name = f'Поле {field} ожидало значение {expected_value}'
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value, error_name)


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа',
            slug='Адрес',
            description='описание',
        )

    def test_models_have_correct_title_names(self):
        '''Проверка заполнения str group'''
        group = GroupModelTest.group
        title = group.__str__()
        self.assertEqual(title, group.title)

    def test_title_label(self):
        '''Проверка заполнения verbose_name'''
        group = GroupModelTest.group
        field_verboses = {'title': 'Название группы',
                          'slug': 'Название группы на латинице',
                          'description': 'Краткое описание группы'}
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_title_help_text(self):
        '''Проверка заполнения help_text'''
        group = GroupModelTest.group
        field_help_texts = {
            'title': 'Укажите название новой группы!',
            'slug': ('Значение должно состоять только из букв,'
                     'цифр, знаков подчеркивания или дефиса!'),
            'description': 'Укажите описание и направление группы!'}
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)
