from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница Последние обновления на сайте
    path('', views.index, name='index'),
    # Все посты указанной группы
    path('group/<slug:slug>/', views.group_posts, name='group_list'),
    # Профайл пользователя
    path('profile/<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    # Создание новой записи
    path('create/', views.post_create, name='post_create'),
    # форма добавления комментариев
    path('posts/<int:post_id>/comment/',
         views.add_comment, name='add_comment'),
    # Редактирование записи
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('follow/', views.follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
