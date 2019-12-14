# coding=utf-8
import os.path
from io import BytesIO

import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.graphics.barcode import code128, eanbc
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfdoc
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import directory.models as directory
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, TubesRegistration
from laboratory.decorators import group_required
from laboratory.settings import FONTS_FOLDER
from users.models import DoctorProfile
from laboratory.utils import strdate
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

pdfmetrics.registerFont(
    TTFont('OpenSans', os.path.join(FONTS_FOLDER, 'OpenSans.ttf')))
pdfmetrics.registerFont(
    TTFont('clacon', os.path.join(FONTS_FOLDER, 'clacon.ttf')))


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

    pw, ph = barcode_size[0], barcode_size[1]  # длина, ширина листа

    doctitle = "Штрих-коды (%s)" % (("направления " + ", ".join(str(v) for v in direction_id)) if not istubes else (
            "ёмкости " + ", ".join(str(v) for v in tubes_id)))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Type'] = 'application/pdf'
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    response['Content-Disposition'] = str.translate('inline; filename="%s.pdf"' % doctitle,
                                                    {ord(a): ord(b) for a, b in zip(*symbols)})

    buffer = BytesIO()
    pdfdoc.PDFInfo.title = doctitle
    c = canvas.Canvas(buffer, pagesize=(pw * mm, ph * mm), bottomup=barcode_type == "std")
    c.setTitle(doctitle)
    if istubes:
        direction_id = set([x.napravleniye_id for x in Issledovaniya.objects.filter(tubes__id__in=tubes_id)])

    for d in direction_id:
        tmp2 = Napravleniya.objects.get(pk=int(d))
        tmp = Issledovaniya.objects.filter(napravleniye=tmp2).order_by("research__title")
        tubes_buffer = {}

        fresearches = set()
        fuppers = set()
        flowers = set()
        has_microbiology = False
        tubet = {}

        for iss in Issledovaniya.objects.filter(napravleniye=tmp2):
            if iss.research.is_microbiology:
                has_microbiology = True
                tpk = int(d) * 10 + 4600000000000
                tubes_id.add(tpk)
                tubet = {"pk": tpk, "researches": {iss.research.title},
                         "title": iss.research.microbiology_tube.title,
                         "microbiology": True,
                         "short_title": iss.research.microbiology_tube.get_short_title()}
            for fr in iss.research.fractions_set.all():
                absor = directory.Absorption.objects.filter(fupper=fr)
                if absor.exists():
                    fuppers.add(fr.pk)
                    fresearches.add(fr.research_id)
                    for absor_obj in absor:
                        flowers.add(absor_obj.flower_id)
                        fresearches.add(absor_obj.flower.research_id)

        if not has_microbiology:
            for v in tmp:
                for val in directory.Fractions.objects.filter(research=v.research):
                    vrpk = val.relation_id
                    rel = val.relation
                    if val.research_id in fresearches and val.pk in flowers:
                        absor = directory.Absorption.objects.filter(flower__pk=val.pk).first()
                        if absor.fupper_id in fuppers:
                            vrpk = absor.fupper.relation_id
                            rel = absor.fupper.relation

                    if vrpk not in tubes_buffer.keys():
                        if not v.tubes.filter(type=rel).exists():
                            ntube = TubesRegistration(type=rel)
                            ntube.save()
                            v.tubes.add(ntube)
                        else:
                            ntube = v.tubes.filter(type=rel).first()
                        tubes_buffer[vrpk] = {"pk": ntube.pk, "researches": set(),
                                              "title": ntube.type.tube.title,
                                              "short_title": ntube.type.tube.get_short_title()}
                        if not istubes:
                            tubes_id.add(ntube.pk)
                    else:
                        ntube = TubesRegistration.objects.get(pk=tubes_buffer[vrpk]["pk"])
                        v.tubes.add(ntube)

                    tubes_buffer[vrpk]["researches"].add(v.research.title)
        else:
            tubes_buffer[tubet["pk"]] = tubet
        for tube_k in sorted(tubes_buffer.keys(), key=lambda k: tubes_buffer[k]["pk"]):
            tube = tubes_buffer[tube_k]["pk"]
            if tube not in tubes_id:
                continue
            # c.setFont('OpenSans', 8)
            st = ""
            if not tmp2.imported_from_rmis:
                otd = list(tmp2.doc.podrazdeleniye.title.split(" "))
                if len(otd) > 1:
                    if "отделение" in otd[0].lower():
                        st = otd[1][:3] + "/о"
                    else:
                        st = otd[0][:3] + "/" + otd[1][:1]
                elif len(otd) == 1:
                    st = otd[0][:3]
            else:
                st = "вн.орг"

            if has_microbiology:
                st = st + "=>м.био"
            else:
                st = (st + "=>" + ",".join(set([x.research.get_podrazdeleniye().get_title()[:3] for x in Issledovaniya.objects.filter(tubes__pk=tube)]))).lower()

            fam = tmp2.client.individual.fio(short=True, dots=False)
            f = {}
            if has_microbiology:
                f["napravleniye"] = d
            else:
                f["tubes__pk"] = tube
            iss = Issledovaniya.objects.filter(**f)[0]
            pr = tubes_buffer[tube_k]["short_title"] + " " + (iss.comment[:9] if not iss.localization else iss.localization.barcode)

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
            if not has_microbiology:
                c.drawRightString(pw * mm - 2 * mm, mm, str(tube))
            m = 0.03
            if tube >= 100:
                m = 0.0212
            if tube >= 1000:
                m = 0.0242
            if tube >= 10000:
                m = 0.018
            if tube >= 100000:
                m = 0.0212
            if tube >= 1000000:
                m = 0.016
            if has_microbiology:
                m = 0.012
            barcode = code128.Code128(str(tube), barHeight=ph * mm - 12 * mm, barWidth=pw / 43 * inch * m)
            barcode.drawOn(c, -3 * mm, 4 * mm)

            c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


