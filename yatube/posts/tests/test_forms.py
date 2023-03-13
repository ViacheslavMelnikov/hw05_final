from http import HTTPStatus
import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Comment
from django.conf import settings

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

text_post = 'Текст записанный в форму'
text_comment = 'Тестовый комментарий'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Группа А',
                                          slug='group_a',
                                          description='Описание А')

        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )

        '''Проверка создания поста'''
        posts_count = Post.objects.count()
        form_data = {'text': text_post,
                     'group': self.group.id,
                     'image': self.uploaded}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверка на редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user}))
        self.assertTrue(Post.objects.filter(
                        text=form_data['text'],
                        group=self.group.id,
                        image=f'posts/{self.uploaded}',
                        author=self.user
                        ).exists(), 'Ошибка создания поста')
        self.assertEqual(Post.objects.count(),
                         posts_count + 1,
                         'Записи в базе данных нет')

    def test_can_edit_post(self):
        '''Проверка редактирования'''
        self.post = Post.objects.create(text=text_post,
                                        author=self.user,
                                        group=self.group,
                                        image=self.uploaded)
        self.group2 = Group.objects.create(title='Группа Б',
                                           slug='group_b',
                                           description='Описание Б')
        form_data = {'text': text_post + '1',
                     'group': self.group2.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # в базе всего один пост
        self.assertEqual(Post.objects.count(),
                         1,
                         'В базе добавлен лишний пост!')
        # получим пост из базы
        post = Post.objects.first()
        # проверим поля поста напрямую
        self.assertEqual(post.text, text_post + '1')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group2)
        # проверим, что пост пропал со страницы старой группы
        self.assertEqual(
            Post.objects.filter(
                id=self.post.id,
                group=self.group.id).count(), 0,
            'Пост остался в прежней группе')

        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                group=self.group2.id,
                author=self.user,
                image=f'posts/{self.uploaded}',
                pub_date=self.post.pub_date).exists(),
            'Данные редактирования не совпадают')


class CommentFormTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Описание группы')
        self.post = Post.objects.create(
            text=text_post,
            author=self.user,
            group=self.group)

    def test_create_comment(self):
        '''Проверка создания комментария'''
        comment_count = Comment.objects.count()
        form_data = {'post_id': self.post.id,
                     'text': text_comment}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        error_name1 = 'Данные комментария не совпадают'
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Comment.objects.filter(
                        text=form_data['text'],
                        post=self.post.id,
                        author=self.user
                        ).exists(), error_name1)
        error_name2 = 'Комментарий не добавлен в базу данных'
        self.assertEqual(Comment.objects.count(),
                         comment_count + 1,
                         error_name2)

    def test_no_edit_comment(self):
        '''Проверка запрета комментирования не авторизованого пользователя'''
        # Создаем комментарий для поста зарегистрированным пользователем
        form_data = {'text': 'Создание комментария'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        # получаем количество комментариев на пост == 1
        posts_count = Comment.objects.count()
        # создаем новый комментарий
        form_data = {'text': 'Новый комментарий попытка'}
        # пытаемся добавить новый коммент без регистрации
        response = self.guest_client.post(reverse('posts:add_comment',
                                          kwargs={'post_id': self.post.id}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # сравниваем кол-во комментариев на пост == 1 != 2
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1,
                            'Комментарий добавлен в базу данных по ошибке')

    def test_comment_null(self):
        '''Запрет пустого комментария'''
        posts_count = Comment.objects.count()
        form_data = {'text': ''}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name2 = 'Комментарий добавлен в базу данных по ошибке'
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1,
                            error_name2)
