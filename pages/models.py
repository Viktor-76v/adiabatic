from django.db import models
from django.utils.translation import gettext_lazy as _, get_language
from django.urls import reverse
from django.utils.text import slugify


def _active_lang(language_code: str | None = None) -> str:
    """Return language code falling back to the currently active Django language."""
    if language_code:
        return language_code
    lang = get_language() or 'uk'
    return lang[:2]  # 'uk', 'ru', 'en' — strip potential region suffix


class Page(models.Model):
    """Основні сторінки сайту"""
    PAGE_TYPES = [
        ('home', _('Головна')),
        ('about', _('Про компанію')),
        ('contacts', _('Контакти')),
        ('products', _('Продукція')),
        ('custom', _('Кастомна сторінка')),
    ]
    
    page_type = models.CharField(_('Тип сторінки'), max_length=20, choices=PAGE_TYPES, unique=True)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True, blank=True)
    
    # Мультимовні поля
    title_uk = models.CharField(_('Заголовок (укр)'), max_length=200)
    title_ru = models.CharField(_('Заголовок (рус)'), max_length=200)
    title_en = models.CharField(_('Заголовок (англ)'), max_length=200)
    
    content_uk = models.TextField(_('Контент (укр)'), blank=True)
    content_ru = models.TextField(_('Контент (рус)'), blank=True)
    content_en = models.TextField(_('Контент (англ)'), blank=True)
    
    # SEO поля
    meta_title_uk = models.CharField(_('Meta title (укр)'), max_length=60, blank=True)
    meta_title_ru = models.CharField(_('Meta title (рус)'), max_length=60, blank=True)
    meta_title_en = models.CharField(_('Meta title (англ)'), max_length=60, blank=True)
    
    meta_description_uk = models.TextField(_('Meta description (укр)'), max_length=160, blank=True)
    meta_description_ru = models.TextField(_('Meta description (рус)'), max_length=160, blank=True)
    meta_description_en = models.TextField(_('Meta description (англ)'), max_length=160, blank=True)
    
    is_published = models.BooleanField(_('Опубліковано'), default=True)
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Оновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('Сторінка')
        verbose_name_plural = _('Сторінки')
        ordering = ['page_type']
    
    def __str__(self):
        return f"{self.get_page_type_display()}: {self.title_uk}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_uk)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Отримати абсолютний URL для сторінки"""
        if self.page_type == 'home':
            return reverse('pages:home')
        elif self.page_type == 'about':
            return reverse('pages:about')
        elif self.page_type == 'contacts':
            return reverse('pages:contacts')
        elif self.page_type == 'products':
            return reverse('pages:products')
        else:
            return reverse('pages:page_detail', kwargs={'slug': self.slug})
    
    def get_title(self, language_code=None):
        """Отримати заголовок для конкретної мови (або активної)."""
        lang = _active_lang(language_code)
        return getattr(self, f'title_{lang}', None) or self.title_uk

    def get_content(self, language_code=None):
        """Отримати контент для конкретної мови (або активної)."""
        lang = _active_lang(language_code)
        return getattr(self, f'content_{lang}', None) or self.content_uk

    def get_meta_title(self, language_code=None):
        """Отримати meta title для конкретної мови (або активної)."""
        lang = _active_lang(language_code)
        return getattr(self, f'meta_title_{lang}', None) or self.title_uk

    def get_meta_description(self, language_code=None):
        """Отримати meta description для конкретної мови (або активної)."""
        lang = _active_lang(language_code)
        return getattr(self, f'meta_description_{lang}', None) or self.content_uk[:160]

    def get_meta_keywords(self, language_code=None):
        """Stub — keywords fields not yet in DB; returns empty string."""
        return ''


class Section(models.Model):
    """Секції сторінок (JSON конструктор)"""
    SECTION_TYPES = [
        ('hero', _('Hero секція')),
        ('text', _('Текстова секція')),
        ('image', _('Зображення')),
        ('gallery', _('Галерея')),
        ('features', _('Особливості')),
        ('testimonials', _('Відгуки')),
        ('cta', _('Call to Action')),
        ('contact', _('Контактна форма')),
    ]
    
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='sections', verbose_name=_('Сторінка'))
    section_type = models.CharField(_('Тип секції'), max_length=20, choices=SECTION_TYPES)
    title = models.CharField(_('Заголовок секції'), max_length=200, blank=True)
    content = models.JSONField(_('Контент секції'), default=dict)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    is_published = models.BooleanField(_('Опубліковано'), default=True)
    
    class Meta:
        verbose_name = _('Секція')
        verbose_name_plural = _('Секції')
        ordering = ['page', 'order']
    
    def __str__(self):
        return f"{self.page.get_page_type_display()}: {self.get_section_type_display()} - {self.title}"