@login_required
@group_required("Создание и редактирование пользователей")
def login(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="login.pdf"'

    barcode_size = [int(x) for x in request.GET.get("barcode_size", "43x25").strip().split("x")]
    pw, ph = barcode_size[0], barcode_size[1]

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(pw * mm, ph * mm))

    pk = int(request.GET.get("pk", "-1"))
    u = DoctorProfile.objects.filter(user__pk=pk).first()
    if u and (not u.user.is_staff or request.user.is_staff):
        barcode = code128.Code128(u.get_login_id(), barHeight=ph * mm - 8 * mm, barWidth=0.265 * mm)
        barcode.drawOn(c, -4 * mm, 6.1 * mm)
        c.setFont('clacon', 15)
        c.drawCentredString(pw * mm / 2, 2 * mm, u.get_fio(dots=False))
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def gen_band_pdf(request):
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Symbola', os.path.join(FONTS_FOLDER, 'Symbola.ttf')))

    napr_id = json.loads(request.GET["napr_id"])
    direction = Napravleniya.objects.filter(pk=napr_id[0]).first()
    dir_create = strdate(direction.data_sozdaniya)
    iss = Issledovaniya.objects.values('research__title').filter(napravleniye=direction).first()
    individual_birthday = strdate(direction.client.individual.birthday)
    individual_fio = direction.client.individual.fio()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(152 * mm, 25 * mm))
    c.setFont('PTAstraSerifBold', 12)
    c.drawString(3.5 * mm, 18 * mm, '{}, {}'.format(individual_fio, individual_birthday))
    c.setFont('PTAstraSerifBold', 13)
    c.drawString(50 * mm, 12 * mm, '№: {}'.format(napr_id[0]))
    c.setFont('PTAstraSerifReg', 11)
    c.drawString(50 * mm, 8 * mm, '{}'.format(iss['research__title']))
    c.drawString(50 * mm, 4 * mm, 'поступил: {}'.format(dir_create))

    barcodeEAN = eanbc.Ean13BarcodeWidget(napr_id[0] + 460000000000, humanReadable=0, barHeight=11 * mm, barWidth=1.25)
    d = Drawing()
    d.add(barcodeEAN)
    renderPDF.draw(d, c, 0 * mm, 4 * mm)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="band.pdf"'
    response.write(pdf)

    return response
