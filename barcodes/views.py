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

pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:false}\);)>>'

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
    pw, ph = 44, 25  # длина, ширина листа
    direction_id = []
    tubes_id = set()
    istubes = False
    if "napr_id" in request.GET.keys():
        direction_id = json.loads(request.GET["napr_id"])
    elif "tubes_id" in request.GET.keys():
        tubes_id = set(json.loads(request.GET["tubes_id"]))
        istubes = True
    response = HttpResponse(content_type='application/pdf')
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'inline; filename="barcodes.pdf"'

    buffer = BytesIO()
    pdfdoc.PDFInfo.title = 'Barcodes'
    c = canvas.Canvas(buffer, pagesize=(pw * mm, ph * mm))
    dt = {"poli": "Поликлиника", "stat": "Стационар", "poli_stom": "Поликлиника-стом."}
    if istubes:
        direction_id = set([x.napravleniye.pk for x in Issledovaniya.objects.filter(tubes__id__in=tubes_id)])
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
                    if not istubes:
                        tubes_id.add(ntube.pk)
                else:
                    ntube = TubesRegistration.objects.get(pk=tubes_buffer[vrpk]["pk"])
                    v.tubes.add(ntube)

                tubes_buffer[vrpk]["researches"].add(v.research.title)
        for tube_k in tubes_buffer.keys():
            tube = tubes_buffer[tube_k]["pk"]
            if tube not in tubes_id:
                continue
            # c.setFont('OpenSans', 8)
            c.setFont('clacon', 12)
            c.drawString(2 * mm, ph * mm - 3 * mm, "№" + str(d) + "," + dt[tmp2.istochnik_f.istype][0])
            otd = tmp2.doc.podrazileniye.title.split(" ")
            st = ""
            if len(otd) > 1:
                st = otd[0][:3] + "/" + otd[1][:1]
            elif len(otd) == 1:
                st = otd[0][:3]
            st += u"=>" + Issledovaniya.objects.filter(tubes__pk=tube).first().research.subgroup.podrazdeleniye.title[
                          :3]
            c.drawRightString(pw * mm - 2 * mm, ph * mm - 3 * mm, st.lower())

            c.drawRightString(pw * mm - 2 * mm, ph * mm - 6 * mm, "л/в: " + tmp2.doc.get_fio(False))

            # c.setFont('OpenSans', 11)

            c.setFont('clacon', 18)
            fam = tmp2.client.family
            if len(fam) > 12:
                c.setFont('clacon', 18 - len(fam) * 0.7 + 12 * 0.7)
            if tmp2.client.twoname and tmp2.client.twoname != "":
                c.drawRightString(pw * mm - 2 * mm, ph * mm - 10 * mm,
                                  fam + " " + tmp2.client.name[0] + tmp2.client.twoname[0])
            else:
                c.drawRightString(pw * mm - 2 * mm, ph * mm - 10 * mm, fam + " " + tmp2.client.name[0])

            # c.setFont('OpenSans', 10)
            c.setFont('clacon', 12)
            types = ["фиолет", "красн", "стекло", "черн", "белая", "серая", "фильтро", "чашка", "голубая", "зеленая",
                     "зелёная", "контейнер", "зонд", "п ф", "л ф"]
            tb_t = tubes_buffer[tube_k]["title"].lower()
            pr = ""
            for s in types:
                if s in tb_t:
                    pr = s[0]
            pr = pr.upper()
            r = re.search(u"(\d+\.\d|\d+,\d+|\d+)\s(мл)", tb_t)
            if r:
                pr += r.group(1) + r.group(2)
            pr += " " + Issledovaniya.objects.filter(tubes__pk=tube).first().comment[:9]
            tdt = str(dateformat.format(datetime.date.today(), settings.DATE_FORMAT))
            tdt = tdt.split(".")[0] + "." + tdt.split(".")[1]
            c.drawString(2 * mm, mm, pr)
            #tube = 4523667
            c.drawRightString(pw * mm - 2 * mm, mm, str(tube))
            m = 0.0245
            if tube >= 10000:
                m = 0.018
            if tube >= 100000:
                m = 0.0212
            if tube >= 1000000:
                m = 0.016
            #m *= 0.9
            # barcode = code39.Standard39(str(tube), barHeight=10*mm, barWidth=inch * m, checksum=0, ratio=2, gap=inch * m*1.5)
            #barcode2 = createBarcodeDrawing("code128", value=str(tube), barHeight=10 * mm, barWidth=inch * m,
            #                                checksum=0, ratio=2, gap=inch * m * 1.8)

            # barcode2.drawOn(c, -4*mm, barcode2.height - 6*mm)
            #barcode2.drawOn(c, 0, barcode2.height - 6 * mm) '''barWidth=inch * m,'''
            barcode = code128.Code128(str(tube), barHeight=10*mm, barWidth=inch * m)
            barcode.drawOn(c, -2*mm, barcode.height - 6 * mm)
            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
