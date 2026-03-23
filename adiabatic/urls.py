"""
URL configuration for adiabatic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from django.urls import re_path
from django.http import HttpResponseRedirect
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # Редирект з кореня на українську мову
    path('', RedirectView.as_view(url='/uk/', permanent=False)),
]

# URL з мовою
urlpatterns += i18n_patterns(
    path('leads/', include('leads.urls')),
    path('', include('pages.urls')),
    prefix_default_language=True,  # Показувати мову в URL для всіх мов
)

# Додаємо статичні файли та медіа
if settings.DEBUG:
    # Розробка
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Продакшен - обслуговування медіа файлів через Django
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
