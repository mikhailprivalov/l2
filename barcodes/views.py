# coding=utf-8
from io import BytesIO
from django.http import HttpResponse
import simplejson as json
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import  code128
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from django.contrib.auth.decorators import login_required
import directory.models as directory
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, mm
import os.path
import re

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))

@login_required
def tubes(request):
    pw, ph = 43, 25
    direction_id = json.loads(request.GET["napr_id"])
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="barcodes.pdf"'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(pw*mm, ph*mm))
    dt = {"poli": "Поликлиника", "stat": "Стационар"}
    for d in direction_id:
        tmp2 = Napravleniya.objects.get(pk=int(d))
        tmp = Issledovaniya.objects.filter(napravleniye=tmp2).order_by("research__title")
        tubes_buffer = {}

        fresearches = set()
        fuppers = set()
        flowers = set()
        for iss in Issledovaniya.objects.filter(napravleniye=tmp2):
            for fr in iss.research.fractions_set.all():
                absor = directory.Absorption.objects.filter(fupper=fr)
                if absor.exists():
                    fuppers.add(fr.pk)
                    fresearches.add(fr.research.pk)
                    for absor_obj in absor:
                        flowers.add(absor_obj.flower.pk)
                        fresearches.add(absor_obj.flower.research.pk)

        for v in tmp:
            for val in directory.Fractions.objects.filter(research=v.research):
                vrpk = val.relation.pk
                rel = val.relation
                if val.research.pk in fresearches and val.pk in flowers:
                    absor = directory.Absorption.objects.filter(flower__pk=val.pk).first()
                    if absor.fupper.pk in fuppers:
                        vrpk = absor.fupper.relation.pk
                        rel = absor.fupper.relation

                if vrpk not in tubes_buffer.keys():
                    if not v.tubes.filter(type=rel).exists():
                        ntube = TubesRegistration(type=rel)
                        ntube.save()
                    else:
                        ntube = v.tubes.get(type=rel)
                    v.tubes.add(ntube)
                    tubes_buffer[vrpk] = {"pk": ntube.pk, "researches": set(), "title": ntube.type.tube.title}
                else:
                    ntube = TubesRegistration.objects.get(pk=tubes_buffer[vrpk]["pk"])
                    v.tubes.add(ntube)

                tubes_buffer[vrpk]["researches"].add(v.research.title)
        for tube_k in tubes_buffer.keys():
            tube = tubes_buffer[tube_k]["pk"]
            c.setFont('OpenSans', 8)
            c.drawString(2*mm, ph*mm - 3*mm, "№ " + str(d))
            c.drawRightString(pw*mm - 2*mm, ph*mm - 3*mm, dt[tmp2.istochnik_f.istype])
            otd = tmp2.doc.podrazileniye.title.split(" ")
            if len(otd) > 1:
                c.drawRightString(pw*mm - 2*mm, ph*mm - 6*mm, otd[0][:9] + ". " + otd[1][:3] + ".")
            elif len(otd) == 1:
                c.drawRightString(pw*mm - 2*mm, ph*mm - 6*mm, otd[0][:9])

            c.drawRightString(pw*mm - 2*mm, ph*mm - 9*mm, "л/в: " + tmp2.doc.get_fio())

            c.setFont('OpenSans', 11)
            c.drawRightString(pw*mm - 2*mm, ph*mm - 13*mm, tmp2.client.family + " " + tmp2.client.name[0] + " " + tmp2.client.twoname[0])

            c.setFont('OpenSans', 10)
            types = ["фиолет", "красн", "стекло", "черн", "белая", "серая", "фильтро", "чашка", "голубая", "зеленая"]
            tb_t = tubes_buffer[tube_k]["title"].lower()
            pr = ""
            for s in types:
                if s in tb_t:
                    pr = s[0]
            pr = pr.upper()
            r = re.search(u"(\d\.\d|\d,\d|\d)\s(мл)", tb_t)
            if r:
                pr += " " + r.group(1) + " " + r.group(2)

            c.drawString(2*mm, mm, pr)
            c.drawRightString(pw*mm - 2*mm, mm, str(tube))

            barcode = code128.Code128(str(tube), barHeight=5*mm, barWidth=inch * 0.026, stop=1, checksum=0)
            barcode.drawOn(c, -4*mm, barcode.barHeight - 0.3*mm)
            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
