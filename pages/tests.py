from django.test import TestCase, Client
from django.urls import reverse
from django.utils import translation


class I18nHomeTest(TestCase):
    """Integration tests: language activation + home page content."""

    def setUp(self):
        self.client = Client()

    def test_home_uk_default(self):
        response = self.client.get('/uk/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Енергетичне', content)

    def test_home_en_has_english_text(self):
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Energy', content)
        self.assertIn('equipment', content)

    def test_home_ru_has_russian_text(self):
        response = self.client.get('/ru/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Энергетическое', content)

    def test_set_language_post_redirects(self):
        set_lang_url = reverse('set_language')
        response = self.client.post(
            set_lang_url,
            data={'language': 'en', 'next': '/uk/'},
            follow=False,
        )
        self.assertIn(response.status_code, [302, 301])

    def test_set_language_en_sets_cookie(self):
        from django.conf import settings
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        set_lang_url = reverse('set_language')
        response = self.client.post(
            set_lang_url,
            data={'language': 'en', 'next': '/uk/'},
            follow=False,
        )
        self.assertIn(response.status_code, [302, 204])
        self.assertIn(cookie_name, response.cookies)
        self.assertEqual(response.cookies[cookie_name].value, 'en')

    def test_set_language_ru_sets_cookie(self):
        from django.conf import settings
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        set_lang_url = reverse('set_language')
        response = self.client.post(
            set_lang_url,
            data={'language': 'ru', 'next': '/uk/'},
            follow=False,
        )
        self.assertIn(response.status_code, [302, 204])
        self.assertIn(cookie_name, response.cookies)
        self.assertEqual(response.cookies[cookie_name].value, 'ru')

    def test_language_code_in_html_lang_attr(self):
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('lang="en"', content)

    def test_language_code_ru_in_html_lang_attr(self):
        response = self.client.get('/ru/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('lang="ru"', content)

    def test_root_redirects_to_uk(self):
        response = self.client.get('/')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('/uk/', response['Location'])

    def test_nav_links_localized_en(self):
        response = self.client.get('/en/')
        content = response.content.decode('utf-8')
        self.assertIn('Catalog', content)
        self.assertIn('Industries', content)

    def test_nav_links_localized_ru(self):
        response = self.client.get('/ru/')
        content = response.content.decode('utf-8')
        self.assertIn('Каталог', content)
        self.assertIn('Сферы применения', content)
