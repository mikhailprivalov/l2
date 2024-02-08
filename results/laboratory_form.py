from appconf.manager import SettingManager
from directions.models import Result
from refprocessor.common import RANGE_IN, RANGE_NOT_IN
from utils.flowable import InteractiveTextField
from reportlab.platypus import Spacer
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
import simplejson as json
from laboratory.utils import strdate, strtime
import operator
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os.path
from laboratory.settings import FONTS_FOLDER
from reportlab.lib.styles import getSampleStyleSheet
from copy import deepcopy
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT


def default_lab_form(fwb, interactive_text_field, pw, direction, styleSheet, directory, show_norm, stl, print_vtype, get_r, result_normal):
    fwb.append(Spacer(1, 4 * mm))
    if interactive_text_field:
        fwb.append(InteractiveTextField())
    tw = pw
    no_units_and_ref = any([x.research.no_units_and_ref for x in direction.issledovaniya_set.all()])
    data = []
    tmp = [
        Paragraph('<font face="FreeSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
        Paragraph('<font face="FreeSansBold" size="8">Результат</font>', styleSheet["BodyText"]),
    ]
    if not no_units_and_ref:
        if direction.client.individual.sex.lower() == "м":
            tmp.append(Paragraph('<font face="FreeSansBold" size="8">Референсные значения (М)</font>', styleSheet["BodyText"]))
        else:
            tmp.append(Paragraph('<font face="FreeSansBold" size="8">Референсные значения (Ж)</font>', styleSheet["BodyText"]))
        tmp.append(Paragraph('<font face="FreeSansBold" size="8">Единицы<br/>измерения</font>', styleSheet["BodyText"]))

    tmp.append(Paragraph('<font face="FreeSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]))
    tmp.append(Paragraph('<font face="FreeSansBold" size="8">Дата</font>', styleSheet["BodyText"]))
    data.append(tmp)
    if no_units_and_ref:
        cw = [int(tw * 0.26), int(tw * 0.482), int(tw * 0.178)]
    else:
        cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
    cw = cw + [tw - sum(cw)]
    t = Table(data, repeatRows=1, colWidths=cw)
    style_t = TableStyle(
        [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
        ]
    )
    style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
    style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)

    t.setStyle(style_t)
    t.spaceBefore = 3 * mm
    t.spaceAfter = 0

    prev_conf = ""
    prev_date_conf = ""

    has0 = directory.Fractions.objects.filter(research__pk__in=[x.research_id for x in direction.issledovaniya_set.all()], hide=False, render_type=0).exists()

    if has0:
        fwb.append(t)

    iss_list = direction.issledovaniya_set.all()
    result_style = styleSheet["BodyText"] if no_units_and_ref else stl
    pks = []
    for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__number", "research__sort_weight"):
        if iss.pk in pks:
            continue
        pks.append(iss.pk)
        data = []
        fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=0).order_by("pk").order_by("sort_weight")

        if fractions.count() > 0:
            if fractions.count() == 1:
                tmp = [Paragraph('<font face="FreeSans" size="8">' + iss.research.title + "</font>", styleSheet["BodyText"])]
                norm = "none"
                sign = RANGE_IN
                if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                    r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                    ref = r.get_ref()
                    if show_norm:
                        norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                        ref = ref_res or ref
                    result = result_normal(r.value)
                    f_units = r.get_units()
                else:
                    continue
                if not iss.time_confirmation and iss.deferred:
                    result = "отложен"
                f = fractions[0]
                st = TableStyle(
                    [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                    ]
                )

                if f.render_type == 0:
                    if norm in ["none", "normal"]:
                        tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                    elif norm == "maybe":
                        tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                    else:
                        tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", result_style))
                    if not no_units_and_ref:
                        tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", stl))
                        tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", stl))

                    if iss.doc_confirmation_fio:
                        if prev_conf != iss.doc_confirmation_fio:
                            prev_conf = iss.doc_confirmation_fio
                            prev_date_conf = ""
                            tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_conf, styleSheet["BodyText"]))
                        else:
                            tmp.append("")
                        if prev_date_conf != strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]:
                            prev_date_conf = strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]
                            tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_date_conf, styleSheet["BodyText"]))
                        else:
                            tmp.append("")
                    else:
                        tmp.append("")
                        tmp.append("")

                    data.append(tmp)
                elif f.render_type == 1:
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")

                    if iss.doc_confirmation_fio:
                        tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % iss.doc_confirmation_fio, styleSheet["BodyText"]))
                        tmp.append(
                            Paragraph(
                                '<font face="FreeSansBold" size="7">%s</font>'
                                % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(iss.tubes.first().time_get)),
                                styleSheet["BodyText"],
                            )
                        )
                        tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % strdate(iss.time_confirmation), styleSheet["BodyText"]))
                    else:
                        tmp.append("")
                        tmp.append(Paragraph('<font face="FreeSansBold" size="7">%s</font>' % strdate(iss.tubes.first().time_get), styleSheet["BodyText"]))
                        tmp.append("")
                    data.append(tmp)

                    j = print_vtype(data, f, iss, 1, st, styleSheet)
                    data.append([Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])])
                    st.add('SPAN', (0, j), (-1, j))
                    st.add('BOX', (0, j), (-1, j), 1, colors.white)
                    st.add('BOX', (0, j - 1), (-1, j - 1), 1, colors.black)

                t = Table(data, colWidths=cw)
                t.setStyle(st)
                t.spaceBefore = 0
            else:
                tmp = [
                    Paragraph(
                        '<font face="FreeSansBold" size="8">'
                        + iss.research.title
                        + '</font>'
                        + ("" if iss.comment == "" or True else '<font face="FreeSans" size="8"><br/>Материал - ' + iss.comment + '</font>'),
                        styleSheet["BodyText"],
                    ),
                    '',
                ]
                if not no_units_and_ref:
                    tmp.append("")
                    tmp.append("")

                if iss.doc_confirmation_fio:
                    if prev_conf != iss.doc_confirmation_fio:
                        prev_conf = iss.doc_confirmation_fio
                        prev_date_conf = ""
                        tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_conf, styleSheet["BodyText"]))
                    else:
                        tmp.append("")
                    if prev_date_conf != strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]:
                        prev_date_conf = strdate(iss.time_confirmation, short_year=True) + '<br/>' + strtime(iss.time_confirmation)[0:5]
                        tmp.append(Paragraph('<font face="FreeSans" size="7">%s</font>' % prev_date_conf, styleSheet["BodyText"]))
                    else:
                        tmp.append("")
                else:
                    tmp.append("")
                    tmp.append("")

                data.append(tmp)
                ts = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.1, colors.white),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                ]

                style_t = TableStyle(ts)
                j = 0

                for f in fractions:
                    j += 1

                    tmp = []
                    if f.render_type == 0:
                        tmp.append(Paragraph('<font face="FreeSans" size="8">' + f.title + "</font>", styleSheet["BodyText"]))

                        norm = "none"
                        sign = RANGE_IN
                        if Result.objects.filter(issledovaniye=iss, fraction=f).exists() and not f.print_title:
                            r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                            ref = r.get_ref()
                            if show_norm:
                                norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                                ref = ref_res or ref
                            result = result_normal(r.value)
                            f_units = r.get_units()
                        elif f.print_title:
                            tmp[0] = Paragraph('<font face="FreeSansBold" size="10">{}</font>'.format(f.title), styleSheet["BodyText"])
                            data.append(tmp)
                            continue
                        else:
                            continue
                        if not iss.doc_confirmation and iss.deferred:
                            result = "отложен"
                        if norm in ["none", "normal"]:
                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                        elif norm == "maybe":
                            tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                        else:
                            tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", result_style))
                        if not no_units_and_ref:
                            tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", stl))
                            tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", stl))
                        tmp.append("")
                        tmp.append("")
                        data.append(tmp)
                    elif f.render_type == 1:
                        jp = j
                        j = print_vtype(data, f, iss, j, style_t, styleSheet)

                        if j - jp > 2:
                            data.append([Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])])
                            style_t.add('SPAN', (0, j), (-1, j))
                            style_t.add('BOX', (0, j), (-1, j), 1, colors.white)
                            j -= 1

                for k in range(0, 6):
                    style_t.add('INNERGRID', (k, 0), (k, j), 0.1, colors.black)
                    style_t.add('BOX', (k, 0), (k, j), 0.8, colors.black)
                    style_t.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                    style_t.add('TOPPADDING', (0, 0), (0, -1), 0)

                t = Table(data, colWidths=cw)
                t.setStyle(style_t)
            fwb.append(t)

        fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=1).order_by("pk").order_by("sort_weight")
        if fractions.count() > 0:
            data = []
            if not has0:
                tmp = [
                    Paragraph('<font face="FreeSansBold" size="8">Исследование</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="FreeSansBold" size="8">Дата сбора материала</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="FreeSansBold" size="8">Дата исполнения</font>', styleSheet["BodyText"]),
                    Paragraph('<font face="FreeSansBold" size="8">Исполнитель</font>', styleSheet["BodyText"]),
                ]
                data.append(tmp)

                tmp = [
                    Paragraph('<font face="FreeSansBold" size="8">%s</font>' % iss.research.title, styleSheet["BodyText"]),
                    Paragraph(
                        '<font face="FreeSans" size="8">%s%s</font>'
                        % ("" if not iss.tubes.exists() or not iss.tubes.first().time_get else strdate(iss.tubes.first().time_get), "" if not iss.comment else "<br/>" + iss.comment),
                        styleSheet["BodyText"],
                    ),
                    Paragraph('<font face="FreeSans" size="8">%s</font>' % ("Не подтверждено" if not iss.time_confirmation else strdate(iss.time_confirmation)), styleSheet["BodyText"]),
                    Paragraph('<font face="FreeSans" size="8">%s</font>' % (iss.doc_confirmation_fio or "Не подтверждено"), styleSheet["BodyText"]),
                ]
                data.append(tmp)

                cw = [int(tw * 0.34), int(tw * 0.24), int(tw * 0.2)]
                cw = cw + [tw - sum(cw)]
                t = Table(data, colWidths=cw)
                style_t = TableStyle(
                    [
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ]
                )

                style_t.add('LINEBELOW', (0, -1), (-1, -1), 2, colors.black)
                t.setStyle(style_t)
                t.spaceBefore = 3 * mm
                t.spaceAfter = 0
                fwb.append(t)

            has_anti = False
            for f in fractions:
                j = 0
                if Result.objects.filter(issledovaniye=iss, fraction=f).exists():
                    result = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0].value

                    if result == "":
                        continue
                    jo = json.loads(result)["rows"]
                    for key, val in jo.items():
                        if val["title"] != "":
                            data = []
                            style_t.add('SPAN', (0, j), (-1, j))
                            j += 1

                            norm_vals = []
                            for rowk, rowv in val["rows"].items():
                                if rowv["value"] not in ["", "null"]:
                                    norm_vals.insert(0, {"title": rowv["title"], "value": rowv["value"], "k": int(rowk)})
                            tmp = [
                                Paragraph(
                                    '<font face="FreeSansBold" size="8">' + (val["title"] if len(norm_vals) == 0 else "Выделенная культура: " + val["title"]) + "</font>",
                                    styleSheet["BodyText"],
                                ),
                                "",
                                "",
                                "",
                                "",
                                "",
                            ]
                            data.append(tmp)

                            if len(norm_vals) > 0:
                                has_anti = True

                                tmp = [Paragraph('<font face="FreeSansBold" size="8">%s</font>' % f.title, styleSheet["BodyText"]), "", "", "", "", ""]
                                data.append(tmp)
                                j += 1

                                li = 0
                                norm_vals.sort(key=operator.itemgetter('k'))
                                for idx, rowv in enumerate(norm_vals):
                                    li = idx
                                    if li % 3 == 0:
                                        tmp = []

                                    tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["title"] + "</font>", styleSheet["BodyText"]))
                                    tmp.append(Paragraph('<font face="FreeSans" size="8">' + rowv["value"] + "</font>", styleSheet["BodyText"]))
                                    if li % 3 == 2:
                                        data.append(tmp)
                                        j += 1

                                if li % 3 == 0:
                                    tmp.append("")
                                    tmp.append("")
                                    tmp.append("")
                                    tmp.append("")
                                if li % 3 == 1:
                                    tmp.append("")
                                    tmp.append("")
                                if li % 3 < 2:
                                    data.append(tmp)
                                    j += 1
                            cw = [int(tw * 0.28), int(tw * 0.06), int(tw * 0.27), int(tw * 0.06), int(tw * 0.27)]
                            cw = cw + [tw - sum(cw)]
                            t = Table(data, colWidths=cw)

                            style_t = TableStyle(
                                [
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                                    ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                                    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                                ]
                            )

                            style_t.add('BOTTOMPADDING', (0, 0), (-1, -1), 1)
                            style_t.add('TOPPADDING', (0, 0), (-1, -1), 2)

                            style_t.add('SPAN', (0, 0), (-1, 0))
                            style_t.add('SPAN', (0, 1), (-1, 1))

                            t.setStyle(style_t)
                            fwb.append(t)
            if has_anti:
                data = []
                tmp = [
                    [Paragraph('<font face="FreeSans" size="8">S - чувствителен; R - резистентен; I - промежуточная чувствительность;</font>', styleSheet["BodyText"])],
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
                data.append(tmp)
                cw = [int(tw * 0.23), int(tw * 0.11), int(tw * 0.22), int(tw * 0.11), int(tw * 0.22)]
                cw = cw + [tw - sum(cw)]
                t = Table(data, colWidths=cw)
                style_t = TableStyle(
                    [
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                        ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                    ]
                )
                style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
                style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
                style_t.add('SPAN', (0, 0), (-1, 0))

                t.setStyle(style_t)
                fwb.append(t)
        if iss.lab_comment and iss.lab_comment != "":
            data = []
            tmp = [
                [Paragraph('<font face="FreeSans" size="8">Комментарий</font>', styleSheet["BodyText"])],
                [Paragraph('<font face="FreeSans" size="8">%s</font>' % (iss.lab_comment.replace("\n", "<br/>")), styleSheet["BodyText"])],
                "",
                "",
                "",
                "",
            ]
            data.append(tmp)
            cw = [int(tw * 0.26), int(tw * 0.178), int(tw * 0.17), int(tw * 0.134), int(tw * 0.178)]
            cw = cw + [tw - sum(cw)]
            t = Table(data, colWidths=cw)
            style_t = TableStyle(
                [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('INNERGRID', (0, 0), (-1, -1), 0.8, colors.black),
                    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), -2),
                ]
            )
            style_t.add('BOTTOMPADDING', (0, 0), (-1, 0), 1)
            style_t.add('TOPPADDING', (0, 0), (-1, 0), 0)
            style_t.add('SPAN', (1, 0), (-1, 0))

            t.setStyle(style_t)
            fwb.append(t)
    return fwb


