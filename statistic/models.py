from django.db import models
import users.models as users
import slog.models as slog
import directory.models as directory


class Uet(models.Model):
    user = models.ForeignKey(users.DoctorProfile, db_index=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    points = models.FloatField()

    @staticmethod
    def add(user: users.DoctorProfile, research: directory.Researches, direction: int):
        isdoc = True
        #isdoc = user.labtype == 1
        pts = sum([x.uet_doc if isdoc else x.uet_lab for x in directory.Fractions.objects.filter(research__pk=research.pk)])
        if pts > 0:
            row = Uet(user=user, points=pts)
            row.save()
        slog.Log(key=str(direction), type=26, body=str(pts), user=user).save()

    def __str__(self):
        return "%s %s +%s" % (str(self.user), self.date, self.points)