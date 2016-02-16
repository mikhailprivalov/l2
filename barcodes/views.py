# coding=utf-8
from io import BytesIO
from django.http import HttpResponse
import simplejson as json
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39, code128, createBarcodeDrawing
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from django.contrib.auth.decorators import login_required
import directory.models as directory
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch, mm
import os.path
import re
from reportlab.pdfbase import pdfdoc
from django.conf import settings
import datetime
from django.utils import dateformat
pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
pdfmetrics.registerFont(
        TTFont('clacon', PROJECT_ROOT + '/../static/fonts/clacon.ttf'))

@login_required
def tubes(request):
    """
    Barcodes view
    :param request:
    :return:
    """
    pw, ph = 43, 25  # длина, ширина листа
    direction_id = json.loads(request.GET["napr_id"])
    response = HttpResponse(content_type='application/pdf')
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'inline; filename="barcodes.pdf"'

    buffer = BytesIO()
    pdfdoc.PDFInfo.title = 'Barcodes'
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
            #c.setFont('OpenSans', 8)
            c.setFont('clacon', 12)
            c.drawString(2*mm, ph*mm - 3*mm, "№ " + str(d))
            c.drawRightString(pw*mm - 2*mm, ph*mm - 3*mm, dt[tmp2.istochnik_f.istype])
            otd = tmp2.doc.podrazileniye.title.split(" ")
            st = ""
            if len(otd) > 1:
                st = otd[0][:3] + "/" + otd[1][:1]
            elif len(otd) == 1:
                st = otd[0][:3]
            st += u" => " + Issledovaniya.objects.filter(tubes__pk=tube).first().research.subgroup.podrazdeleniye.title[:4] + ". лаб."
            c.drawRightString(pw*mm - 2*mm, ph*mm - 6*mm, st.lower())

            #c.drawRightString(pw*mm - 2*mm, ph*mm - 9*mm, "л/в: " + tmp2.doc.get_fio())

            #c.setFont('OpenSans', 11)

            c.setFont('clacon', 18)
            fam = tmp2.client.family
            if len(fam) > 12:
                c.setFont('clacon', 18 - len(fam) * 0.7 + 12 * 0.7)

            c.drawRightString(pw*mm - 2*mm, ph*mm - 10*mm, fam + " " + tmp2.client.name[0] + tmp2.client.twoname[0])

            #c.setFont('OpenSans', 10)
            c.setFont('clacon', 12)
            types = ["фиолет", "красн", "стекло", "черн", "белая", "серая", "фильтро", "чашка", "голубая", "зеленая", "зелёная"]
            tb_t = tubes_buffer[tube_k]["title"].lower()
            pr = ""
            for s in types:
                if s in tb_t:
                    pr = s[0]
            pr = pr.upper()
            r = re.search(u"(\d\.\d|\d,\d|\d)\s(мл)", tb_t)
            if r:
                pr += " " + r.group(1) + " " + r.group(2)
            tdt = str(dateformat.format(datetime.date.today(), settings.DATE_FORMAT))
            tdt = tdt.split(".")[0] + "." + tdt.split(".")[1]
            c.drawString(2*mm, mm, pr)
            #tube = 30005
            # tube *= 100
            c.drawRightString(pw*mm - 2*mm, mm, str(tube))
            m = 0.027
            if tube >= 10000:
                m = 0.02
            if tube >= 100000:
                m = 0.02
            if tube >= 1000000:
                m = 0.017
            m *= 0.8
            #barcode = code39.Standard39(str(tube), barHeight=10*mm, barWidth=inch * m, checksum=0, ratio=2, gap=inch * m*1.5)
            barcode2 = createBarcodeDrawing("Codabar", value=str(tube),  barHeight=10*mm, barWidth=inch * m, checksum=0, ratio=2, gap=inch * m*1.5)

            #barcode2.drawOn(c, -4*mm, barcode2.height - 6*mm)
            barcode2.drawOn(c, 0, barcode2.height - 6*mm)
            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