def lab_form_1(fwb, interactive_text_field, pw, direction, styleSheet, directory, show_norm, stl, print_vtype, get_r, result_normal):
    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSans', os.path.join(FONTS_FOLDER, 'FreeSans.ttf')))
    pdfmetrics.registerFont(TTFont('FreeSansBold', os.path.join(FONTS_FOLDER, 'FreeSansBold.ttf')))

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "FreeSans"
    style.fontSize = 9
    style.leading = 10
    style.spaceAfter = 1 * mm

    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER

    styleBold = deepcopy(style)
    styleBold.fontName = "FreeSansBold"

    styleLeft = deepcopy(style)
    styleLeft.alignment = TA_LEFT

    styleLeftFont7 = deepcopy(style)
    styleLeftFont7.fontSize = 7

    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_LEFT

    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    styleBackgroundcolor = deepcopy(style)
    styleBackgroundcolor.textColor = colors.white
    styleBackgroundcolor.alignment = TA_LEFT
    styleBackgroundcolor.spaceAfter = 2 * mm

    fwb.append(Spacer(1, 4 * mm))
    no_units_and_ref = False
    if interactive_text_field:
        fwb.append(InteractiveTextField())
    data = []
    tmp = [
        Paragraph('Исследование', styleBold),
        Paragraph('Результат', styleCenterBold),
    ]

    if direction.client.individual.sex.lower() == "м":
        tmp.append(Paragraph('Реф. значения (М)', styleCenterBold))
    else:
        tmp.append(Paragraph('Реф. значения (Ж)', styleCenterBold))
    tmp.append(Paragraph('Ед. изм.', styleCenterBold))

    data.append(tmp)

    cw = (80 * mm, 30 * mm, 45 * mm, 25 * mm)
    t = Table(data, repeatRows=1, colWidths=cw, hAlign='CENTRE')
    style_t = TableStyle(
        [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0.2 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1 * mm),
        ]
    )

    t.setStyle(style_t)
    t.spaceBefore = 3 * mm
    t.spaceAfter = 0

    has0 = directory.Fractions.objects.filter(research__pk__in=[x.research_id for x in direction.issledovaniya_set.all()], hide=False, render_type=0).exists()

    if has0:
        fwb.append(t)

    iss_list = direction.issledovaniya_set.all()
    result_style = deepcopy(stl)
    result_style.alignment = TA_LEFT

    pks = []
    laboratory_analyzer_data = []
    for iss in iss_list.order_by("research__direction_id", "research__pk", "tubes__number", "research__sort_weight"):
        if iss.pk in pks:
            continue
        pks.append(iss.pk)
        data = []
        fractions = directory.Fractions.objects.filter(research=iss.research, hide=False, render_type=0).order_by("pk").order_by("sort_weight")
        if iss.api_app:
            laboratory_analyzer_data.append(iss.api_app.name)

        if fractions.count() > 0:
            if fractions.count() == 1:
                tmp = [Paragraph('<font face="FreeSans" size="8">' + iss.research.title + "</font>", styleSheet["BodyText"])]
                norm = "none"
                sign = RANGE_IN
                if Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).exists():
                    r = Result.objects.filter(issledovaniye=iss, fraction=fractions[0]).order_by("-pk")[0]
                    ref = r.get_ref()
                    if show_norm:
                        norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                        ref = ref_res or ref
                    result = result_normal(r.value)
                    f_units = r.get_units()
                else:
                    continue
                if not iss.time_confirmation and iss.deferred:
                    result = "отложен"
                f = fractions[0]
                ts = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('LEFTPADDING', (0, 0), (0, -1), 3),
                ]

                style_t = TableStyle(ts)
                result_is_norm = []
                if f.render_type == 0:
                    if norm in ["none", "normal"]:
                        tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                        result_is_norm.append(True)
                    elif norm == "maybe":
                        tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                        result_is_norm.append(True)
                    else:
                        # tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", styleBackgroundcolor))
                        tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "*" + "</font>", styleBackgroundcolor))
                        result_is_norm.append(False)
                    if not no_units_and_ref:
                        tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", stl))
                        tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", stl))
                    data.append(tmp)

                for k in range(0, 4):
                    style_t.add('TOPPADDING', (0, 0), (0, -1), 0)
                    style_t.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                    style_t.add('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black)
                    style_t.add('LEFTPADDING', (1, 0), (1, -1), 4 * mm)
                    style_t.add('LEFTPADDING', (2, 0), (2, -1), 4 * mm)
                    style_t.add('LEFTPADDING', (3, 0), (3, -1), 4 * mm)

                step = 0
                for is_norm in result_is_norm:
                    if not is_norm:
                        style_t.add('BACKGROUND', (1, step), (1, step), HexColor(0xF45E1E))

                    step += 1

                t = Table(data, colWidths=cw)
                t.setStyle(style_t)
                t.spaceBefore = 0
            else:
                tmp = [
                    Paragraph(
                        '<font face="FreeSansBold" size="8">'
                        + iss.research.title
                        + '</font>'
                        + ("" if iss.comment == "" or True else '<font face="FreeSans" size="8"><br/>Материал - ' + iss.comment + '</font>'),
                        styleSheet["BodyText"],
                    ),
                    '',
                ]
                if not no_units_and_ref:
                    tmp.append("")
                    tmp.append("")

                data.append(tmp)
                ts = [
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('LEFTPADDING', (0, 0), (0, -1), 3),
                ]

                style_t = TableStyle(ts)
                j = 0

                result_is_norm = []
                for f in fractions:
                    j += 1

                    tmp = []
                    if f.render_type == 0:
                        tmp.append(Paragraph('<font face="FreeSans" size="8">' + f.title + "</font>", styleSheet["BodyText"]))

                        norm = "none"
                        sign = RANGE_IN
                        if Result.objects.filter(issledovaniye=iss, fraction=f).exists() and not f.print_title:
                            r = Result.objects.filter(issledovaniye=iss, fraction=f).order_by("-pk")[0]
                            ref = r.get_ref()
                            if show_norm:
                                norm, sign, ref_res = r.get_is_norm(recalc=True, with_ref=True)
                                ref = ref_res or ref
                            result = result_normal(r.value)
                            f_units = r.get_units()
                        elif f.print_title:
                            tmp[0] = Paragraph('<font face="FreeSansBold" size="10">{}</font>'.format(f.title), styleSheet["BodyText"])
                            data.append(tmp)
                            continue
                        else:
                            continue
                        if norm in ["none", "normal"]:
                            tmp.append(Paragraph('<font face="FreeSans" size="8">' + result + "</font>", result_style))
                            result_is_norm.append(True)
                        elif norm == "maybe":
                            tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "</font>", result_style))
                            result_is_norm.append(True)
                        else:
                            # tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + RANGE_NOT_IN.get(sign, "") + "</font>", styleBackgroundcolor))
                            tmp.append(Paragraph('<font face="FreeSansBold" size="8">' + result + "*" + "</font>", styleBackgroundcolor))
                            result_is_norm.append(False)
                        if not no_units_and_ref:
                            tmp.append(Paragraph('<font face="FreeSans" size="7">' + get_r(ref) + "</font>", result_style))
                            tmp.append(Paragraph('<font face="FreeSans" size="7">' + f_units + "</font>", result_style))
                        data.append(tmp)

                for k in range(0, 4):
                    style_t.add('TOPPADDING', (0, 0), (0, -1), 0)
                    style_t.add('BOTTOMPADDING', (0, 0), (0, -1), 0)
                    style_t.add('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black)
                    style_t.add('LEFTPADDING', (1, 0), (1, -1), 4 * mm)
                    style_t.add('LEFTPADDING', (2, 0), (2, -1), 4 * mm)
                    style_t.add('LEFTPADDING', (3, 0), (3, -1), 4 * mm)

                step = 0
                for is_norm in result_is_norm:
                    if not is_norm:
                        style_t.add('BACKGROUND', (1, step + 1), (1, step + 1), HexColor(0xF45E1E))

                    step += 1

                t = Table(data, colWidths=cw)
                t.setStyle(style_t)

            fwb.append(t)

    fwb.append(Spacer(1, 3 * mm))
    data = []

    laboratory_analyzer = ""
    if len(laboratory_analyzer_data) > 0:
        laboratory_analyzer = f"<br/>{' '.join(laboratory_analyzer_data)}"

    tmp = [
        Paragraph(f"Дата, время выполнения: {strdate(iss.time_confirmation, short_year=False)} {strtime(iss.time_confirmation)[0:5]}{laboratory_analyzer}", styleLeft),
        Paragraph(f"Исследования выполнены: {iss.doc_confirmation_fio} (Врач клинической лабораторной диагностики)", styleLeft),
    ]

    data.append(tmp)

    cw = (90 * mm, 90 * mm)
    t = Table(data, repeatRows=1, colWidths=cw, hAlign='CENTRE')
    style_t = TableStyle(
        [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), -0.2 * mm),
        ]
    )

    t.setStyle(style_t)
    t.spaceBefore = 3 * mm
    t.spaceAfter = 0
    fwb.append(t)

    data1 = []
    tmp = [
        Paragraph(
            "* Референсные значения приводятся с учетом возраста, пола, фазы менструального цикла, срока беременности. "
            "Результаты исследований не являются диагнозом, необходима консультация специалиста.",
            styleLeftFont7,
        ),
        Paragraph("", styleLeftFont7),
    ]

    data1.append(tmp)

    cw = (150 * mm, 20 * mm)
    t = Table(data1, repeatRows=1, colWidths=cw, hAlign='LEFT')
    style_t = TableStyle(
        [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2 * mm),
        ]
    )

    t.setStyle(style_t)
    t.spaceBefore = 3 * mm
    t.spaceAfter = 0

    fwb.append(t)

    return fwb


def self_watermarks_func(canvas_mark):
    canvas_mark.line(10 * mm, 10.7 * mm, 200 * mm, 10.7 * mm)
    canvas_mark.setFont('FreeSans', 7)
    canvas_mark.drawString(120 * mm, 8 * mm, 'Исследования выполнены в {} {} {}'.format(SettingManager.get("org_title"), SettingManager.get("org_www"), SettingManager.get("org_phones")))
    canvas_mark.drawString(15 * mm, 8 * mm, 'Дата печати: {}'.format("13.10.2023 12:15"))
    return canvas_mark
