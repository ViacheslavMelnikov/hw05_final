from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    # название группы
    title = models.CharField(
        verbose_name='Название группы',
        help_text='Укажите название новой группы!',
        max_length=200
    )
    # уникальный адрес группы, часть URL
    # (например, для группы любителей котиков
    # slug будет равен cats: group/cats)
    slug = models.SlugField(
        verbose_name='Название группы на латинице',
        help_text=('Значение должно состоять только из букв,'
                   'цифр, знаков подчеркивания или дефиса!'),
        unique=True
    )
    # текст, описывающий сообщество.
    # Этот текст будет отображаться на странице сообщества
    description = models.TextField(
        verbose_name='Краткое описание группы',
        help_text='Укажите описание и направление группы!'
    )

    def __str__(self):
        # выводим название группы
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Поле для Вашего текста в нашей социальной сети!',
        null=False,
        blank=False
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста',
        help_text='Выберите автора'
    )
    # Ссылка на модель Group
    # Параметр on_delete=models.CASCADE
    # обеспечивает связность данных:
    # если из таблицы User будет удалён пользователь,
    # то будут удалены все связанные с ним посты.
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Укажите группу (необязательно)'
    )

    # Поле для картинки (необязательное)
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Загрузите картинку'
    )
    # Аргумент upload_to указывает директорию,
    # в которую будут загружаться пользовательские файлы.

    def __str__(self) -> str:
        # выводим текст поста
        return self.text[:settings.LEN_OF_POSTS]

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        # Многословное имя во множественном числе
        verbose_name_plural = 'Посты'


class Comment(CreatedModel):

    post = models.ForeignKey('Post',
                             on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Текст поста',
                             blank=True,
                             null=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор')
    text = models.TextField('Текст', help_text='Текст нового комментария')

    class Meta:
        ordering = ('-pub_date',)
        # Многословное имя во множественном числе
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(User, related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='following',
                               on_delete=models.CASCADE)

    class Meta:
        ordering = ('-author',)
        verbose_name = 'Лента автора'
        # Многословное имя во множественном числе
        verbose_name_plural = 'Лента авторов'
        # Ограничения
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'], name='unique_members')]
