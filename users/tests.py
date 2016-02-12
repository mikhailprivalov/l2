from django.test import TestCase
import users.models as users
from podrazdeleniya.models import Podrazdeleniya as podr
from django.contrib.auth.models import Group

class UsersTests(TestCase):
    fixtures = ['dbBase.json']

    def setUp(self):
        p = podr(title="TEST PODR")
        p.save()

        user = users.User.objects.create_user("test")
        user.set_password("pass")
        user.email = "test@test.ru"
        user.is_active = True
        user.save()

        for g in Group.objects.all():
            user.groups.add(g)
        user.save()

        profile = users.DoctorProfile.objects.create()
        profile.user = user
        profile.fio = "Привалов Михаил Сергеевич"
        pf = podr.objects.first()
        profile.podrazileniye = pf
        profile.isLDAP_user = False
        profile.save()


    def test_user_and_profile_create(self):
        self.assertEqual(users.User.objects.filter(username="test").exists(), True)
        self.assertEqual(users.DoctorProfile.objects.filter(user__username="test").exists(), True)

    def test_auth(self):
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=False)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(users.User.objects.filter(username="test").exists(), True)
        u = users.User.objects.get(username="test")
        self.assertTrue(self.client.login(username='test', password='pass'))

        csrf_client.post(path="/", data={"username": "test", "password": "pass"})

        response = self.client.get('/dashboard/')

        self.assertContains(response, 'Привалов Михаил Сергеевич')
        self.assertContains(response, 'TEST PODR')
