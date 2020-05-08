from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from unidecode import unidecode
from django.template.defaultfilters import slugify
import datetime


class Category(models.Model):
    """文章分类"""
    name = models.CharField(max_length=30, unique=True, verbose_name='分类名')
    slug = models.SlugField(max_length=40, verbose_name='slug')
    parent_category = models.ForeignKey('self', verbose_name='父级分类', blank=True, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('blog:category_detail', args=[self.slug])

    def has_child(self):
        if self.category_set.all().count() > 0:
            return True

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "分类"
        verbose_name_plural = verbose_name


class Tag(models.Model):
    """文章标签集合"""
    name = models.CharField(max_length=30, unique=True, verbose_name='标签名')
    slug = models.SlugField(max_length=40, verbose_name='slug')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag_detail', args=[self.slug])

    def get_article_count(self):
        return Article.objects.filter(tags__slug=self.slug).count()

    class Meta:
        ordering = ['name']
        verbose_name = "标签"
        verbose_name_plural = verbose_name


class Article(models.Model):
    """文章模型"""
    STATUS_CHOICES = (
        ('d', '草稿'),
        ('p', '发表'),
    )

    title = models.CharField(max_length=200, unique=True, verbose_name='标题')
    slug = models.SlugField(max_length=60, blank=True, verbose_name='slug')
    body = models.TextField(verbose_name='正文')
    pub_date = models.DateTimeField(verbose_name='发布时间', null=True)
    create_date = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    mod_date = models.DateTimeField(verbose_name='修改时间', auto_now=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='p')
    views = models.PositiveIntegerField(verbose_name='浏览量', default=0)
    author = models.ForeignKey(User, verbose_name='作者', on_delete=models.CASCADE, blank=False, null=False)

    category = models.ForeignKey(Category, verbose_name='分类', on_delete=models.CASCADE, default=1, blank=False, null=False)
    tags = models.ManyToManyField(Tag, verbose_name='标签集合', blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id or not self.slug:
            # Newly created object, so set slug
            self.slug = slugify(unidecode(self.title))

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog: article_detail', args=[str(self.pk), self.slug])

    def clean(self):
        # Don't allow draft entries to have a pub_date
        if self.status == 'd' and self.pub_date is not None:
            self.pub_date = None
            # Raise ValidationError('草稿没有发布日期，发布日期已清空。')
        if self.status == 'p' and self.pub_date is None:
            self.pub_date = datetime.datetime.now()

    def viewed(self):
        self.views += 1
        self.save(update_fields=['views'])

    def published(self):
        self.status = 'p'
        self.pub_date = datetime.datetime.now()
        self.save(update_fields=['status', 'pub_date'])

    class Meta:
        ordering = ['-pub_date']
        verbose_name = "文章"
        verbose_name_plural = verbose_name
