from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Article, Category
from django.shortcuts import get_object_or_404, redirect
from .forms import ArticleForm
from django.http import Http404
from django.core.paginator import Paginator
# from django.contrib.auth.decorators import login_required
# from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy


class ArticleListView(ListView):
    paginate_by = 100000

    def get_queryset(self):
        return Article.objects.filter().order_by('-mod_date')


class ArticleDetailView(DetailView):
    model = Article

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        obj.viewed()
        return obj


class ArticleDraftListView(ListView):
    template_name = "blog/article_draft_list.html"
    paginate_by = 3

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user).filter(status='d').order_by('-pub_date')


class PublishedArticleListView(ListView):
    template_name = "blog/published_article_list.html"
    paginate_by = 100

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user).filter(status='p').order_by('-pub_date')


class ArticleUpdateView(UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "blog/article_update_form.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.author != self.request.user:
            raise Http404()
        return obj


class ArticleCreateView(CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_create_form.html'

    # Associate form.instance.user with self.request.user
    def form_valid(self, form):

        form.instance.author = self.request.user
        return super().form_valid(form)


class ArticleDeleteView(DeleteView):
    model = Article
    success_url = reverse_lazy('blog:article_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.author != self.request.user:
            raise Http404()
        return obj


def article_publish(request, pk, slug1):
    article = get_object_or_404(Article, pk=pk, author=request.user)
    article.published()
    return redirect(reverse("blog:article_detail", args=[str(pk), slug1]))


class CategoryDetailView(DetailView):
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object.has_child():
            articles = Article.objects.filter()
            categories = self.object.category_set.all()
            for category in categories:
                queryset = Article.objects.filter(category=category.id).order_by('-pub_date')
                articles.union(queryset)
        else:
            articles = Article.objects.filter(category=self.object.id).order_by('-pub_date')

        paginator = Paginator(articles, 100)
        page = self.request.GET.get('page')
        page_obj = paginator.get_page(page)
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['is_paginated'] = True
        return context
