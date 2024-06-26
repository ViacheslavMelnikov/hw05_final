import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings
from ..models import Group, Post, Comment, Follow
from django.core.cache import cache
from ..forms import PostForm

User = get_user_model()
# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')

    def test_correct_page_context_guest_client(self):
        # Проверка количества постов на первой и второй страницах
        # Посты для теста пагинации создаем в самом тесте == 13
        bilk_post: list = []
        for i in range(settings.TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(bilk_post)

        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={'username': f'{self.user.username}'}),
                        reverse('posts:group_list',
                                kwargs={'slug': f'{self.group.slug}'}))

        # Прикольно получилось! Спасибо!
        # Честно говоря на учебе идешь по накатанной дорожке
        # а кривая дорожка гораздо прямее накатанной!!!
        # Спасибо!
        paginations = (
            (1, settings.POSTS_PER_PAGE),
            (2, settings.TEST_OF_POST - settings.POSTS_PER_PAGE)
        )

        for page in pages:
            for page_no, expected_count in paginations:
                response = self.guest_client.get(page, {"page": page_no})
                count_posts = len(response.context['page_obj'])
                error_name = (
                    f'Ошибка количества постов: {count_posts},'
                    f' должно {expected_count}')
                self.assertEqual(
                    count_posts,
                    expected_count,
                    error_name)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):

    def setUp(self):

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

        self.guest_client = Client()
        self.user = User.objects.create_user(username='author')
        self.user2 = User.objects.create_user(username='alien')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст и дополнительно',
                                        group=self.group,
                                        author=self.user,
                                        image=self.uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    # Проверяем используемые шаблоны+++++++++++++++++++++
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.post.group.slug}'}): (
                    'posts/group_list.html'),
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.post.author}'}): (
                    'posts/profile.html'),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}): (
                    'posts/post_detail.html'),
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}): (
                    'posts/post_create.html'),
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                error_name = f'Ошибка: {reverse_name} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    # вспомогательный метод для тестирования общих частей контекстов
    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('post', context)
            post = context['post'][0]
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(post.group, self.post.group)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.check_context_contains_page_or_post(response.context, True)
        # Уважаемый ревьювер, Денис! У меня в post_detail 'author' не
        # передается напрямую, он находится в 'post'
        # разве это не аналогичные строки?
        # self.assertEqual(response.context['post'].author, self.user)
        # self.assertEqual(response.context['author'], TestPosts.user)
        # это из check_context_contains_page_or_post
        # а, вот как self.assertIn('author', response.context) сделать
        # эту проверку если 'post' неитеррабельный? я наверное туплю...
        # пробовал self.assertIn('author', response.context['post'])

    def test_post_create_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        # Тест страницы создания и редактирования
        templates_page_names = (
            (reverse('posts:post_create'), type(None)),
            (reverse('posts:post_edit',
                     kwargs={'post_id': self.post.id}), Post))
        for path, clazz in templates_page_names:
            response = self.authorized_client.get(path)
            # наличие переменной post в контексте
            self.assertIn("post", response.context)
            # тип и значение переменной post
            self.assertIsInstance(response.context["post"], clazz)
            # проверяем наличие формы и ее тип
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context["form"], PostForm)
            # Может быть я ошибся :-(

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно++++++++++"""
        post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group,
            image=self.uploaded)
        response_index = self.authorized_client.get(
            reverse('posts:index'))
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'поста нет на главной')
        self.assertIn(post, group, 'поста нет в группе')
        self.assertIn(post, profile, 'поста нет в профайле')

    def test_profile_page_context_is_correct(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        self.check_context_contains_page_or_post(response.context, True)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)

    def test_group_page_context_is_correct(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
        self.check_context_contains_page_or_post(response.context, True)

    def test_other_group_does_not_have_the_post(self):
        """пост не попал в группу, для которой не был предназначен"""
        group2 = Group.objects.create(
            title='Дополнительная группа',
            slug='dop_group')
        posts_count = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text='Тестовый пост чужого',
            author=self.user2,
            group=group2)
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        group = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(group, posts_count, 'поста нет в другой группе')
        self.assertNotIn(post, profile,
                         'поста нет в группе другого пользователя')

    def test_post_with_image_appears_in_pages(self):
        templates_page_names = {
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}): False,
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}): False,
            reverse('posts:index'): False,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): True}
        for path in templates_page_names:
            response = self.guest_client.get(path)
            self.check_context_contains_page_or_post(response.context, True)

    def test_cache_context(self):
        '''Проверка кэширования страницы index'''
        # Создаем пост
        post2 = Post.objects.create(
            author=self.user,
            text='Текст поста для кэша',
            group=self.group)
        # делаем запрос 1
        response_1 = self.authorized_client.get(
            reverse('posts:index'))
        # получаем контекст_1
        context_1 = response_1.content
        # удаляем существующий пост
        post2.delete()
        # Post.objects.get(pk=self.post.id).delete()
        # делаем запрос 2
        response_2 = self.authorized_client.get(
            reverse('posts:index'))
        # получаем контекст_2
        context_2 = response_2.content
        # сравниваем контекст_1 == контекст_2
        self.assertEqual(context_1, context_2)
        # Очистка
        cache.clear()
        # Третий шаг
        response_3 = self.authorized_client.get(reverse('posts:index'))
        context_3 = response_3.content
        # Проверка очистки кэша
        self.assertNotEqual(context_3, context_2)


class CommentTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст и дополнительно',
                                        group=self.group,
                                        author=self.user)

    # Уважаемый ревьювер! Денис, Спасибо! :-)
    def test_post_detail_page_show_correct_context(self):
        """Правильный контекст комментария"""
        self.comment = Comment.objects.create(
            post_id=self.post.id,
            author=self.user,
            text='Комментарий пользователя')
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comments = {
            response.context['comments'][0].text: 'Комментарий пользователя',
            response.context['comments'][0].author: self.user.username}
        for value, expected in comments.items():
            self.assertEqual(comments[value], expected)
        self.assertTrue(response.context['form'], 'Форма получена')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='slavatest',
            email='melnikov.plusm@yandex.ru',
            password='testpassword')
        cls.user2 = User.objects.create_user(username='user2')
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_user_follower_authors(self):
        '''Посты доступны подписчикам'''
        count_follow = Follow.objects.filter(user=FollowViewsTest.user).count()
        data_follow = {
            'user': FollowViewsTest.user,
            'author': FollowViewsTest.author}

        url_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTest.author.username})
        # подписываемся на автора
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}),
            data=data_follow, follow=True)

        # новое количество +1
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()

        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_user_unfollower_authors(self):
        '''Посты не доступны пользователю, который не подписался'''
        # количество подписок
        count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = ('/auth/login/?next=/profile/'
                        f'{self.author.username}/unfollow/')
        # отпишимся
        response = self.guest_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow, new_count_follow)

    def test_follower_see_new_post(self):
        '''У подписчика добавляется новый пост от автора.
        У не подписчика поста нет'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_posts)

    def test_unfollower_no_see_new_post(self):
        '''Не подписался - нет поста'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)
