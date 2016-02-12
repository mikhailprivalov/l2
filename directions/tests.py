from django.test import TestCase
import users.models as users
import directions.models as dm

class DirectionsTests(TestCase):
    fixtures = ['dbBase.json', 'clients.json']

    def test_create_direction(self):
        self.assertTrue(self.client.login(username='kamshekinaea', password='qazxswedc121153'))

        response = self.client.get('/dashboard/directions')

        self.assertContains(response, 'Категория пациентов')