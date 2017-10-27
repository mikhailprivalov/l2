# coding=utf-8
import datetime
import os.path
import re
from io import BytesIO

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import dateformat
from reportlab.graphics.barcode import code128
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfdoc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import directory.models as directory
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, TubesRegistration


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
pdfmetrics.registerFont(
    TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))
pdfmetrics.registerFont(
    TTFont('clacon', PROJECT_ROOT + '/../static/fonts/clacon.ttf'))


@login_required
def tubes(request, direction_implict_id=None):
    """
    Barcodes view
    :param request:
    :return:
    """
    if SettingManager.get("pdf_auto_print", "true", "b"):
        pdfdoc.PDFCatalog.OpenAction = '<</S/JavaScript/JS(this.print\({bUI:true,bSilent:false,bShrinkToFit:true}\);)>>'
    direction_id = []
    tubes_id = set()
    istubes = False
    if direction_implict_id is None:
        if "napr_id" in request.GET.keys():
            direction_id = json.loads(request.GET["napr_id"])
        elif "tubes_id" in request.GET.keys():
            tubes_id = set(json.loads(request.GET["tubes_id"]))
            istubes = True
    else:
        direction_id = [direction_implict_id]

    barcode_size = [int(x) for x in request.GET.get("barcode_size", "43x25").strip().split("x")]
    barcode_type = request.GET.get("barcode_type", "std").strip()
    padding = [int(x) for x in request.GET.get("padding", "0x0x0x0").strip().split("x")]

    pw, ph = barcode_size[0], barcode_size[1]  # длина, ширина листа

    doctitle = "Штрих-коды (%s)" % (("направления " + ", ".join(str(v) for v in direction_id)) if not istubes else (
        "пробирки " + ", ".join(str(v) for v in tubes_id)))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Type'] = 'application/pdf'
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    response['Content-Disposition'] = str.translate('inline; filename="%s.pdf"' % doctitle,
                                                    {ord(a): ord(b) for a, b in zip(*symbols)})

    buffer = BytesIO()
    pdfdoc.PDFInfo.title = 'Barcodes'
    c = canvas.Canvas(buffer, pagesize=(pw * mm, ph * mm), bottomup=barcode_type == "std")
    c.setTitle(doctitle)
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
        for tube_k in sorted(tubes_buffer.keys(), key=lambda k: tubes_buffer[k]["pk"]):
            tube = tubes_buffer[tube_k]["pk"]
            if tube not in tubes_id:
                continue
            # c.setFont('OpenSans', 8)
            otd = list(tmp2.doc.podrazdeleniye.title.split(" "))
            fam = tmp2.client.individual.fio(short=True, dots=False)
            st = ""
            if len(otd) > 1:
                if "отделение" in otd[0].lower():
                    st = otd[1][:3] + "/о"
                else:
                    st = otd[0][:3] + "/" + otd[1][:1]
            elif len(otd) == 1:
                st = otd[0][:3]
            st = (
            st + "=>" + Issledovaniya.objects.filter(tubes__pk=tube).first().research.subgroup.podrazdeleniye.title[
                        :3]).lower()
            types = ["фиолет", "красн", "стекло", "черн", "белая", "серая", "фильтро", "чашка", "голубая", "зеленая", "желтая", "жёлтая",
                     "зелёная", "контейнер", "зонд", "п ф", "л ф", "синяя"]
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

            nm = "№" + str(d) + "," + tmp2.client.base.short_title

            c.setFont('clacon', 12)
            c.drawString(2 * mm, ph * mm - 3 * mm, nm)
            c.drawRightString(pw * mm - 2 * mm, ph * mm - 3 * mm, st)
            c.setFont('clacon', 18)
            if len(fam) > 14:
                c.setFont('clacon', 18 - len(fam) * 0.7 + 12 * 0.7)
            c.drawRightString(pw * mm - 2 * mm, ph * mm - 7 * mm, fam)
            c.setFont('clacon', 12)
            c.drawString(2 * mm, mm, pr)
            c.drawRightString(pw * mm - 2 * mm, mm, str(tube))
            m = 0.0212
            if tube >= 10000:
                m = 0.018
            if tube >= 100000:
                m = 0.0212
            if tube >= 1000000:
                m = 0.016
            barcode = code128.Code128(str(tube), barHeight=ph * mm - 12 * mm, barWidth=pw / 43 * inch * m)
            barcode.drawOn(c, -3 * mm, 4 * mm)

            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
