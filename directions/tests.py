from django.test import TestCase
import users.models as users
import directions.models as dm
import clients.models as clients
import uuid
import simplejson as json
import podrazdeleniya.models as podrs

class DirectionsTests(TestCase):
    fixtures = ['dbBase.json', 'clients.json']
    naprs = []
    cl = None

    def test_A_create_direction(self):
        self.assertTrue(users.User.objects.filter(username="kamshekinaea").exists())
        u = users.User.objects.get(username="kamshekinaea")
        u.set_password("123456")
        u.save()

        self.assertTrue(self.client.login(username='kamshekinaea', password='123456'))

        response = self.client.get('/dashboard/directions')
        self.assertContains(response, 'Категория пациентов')
        self.assertTrue(clients.Importedclients.objects.filter(num="65222").exists())
        self.cl = clients.Importedclients.objects.get(num="65222")

        response = self.client.get('/clients/ajax/search', data={"query": "65222", "type": "poli"})
        self.assertContains(response, json.dumps(self.cl.family))

        response = self.client.get('/directory/researches/list', data={"lab_id": "32"})
        self.assertContains(response, json.dumps("Общий анализ крови"))

        liq = dm.Napravleniya.gen_napravleniya_by_issledovaniya(self.cl.pk, str(uuid.uuid4()),
                                                               "1", "",
                                                               users.DoctorProfile.objects.get(
                                                                   user__username="promenashevate").pk,
                                                               "poli", u.doctorprofile, [["63", "71", "65", "54", "56", "57", "66", "69",
                                                                         "70", "61", "64", "60", "58", "52", "154",
                                                                         "59", "55", "53", "67", "68"],
                                                                        ["123", "131", "143", "130", "145", "134",
                                                                         "133", "166", "165", "124", "172", "122",
                                                                         "142", "120", "115", "144", "129", "170",
                                                                         "169", "110", "111", "117", "126", "139",
                                                                         "118", "119", "136", "135", "132", "113",
                                                                         "114", "128", "127", "137", "121", "112",
                                                                         "140", "141", "138", "116", "125"],
                                                                        ["84", "97", "82", "104", "83", "159", "162",
                                                                         "74", "76", "75", "158", "86", "73", "94",
                                                                         "78", "92", "93", "89", "96", "98", "81", "80",
                                                                         "161", "160", "91", "88", "87", "156", "95",
                                                                         "90", "106", "79", "167", "157", "77",
                                                                         "85"]])
        self.assertTrue(liq["r"])
        self.assertTrue(len(liq["list_id"]) > 0)
        for n in json.loads(liq["list_id"]):
            self.naprs.append(int(n))

        response = self.client.get('/barcodes/tubes', data={"napr_id": json.dumps(self.naprs)})
        self.assertEqual(response.status_code, 200)

        for pk in self.naprs:
            response = self.client.get('/directions/get/one', data={"id": pk})
            self.assertEqual(response.status_code, 200)
            j = json.loads(response.content)
            self.assertTrue(self.cl.family in j["client"]["fio"])
            self.assertTrue(j["ok"])
            for tpk in j["tubes"].keys():
                tube = dm.TubesRegistration.objects.get(pk=tpk)
                tube.set_get(u.doctorprofile)
                self.assertTrue(tube.getstatus())

        self.client.logout()

        usernames = ["bio-test", "kdl-test", "imm-test"]
        for uname in usernames:
            self.assertTrue(users.User.objects.filter(username=uname).exists())
            u = users.User.objects.get(username=uname)
            u.set_password("1")
            u.save()

            self.assertTrue(self.client.login(username=uname, password='1'))

            response = self.client.get('/dashboard/receive')
            self.assertEqual(response.status_code, 200)

            response = self.client.get('/tubes/get', data={"subgroup": podrs.Subgroups.objects.filter(podrazdeleniye=u.doctorprofile.podrazileniye).first().pk, "from": 36})
            self.assertEqual(response.status_code, 200)

            tubes = json.loads(response.content)

            i = 0

            for tube_row in tubes:
                i += 1
                tube_obj = dm.TubesRegistration.objects.get(pk=tube_row["tube"]["id"])
                if i % 2 == 0:
                    response2 = self.client.post("/dashboard/receive", {"data": json.dumps([{"id": tube_obj.pk, "status": True, "notice": "" if i % 6 != 0 else str(uuid.uuid4())}])})
                    self.assertContains(response2, "true")
                    self.assertTrue(dm.TubesRegistration.objects.get(pk=tube_obj.pk).rstatus())
                else:
                    tube_obj.set_r(u.doctorprofile)
                    self.assertTrue(tube_obj.rstatus())

            response = self.client.get('/results/enter')
            self.assertEqual(response.status_code, 200)

            import datetime
            today = datetime.datetime.today()

            response = self.client.get("/results/loadready", data={"def": 0, "datestart": today.strftime('%d.%m.%Y'), "dateend": today.strftime('%d.%m.%Y')})
            self.assertEqual(response.status_code, 200)

            ready = json.loads(response.content)
            self.assertTrue(len(ready["directions"]) != 0 and len(ready["tubes"]) != 0)

            for tube_row in ready["tubes"]:
                response2 = self.client.get("/directions/get/issledovaniya", data={"id": tube_row["id"], "type": 0})
                self.assertEqual(response2.status_code, 200)
                dird = json.loads(response2.content)
                for iss_t in dird["issledovaniya"]:
                    response3 = self.client.get("/researches/get/one", data={"id": int(iss_t["pk"])})
                    self.assertEqual(response3.status_code, 200)

                    resd = json.loads(response3.content)
                    fractions_result = {}
                    for fr_row in resd["fractions"].keys():
                        fractions_result[resd["fractions"][fr_row]["pk"]] = str(uuid.uuid4())

                    response4 = self.client.post("/results/save", {"fractions": json.dumps(fractions_result), "issledovaniye": int(iss_t["pk"])})
                    self.assertContains(response4, "true")

                    response5 = self.client.post("/results/confirm/list", {"list": json.dumps([iss_t["pk"]])})
                    self.assertContains(response5, "true")

        response6 = self.client.get("/results/pdf", data={"pk": json.dumps(self.naprs)})
        self.assertEqual(response6.status_code, 200)
        self.assertTrue(self.client.login(username='kamshekinaea', password='123456'))
        for pk in self.naprs:
            response = self.client.get("/results/get/full", data={"pk": pk})
            self.assertEqual(response.status_code, 200)




