from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginate


def index(request):
    posts = Post.objects.all()
    page_obj = paginate(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate(request, posts)
    context = {'group': group,
               'posts': posts,
               'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = posts.count()
    page_obj = paginate(request, posts)
    following = (request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author).exists())
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_count': post_count,
        'posts': posts,
        'following': following}

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    post_count = post.author.posts.count()
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    post = None
    if not request.method == 'POST' or not form.is_valid():
        return render(
            request,
            'posts/post_create.html',
            {'form': form, 'post': post})

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if not request.method == 'POST' or not form.is_valid():
        return render(
            request,
            'posts/post_create.html',
            {'form': form, 'post': post})

    post = form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    # информация о текущем пользователе доступна в переменной request.user
    posts = Post.objects.filter(author__following__user=request.user)
    page = paginate(request, posts)
    context = {"page_obj": page}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    user = request.user
    Follow.objects.filter(user=user, author__username=username).delete()
    return redirect("posts:profile", username=username)
