from django.test import TestCase, Client


class SurveySubmitTests(TestCase):
    def test_submit_minimal_fields_returns_success_json(self):
        # enforce_csrf_checks=False: уникнення GET сторінки з важким контекстом у тестовому рандері
        client = Client(HTTP_HOST='localhost', enforce_csrf_checks=False)
        res = client.post(
            '/uk/leads/survey/',
            data={
                'contact_person': 'Тест',
                'email': 'test@example.com',
                'phone': '+380501112233',
            },
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body['success'], msg=body.get('message'))
