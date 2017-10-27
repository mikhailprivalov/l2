from django.test import TestCase
import users.models as users
from podrazdeleniya.models import Podrazdeleniya as podr
from django.contrib.auth.models import Group

class UsersTests(TestCase):
    fixtures = ['dbBase.json']

    def test_auth(self):
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=False)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(users.User.objects.filter(username="kamshekinaea").exists())
        u = users.User.objects.get(username="kamshekinaea")
        u.set_password("123456")
        u.save()

        self.assertTrue(self.client.login(username='kamshekinaea', password='123456'))

        response = self.client.get('/mainmenu/')

        self.assertContains(response, 'Камшекина')
