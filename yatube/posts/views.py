from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'misc/index.html', {'page': page, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, settings.NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/group.html', {
        'group': group, 'page': page,
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    number_of_posts = Post.objects.filter(author_id=user.id).count()
    paginator = Paginator(user.posts.all(), settings.NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and (Follow.objects.filter(
        user=request.user, author=user).exists()
                                                   )
    return render(request, 'misc/profile.html', {
        'number_of_posts': number_of_posts, 'page': page, 'author': user,
        'following': following,
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'), id=post_id,
                             author__username=username)
    form = CommentForm()
    comments = post.comments.all()
    return render(request, 'posts/post.html', {
        'number_of_posts': post.author.posts.count(), 'post': post,
        'author': post.author, 'form': form, 'comments': comments
    })


@login_required
def new_post(request):
    form = PostForm()
    if request.method == 'GET':
        return render(request, 'posts/new.html', {'form': form, })
    elif request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            post: Post = form.save(False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'posts/new.html', {'form': form})
    return render(request, 'posts/new.html', {'form': form, })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect('posts', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts', username=username, post_id=post_id)
    return render(request, 'posts/new.html', {'form': form, 'post': post})


def page_not_found(request, exception=None):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts', username, post_id)
    return render(request, 'misc/comments.html', {
        'form': form, 'comments': comments, 'post': post
    }
                  )


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user)
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page, })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(author=author, user=user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('profile', username=username)
