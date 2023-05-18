from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from blog.models import Category, Comment, Post, User
from blogicum.settings import ITEMS_PER_PAGE
from .forms import CommentForm, PostForm, UserForm


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now())
        queryset = queryset.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        return queryset


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def from_valid(self, form):
        super(PostUpdateView, self).form_valid(form)
        return redirect('blog:edit_post', form.instance)

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)


class PostDeliteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['slug'],
            is_published=True
        )
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category=self.category,
            category__is_published=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = ITEMS_PER_PAGE
    author = None

    def get_queryset(self):
        username = self.kwargs['username']
        self.author = get_object_or_404(User, username=username)

        queryset = Post.objects.filter(author=self.author)

        if self.author == self.request.user:
            return queryset

        queryset = queryset.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now(),
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        context['user'] = self.request.user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.comment
        return super().form_valid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('blog:post_detail', kwargs={'pk': pk})


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'id'
    post_data = None

    def dispatch(self, request, *args, **kwargs):
        comment_pk = self.kwargs.get(self.pk_url_kwarg)
        author = get_object_or_404(self.model, pk=comment_pk).author
        if author != self.request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        self.post_data = get_object_or_404(Post, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        pk = self.post_data.pk
        return reverse("blog:post_detail", kwargs={"pk": pk})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        comment_pk = self.kwargs.get(self.pk_url_kwarg)
        author = get_object_or_404(self.model, pk=comment_pk).author
        if author != self.request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        self.post_data = get_object_or_404(Post, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.object.post.pk})