class Hero(models.Model):
    """Hero секції для головної сторінки"""
    title_uk = models.CharField(_('Заголовок (укр)'), max_length=200)
    title_ru = models.CharField(_('Заголовок (рус)'), max_length=200)
    title_en = models.CharField(_('Заголовок (англ)'), max_length=200)
    
    subtitle_uk = models.CharField(_('Підзаголовок (укр)'), max_length=300, blank=True)
    subtitle_ru = models.CharField(_('Підзаголовок (рус)'), max_length=300, blank=True)
    subtitle_en = models.CharField(_('Підзаголовок (англ)'), max_length=300, blank=True)
    
    description_uk = models.TextField(_('Опис (укр)'), blank=True)
    description_ru = models.TextField(_('Опис (рус)'), blank=True)
    description_en = models.TextField(_('Опис (англ)'), blank=True)
    
    background_image = models.ImageField(_('Фонове зображення'), upload_to='hero/')
    cta_text_uk = models.CharField(_('Текст кнопки (укр)'), max_length=50, default=_('Дізнатися більше'))
    cta_text_ru = models.CharField(_('Текст кнопки (рус)'), max_length=50, default=_('Дізнатися більше'))
    cta_text_en = models.CharField(_('Текст кнопки (англ)'), max_length=50, default=_('Дізнатися більше'))
    cta_url = models.CharField(_('URL кнопки'), max_length=200, blank=True)
    
    is_active = models.BooleanField(_('Активна'), default=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('Hero секція')
        verbose_name_plural = _('Hero секції')
        ordering = ['order']
    
    def __str__(self):
        return f"Hero: {self.title_uk}"
    
    def get_title(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'title_{lang}', None) or self.title_uk

    def get_subtitle(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'subtitle_{lang}', None) or self.subtitle_uk

    def get_description(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'description_{lang}', None) or self.description_uk

    def get_cta_text(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'cta_text_{lang}', None) or self.cta_text_uk


class Partner(models.Model):
    """Партнери компанії"""
    name = models.CharField(_('Назва'), max_length=200)
    logo = models.ImageField(_('Логотип'), upload_to='partners/')
    website_url = models.URLField(_('Веб-сайт'), blank=True)
    description = models.TextField(_('Опис'), blank=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    is_published = models.BooleanField(_('Опубліковано'), default=True)
    
    class Meta:
        verbose_name = _('Партнер')
        verbose_name_plural = _('Партнери')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Продукція компанії (каталог обладнання)"""
    
    # Основна інформація
    title_uk = models.CharField(_('Назва (укр)'), max_length=200)
    title_ru = models.CharField(_('Назва (рус)'), max_length=200, blank=True)
    title_en = models.CharField(_('Назва (англ)'), max_length=200, blank=True)
    
    slug = models.SlugField(_('Slug'), max_length=200, unique=True, blank=True)
    
    # Короткий опис (для картки)
    short_description_uk = models.TextField(_('Короткий опис (укр)'), max_length=300)
    short_description_ru = models.TextField(_('Короткий опис (рус)'), max_length=300, blank=True)
    short_description_en = models.TextField(_('Короткий опис (англ)'), max_length=300, blank=True)
    
    # Повний опис
    full_description_uk = models.TextField(_('Повний опис (укр)'))
    full_description_ru = models.TextField(_('Повний опис (рус)'), blank=True)
    full_description_en = models.TextField(_('Повний опис (англ)'), blank=True)
    
    # Зображення (до 3 фото на товар) - шляхи до static файлів
    image1 = models.CharField(_('Зображення 1'), max_length=200, blank=True, default='', help_text='Шлях до файлу в static, наприклад: images/tovar1.png')
    image2 = models.CharField(_('Зображення 2'), max_length=200, blank=True, default='', help_text='Шлях до файлу в static, наприклад: images/tovar11.png')
    image3 = models.CharField(_('Зображення 3'), max_length=200, blank=True, default='', help_text='Шлях до файлу в static, наприклад: images/tovar111.png')
    
    # Технічні характеристики (JSON)
    specifications = models.JSONField(_('Технічні характеристики'), default=dict, blank=True)
    
    # Переваги
    advantages_uk = models.TextField(_('Переваги (укр)'), blank=True)
    advantages_ru = models.TextField(_('Переваги (рус)'), blank=True)
    advantages_en = models.TextField(_('Переваги (англ)'), blank=True)
    
    # Галузі застосування
    applications_uk = models.TextField(_('Галузі застосування (укр)'), blank=True)
    applications_ru = models.TextField(_('Галузі застосування (рус)'), blank=True)
    applications_en = models.TextField(_('Галузі застосування (англ)'), blank=True)
    
    # Emoji іконка (fallback якщо немає фото)
    icon_emoji = models.CharField(_('Іконка (emoji)'), max_length=10, default='🔧')
    
    # Порядок сортування
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    is_published = models.BooleanField(_('Опубліковано'), default=True)
    
    # SEO поля
    meta_title_uk = models.CharField(_('Meta title (укр)'), max_length=60, blank=True)
    meta_title_ru = models.CharField(_('Meta title (рус)'), max_length=60, blank=True)
    meta_title_en = models.CharField(_('Meta title (англ)'), max_length=60, blank=True)
    
    meta_description_uk = models.TextField(_('Meta description (укр)'), max_length=160, blank=True)
    meta_description_ru = models.TextField(_('Meta description (рус)'), max_length=160, blank=True)
    meta_description_en = models.TextField(_('Meta description (англ)'), max_length=160, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('Створено'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Оновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товари')
        ordering = ['order', 'title_uk']
    
    def __str__(self):
        return self.title_uk
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title_uk)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('pages:catalog') + f'#{self.slug}'
    
    def get_title(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'title_{lang}', None) or self.title_uk

    def get_short_description(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'short_description_{lang}', None) or self.short_description_uk

    def get_full_description(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'full_description_{lang}', None) or self.full_description_uk

    def get_advantages(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'advantages_{lang}', None) or self.advantages_uk

    def get_applications(self, language_code=None):
        lang = _active_lang(language_code)
        return getattr(self, f'applications_{lang}', None) or self.applications_uk
